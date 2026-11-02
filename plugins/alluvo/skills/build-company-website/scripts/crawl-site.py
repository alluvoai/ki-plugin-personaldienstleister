#!/usr/bin/env python3
"""Inventory every URL of an existing company website before rebuilding it on alluvo (workflow build-company-website).

Usage:
    python3 crawl-site.py https://www.example-personal.de [--max-pages 500] [--out urls.json] [--render]

Strategy:
1. Sitemaps first: every `Sitemap:` entry of robots.txt, otherwise /sitemap.xml and /sitemap_index.xml
   (sitemap indexes and gzip-compressed sitemaps are followed; only the page `<loc>` of each `<url>` counts,
   never the `<image:loc>` of Yoast/Google image sitemaps).
2. Without a sitemap, or with fewer than 3 URLs in it (typical for one-pagers and JS sites), crawl same-host links
   from the start page: robots.txt is respected, requests are rate-limited (--delay), redirects are followed and the
   final URL + status recorded. Linked PDFs and images on the same host are inventoried too. Tracking parameters
   (utm_*, gclid, fbclid, ...) are dropped.
3. `--render` additionally opens the start page and the crawled HTML pages in headless Chrome (python `playwright`,
   else the `agent-browser` CLI) to read links that JavaScript builds (Readymag, Wix, Squarespace, SPAs). Without a
   renderer the script says how to install one and carries on with the static HTML.

External targets (other hosts) are listed separately under `external`: PDFs (also Google Drive/Docs and Dropbox
files), job boards and applicant-tracking widgets (the jobs move to the Talent Hub), booking tools, chat widgets and
review portals. Problems are collected under `warnings`
(robots.txt/sitemap.xml answering non-200 or HTML, tiny sitemaps, JS-only pages) and printed at the end.

Non-ASCII URLs (IRIs such as /über-uns, IDN hosts such as müller-personal.de) are requested as ASCII URIs (IDNA host,
UTF-8 percent-encoding, existing %XX escapes kept). The inventory reports one readable canonical form per page
(punycode host, "/über-uns"; "/%C3%BCber-uns" is the same page), which import-redirects accepts as `from`.

Writes the inventory as JSON (url, final_url, status, content_type, title, canonical, lastmod, then the SEO and
content fields: description, h1, h1_count, lang, hreflang [{lang, url}], jsonld_types, og_image, images [{src, width,
height, alt}, plus {src, background: true, via} for lazy CSS background images], word_count, forms) and a
sitemap.xml of the reachable HTML pages next to it (percent-encoded `<loc>`, as the sitemap protocol requires). Python 3.9+, standard library only (`--render` needs playwright
or agent-browser).
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, quote, urldefrag, urlencode, urljoin, urlsplit, urlunsplit
from xml.sax.saxutils import escape

USER_AGENT = "AlluvoWebsiteCrawler/1.0 (+https://alluvo.ai)"
TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"gclid", "fbclid", "msclkid", "dclid", "mc_cid", "mc_eid", "_ga", "_gl", "igshid", "yclid"}
ASSET_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg")
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "whatsapp:")
MAX_SITEMAPS = 50
MIN_SITEMAP_URLS = 3
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
HTML_TYPES = ("text/html", "application/xhtml+xml")
MAX_IMAGES_PER_PAGE = 100
# lazy <img> sources (WordPress lazy-load plugins, Avada) and lazy CSS background images (Avada data-bg, Elementor,
# WP Rocket data-bg/data-bg-url, generic data-background); data-src on a non-img element is a background too.
LAZY_IMG_ATTRIBUTES = ("data-src", "data-orig-src", "data-lazy-src")
LAZY_BG_ATTRIBUTES = ("data-bg", "data-bg-url", "data-background", "data-background-image", "data-src", "data-orig-src", "data-lazy-src")
NOT_BACKGROUND_TAGS = ("img", "source", "iframe", "video", "audio", "script", "embed", "track")
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
SKIP_TEXT_TAGS = ("script", "style", "noscript", "template", "svg")
CHROME_TAGS = ("nav", "header", "footer")
WORD = re.compile(r"\w+", re.UNICODE)

# External targets worth migrating or linking: kind -> host fragments (matched on the host, www. stripped).
EXTERNAL_HOSTS = {
    # Job widgets and applicant tracking: their jobs move to the Talent Hub, the website links it.
    "jobs": ("hr4you.", "softgarden.", "personio.", "zvoove.", "rexx-systems.", "rexx-recruitment.", "onlyfy.", "b-ite.", "join.com", "recruitee.", "smartrecruiters.", "jobbase.", "d.vinci.", "dvinci-", "concludis.", "umantis.", "stepstone.", "indeed.", "arbeitsagentur.", "jobware.", "kimeta."),
    "booking": ("calendly.", "cal.com", "outlook.office365.com/book", "bookings.", "terminland.", "etermin.", "doodle."),
    "chat": ("tawk.", "intercom.", "crisp.chat", "userlike.", "moin.ai", "chatbase.", "tidio.", "zendesk.", "whatsapp.com", "wa.me"),
    "review": ("kununu.", "provenexpert.", "trustpilot.", "trustedshops.", "ausgezeichnet.org", "proven-expert."),
}
JOB_PATH_WORDS = ("stellenangebote", "stellenanzeige", "karriere", "bewerbung", "/jobs", "/job/")
FILE_HOSTS = ("drive.google.com", "docs.google.com", "dropbox.com", "dl.dropboxusercontent.com", "onedrive.live.com", "1drv.ms", "wetransfer.com", "we.tl", "issuu.com", "yumpu.com", "flipsnack.com", "calameo.com")


# --- IRI → URI (kept identical in crawl-site.py and verify-redirects.py; tests/Python checks both) ---------------------
UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
STRAY_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
ESCAPE_RUN = re.compile(r"(?:%[0-9A-Fa-f]{2})+")
PATH_SAFE = "/;:@!$&'()*+,="
QUERY_SAFE = PATH_SAFE + "?"


def _quote_component(value: str, safe: str) -> str:
    """Percent-encodes everything outside `safe` as UTF-8; existing %XX escapes are kept (hex uppercased), a stray % becomes %25."""
    quoted = quote(STRAY_PERCENT.sub("%25", value), safe=safe + "%")
    return ESCAPE_RUN.sub(lambda match: match.group(0).upper(), quoted)


def _ascii_host(host: str) -> str:
    """IDNA (punycode) form of a host name, lowercase: müller-personal.de → xn--mller-personal-gsb.de."""
    host = host.lower()
    if host.isascii():
        return host
    labels = host.replace("。", ".").replace("．", ".").replace("｡", ".").split(".")
    try:
        return ".".join(label if label.isascii() else label.encode("idna").decode("ascii") for label in labels)
    except UnicodeError:
        return quote(host, safe=".-")


def _ascii_netloc(netloc: str) -> str:
    userinfo, at, hostport = netloc.rpartition("@")
    if hostport.startswith("["):  # IPv6 literal, ASCII already
        host, port = hostport, ""
    else:
        host, colon, port = hostport.partition(":")
        port = colon + port
    return (_quote_component(userinfo, "!$&'()*+,;=:") + at if at else "") + _ascii_host(host) + port


def to_uri(url: str) -> str:
    """Any IRI as a valid ASCII URI for the request line: IDNA host, UTF-8 percent-encoded path, query and fragment.

    Existing escapes are never encoded twice ("/das-men%C3%BC" stays, "/das-menü" becomes "/das-men%C3%BC").
    Raises ValueError for unparsable URLs (e.g. a broken IPv6 literal).
    """
    parts = urlsplit(url.strip())
    return urlunsplit((
        parts.scheme,
        _ascii_netloc(parts.netloc),
        _quote_component(parts.path, PATH_SAFE),
        _quote_component(parts.query, QUERY_SAFE),
        _quote_component(parts.fragment, QUERY_SAFE),
    ))


def _readable_escapes(match: re.Match) -> str:
    data = bytes.fromhex(match.group(0).replace("%", ""))
    out: list[str] = []
    index = 0
    while index < len(data):
        byte = data[index]
        size = 1 if byte < 0x80 else 2 if 0xC2 <= byte <= 0xDF else 3 if 0xE0 <= byte <= 0xEF else 4 if 0xF0 <= byte <= 0xF4 else 0
        try:
            char = data[index:index + size].decode("utf-8") if size else ""
        except UnicodeDecodeError:
            char = ""
        if char and (char in UNRESERVED or (not char.isascii() and char.isprintable() and not char.isspace())):
            out.append(char)
            index += size
        else:
            out.append(f"%{byte:02X}")
            index += 1
    return "".join(out)


def to_iri(url: str) -> str:
    """Readable canonical form of a URL: ASCII (punycode) host, but UTF-8 escapes of letters decoded ("/%C3%BCber-uns" →
    "/über-uns"). Reserved characters, spaces, controls and invalid UTF-8 stay percent-encoded, so to_uri(to_iri(u))
    addresses the same resource; spellings that differ only in escaping get the same form.
    """
    parts = urlsplit(to_uri(url))
    return urlunsplit((parts.scheme, parts.netloc, *(ESCAPE_RUN.sub(_readable_escapes, value) for value in (parts.path, parts.query, parts.fragment))))


def header_text(value: str) -> str:
    """A header value as text: http.client decodes header bytes as Latin-1, so raw UTF-8 in a Location header arrives as
    mojibake ("/Ã¼ber-uns") and is decoded again; other non-ASCII bytes are percent-encoded byte by byte."""
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return "".join(char if char.isascii() else "".join(f"%{byte:02X}" for byte in char.encode("latin-1", "replace")) for char in value)
# --- end IRI → URI -------------------------------------------------------------------------------------------------


def normalize_url(url: str) -> str:
    """Canonical inventory form: no fragment or tracking parameters, lowercase scheme and host, sorted query, IDNA host,
    and readable escapes (see to_iri), so "/über-uns", "/%C3%BCber-uns" and "/%c3%bcber-uns" are one page.

    import-redirects accepts this form as `from` (it percent-decodes paths); requests always go out as to_uri().
    """
    url, _fragment = urldefrag(url.strip())
    parts = urlsplit(to_uri(url))
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS and not key.lower().startswith(TRACKING_PREFIXES)
    ]
    path = parts.path or "/"
    return to_iri(urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(sorted(query)), "")))


def host_key(url: str) -> str:
    """Host (with port) without a leading www., so www and apex count as the same site."""
    netloc = _ascii_netloc(urlsplit(url).netloc)
    return netloc[4:] if netloc.startswith("www.") else netloc


def is_asset(url: str) -> bool:
    return urlsplit(url).path.lower().endswith(ASSET_EXTENSIONS)


def _dimension(value: str) -> int | None:
    """A width/height attribute as whole pixels ("800", "800px"); None when absent or relative ("100%", "auto")."""
    match = re.fullmatch(r"\s*(\d+)(?:\.\d+)?\s*(?:px)?\s*", value or "")
    return int(match.group(1)) if match else None


def jsonld_types(data) -> list[str]:
    """@type values of a JSON-LD document: top-level objects, lists and @graph members (nested values are left out)."""
    items = data if isinstance(data, list) else [data]
    types: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get("@type")
        for type_ in value if isinstance(value, list) else [value]:
            if isinstance(type_, str) and type_ and type_ not in types:
                types.append(type_)
        if isinstance(item.get("@graph"), list):
            types.extend(type_ for type_ in jsonld_types(item["@graph"]) if type_ not in types)
    return types


def empty_page_fields() -> dict:
    """The SEO and content fields of a record that is no HTML page (or could not be read): appended after lastmod."""
    return {"description": "", "h1": "", "h1_count": 0, "lang": "", "hreflang": [], "jsonld_types": [], "og_image": "", "images": [], "word_count": 0, "forms": 0}


class PageParser(HTMLParser):
    """Collects the title, the canonical link, every href/src and the SEO/content facts of one HTML page.

    Facts: meta description, the first h1 (and how many there are), <html lang>, hreflang alternates, JSON-LD @types,
    og:image, images (src, width/height attributes when present, alt: None when the attribute is missing, "" when
    empty; lazy-loaded <img> sources such as data-src, data-orig-src and data-lazy-src count too), lazy CSS background
    images (Avada/Elementor/WP Rocket data-bg, data-bg-url, data-background, data-src on non-img elements, inline
    style background(-image): url(...)) as {src, background: true, via: <attribute>}: page-header and card photos often
    exist only there, the word count of the main text (inside <main> when the page has one, else the body without nav, header
    and footer; scripts and styles never count) and the number of forms.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.canonical = ""
        self.links: list[str] = []
        self.description = ""
        self.h1 = ""
        self.h1_count = 0
        self.lang = ""
        self.hreflang: list[dict] = []
        self.jsonld_types: list[str] = []
        self.og_image = ""
        self.images: list[dict] = []
        self.forms = 0
        self.main_words = 0
        self.body_words = 0
        self.has_main = False
        self._in_title = False
        self._in_h1 = False
        self._jsonld: str | None = None
        self._skip = 0
        self._chrome = 0
        self._main = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): (value or "") for name, value in attrs}
        present = {name.lower() for name, _value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "html" and attributes.get("lang"):
            self.lang = attributes["lang"].strip()
        elif tag == "link":
            rel = attributes.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = attributes.get("href", "")
            elif "alternate" in rel and attributes.get("hreflang") and attributes.get("href"):
                self.hreflang.append({"lang": attributes["hreflang"].strip(), "url": attributes["href"].strip()})
        elif tag == "meta":
            key = (attributes.get("name") or attributes.get("property") or "").lower()
            if key == "description" and not self.description:
                self.description = " ".join(attributes.get("content", "").split())
            elif key in ("og:image", "og:image:url", "og:image:secure_url") and not self.og_image:
                self.og_image = attributes.get("content", "").strip()
        elif tag == "h1":
            self.h1_count += 1
            self._in_h1 = self.h1_count == 1
        elif tag == "form":
            self.forms += 1
        elif tag == "script" and attributes.get("type", "").lower().strip() == "application/ld+json":
            self._jsonld = ""
        if tag in ("a", "area") and attributes.get("href"):
            self.links.append(attributes["href"])
        elif tag in ("img", "source", "embed", "iframe") and attributes.get("src"):
            self.links.append(attributes["src"])
        elif tag == "object" and attributes.get("data"):
            self.links.append(attributes["data"])
        if tag not in NOT_BACKGROUND_TAGS:
            self._background_images(attributes)
        if tag == "img" and len(self.images) < MAX_IMAGES_PER_PAGE:
            src = attributes.get("src") or ""
            if not src or src.startswith("data:"):
                src = next((attributes[name] for name in LAZY_IMG_ATTRIBUTES if attributes.get(name) and not attributes[name].startswith("data:")), src)
            if src and not src.startswith("data:"):
                self.images.append({
                    "src": src,
                    "width": _dimension(attributes.get("width", "")),
                    "height": _dimension(attributes.get("height", "")),
                    "alt": " ".join(attributes["alt"].split()) if "alt" in present else None,
                })
        if tag in SKIP_TEXT_TAGS:
            self._skip += 1
        elif tag in CHROME_TAGS:
            self._chrome += 1
        elif tag == "main" or attributes.get("role", "").lower() == "main":
            self.has_main = True
            if tag == "main":
                self._main += 1

    def _background_images(self, attributes: dict[str, str]) -> None:
        """Lazy CSS background images of one element: data-bg (and friends) and inline background(-image): url()."""
        found: list[tuple[str, str]] = []
        for name in LAZY_BG_ATTRIBUTES:
            value = attributes.get(name, "").strip()
            if value:
                urls = [match[1] for match in CSS_URL.findall(value)] or [value]
                found.extend((url, name) for url in urls)
        style = attributes.get("style", "")
        if "background" in style.lower():
            found.extend((match[1], "style") for match in CSS_URL.findall(style))
        for raw, via in found:
            src = raw.strip().strip("'\"").strip()
            if not src or src.startswith(("data:", "#", "var(")) or len(self.images) >= MAX_IMAGES_PER_PAGE:
                continue
            if any(image["src"] == src for image in self.images):
                continue
            self.links.append(src)
            self.images.append({"src": src, "width": None, "height": None, "alt": None, "background": True, "via": via})

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "script" and self._jsonld is not None:
            try:
                found = jsonld_types(json.loads(self._jsonld))
            except ValueError:
                found = []
            self.jsonld_types.extend(type_ for type_ in found if type_ not in self.jsonld_types)
            self._jsonld = None
        if tag in SKIP_TEXT_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in CHROME_TAGS:
            self._chrome = max(0, self._chrome - 1)
        elif tag == "main":
            self._main = max(0, self._main - 1)

    def handle_data(self, data: str) -> None:
        if self._jsonld is not None:
            self._jsonld += data
            return
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1 += data
        if self._skip or self._in_title:
            return
        words = len(WORD.findall(data))
        if self._main:
            self.main_words += words
        if not self._chrome:
            self.body_words += words

    @property
    def word_count(self) -> int:
        return self.main_words if self.has_main and self.main_words else self.body_words


class SitemapParser(HTMLParser):
    """Reads <urlset> and <sitemapindex> documents with XML namespaces resolved by hand.

    HTMLParser instead of ElementTree: not every Python build ships expat, and it tolerates sloppy XML. Only the
    `<loc>` / `<lastmod>` that are direct children of `<url>` / `<sitemap>` in the sitemap namespace (or without one)
    count: `<image:loc>`, `<video:content_loc>` and `<xhtml:link>` of Yoast/Google extension sitemaps never leak into the URL.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.kind = ""
        self.urls: list[dict] = []
        self.sitemaps: list[str] = []
        self._stack: list[tuple[bool, str, dict]] = []  # (is sitemap namespace, local name, prefix -> namespace)
        self._entry: dict = {}
        self._field = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        scope = dict(self._stack[-1][2]) if self._stack else {}
        for name, value in attrs:
            if name == "xmlns":
                scope[""] = value or ""
            elif name.startswith("xmlns:"):
                scope[name[6:]] = value or ""
        prefix, _, local = tag.rpartition(":")
        namespace = scope.get(prefix) if prefix else scope.get("", "")
        ours = namespace in (SITEMAP_NS, "")
        parent_is_entry = bool(self._stack) and len(self._stack) == 2 and self._stack[-1][0] and self._stack[-1][1] in ("url", "sitemap")
        self._stack.append((ours, local, scope))

        if len(self._stack) == 1:
            if ours and local in ("urlset", "sitemapindex"):
                self.kind = local
        elif ours and self.kind and len(self._stack) == 2 and local in ("url", "sitemap"):
            self._entry = {"loc": "", "lastmod": ""}
        elif ours and parent_is_entry and local in ("loc", "lastmod"):
            self._field = local

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        ours, local, _scope = self._stack.pop()
        if self._field and local == self._field:
            self._field = ""
        elif ours and len(self._stack) == 1 and local in ("url", "sitemap") and self._entry.get("loc"):
            if local == "url":
                self.urls.append({"url": self._entry["loc"].strip(), "lastmod": self._entry["lastmod"].strip()[:10]})
            else:
                self.sitemaps.append(self._entry["loc"].strip())
            self._entry = {}

    def handle_data(self, data: str) -> None:
        if self._field:
            self._entry[self._field] = self._entry.get(self._field, "") + data

    def unknown_decl(self, data: str) -> None:  # <![CDATA[ ... ]]>
        if self._field and data.upper().startswith("CDATA["):
            self._entry[self._field] = self._entry.get(self._field, "") + data[6:]


def parse_sitemap_xml(body: bytes) -> tuple[str, list[dict], list[str]]:
    """(kind, page entries, child sitemap URLs) of a `<urlset>` or `<sitemapindex>`; kind is "" when it is neither."""
    parser = SitemapParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    parser.close()
    return parser.kind, parser.urls, parser.sitemaps


class IriRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follows redirects whose Location holds raw UTF-8 bytes or a non-ASCII host by requesting its ASCII URI."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        location = headers.get("Location") or headers.get("URI")
        if location:
            try:
                newurl = to_uri(urljoin(req.full_url, header_text(location)))
            except ValueError:
                pass
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    """Rate-limited HTTP client that follows redirects and never raises for HTTP status codes.

    Every URL (IRIs with umlauts or IDN hosts included) is sent as its ASCII URI (to_uri); http.client would
    otherwise fail with UnicodeEncodeError on the request line.
    """

    def __init__(self, delay: float, timeout: float, user_agent: str) -> None:
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent
        self.opener = urllib.request.build_opener(IriRedirectHandler)
        self._last_request = 0.0

    def get(self, url: str, method: str = "GET") -> dict:
        wait = self._last_request + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

        try:
            request = urllib.request.Request(to_uri(url), method=method, headers={"User-Agent": self.user_agent, "Accept-Encoding": "identity"})
        except ValueError as error:
            return {"status": 0, "final_url": url, "headers": {}, "body": b"", "error": f"invalid URL: {error}"}
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read() if method == "GET" else b""
                return {"status": response.status, "final_url": response.geturl(), "headers": response.headers, "body": body}
        except urllib.error.HTTPError as error:
            error.close()
            return {"status": error.code, "final_url": error.geturl() or url, "headers": error.headers, "body": b""}
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            reason = getattr(error, "reason", error)
            return {"status": 0, "final_url": url, "headers": {}, "body": b"", "error": str(reason)}


def decode_body(body: bytes, headers) -> str:
    charset = "utf-8"
    content_type = headers.get("Content-Type", "") if headers else ""
    if "charset=" in content_type:
        charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def last_modified(headers) -> str:
    value = headers.get("Last-Modified") if headers else None
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return ""


def looks_like_html(body: bytes, headers) -> bool:
    content_type = (headers.get("Content-Type", "") if headers else "").lower()
    head = body[:512].lstrip().lower()
    return "html" in content_type or head.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))


def load_robots(fetcher: Fetcher, base: str, warnings: list[str]) -> tuple[urllib.robotparser.RobotFileParser, list[str]]:
    robots_url = urljoin(base, "/robots.txt")
    parser = urllib.robotparser.RobotFileParser(robots_url)
    result = fetcher.get(robots_url)
    lines: list[str] = []
    if result["status"] != 200:
        warnings.append(f"robots.txt answered {result['status'] or result.get('error', 'no response')} ({robots_url}): no crawl rules and no Sitemap line known, everything is treated as allowed.")
    elif looks_like_html(result["body"], result["headers"]):
        warnings.append(f"robots.txt returned HTML instead of text ({robots_url}): probably a catch-all page of the site, ignored.")
    else:
        lines = decode_body(result["body"], result["headers"]).splitlines()
    parser.parse(lines)
    sitemaps = [line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("sitemap:")]
    return parser, sitemaps


def parse_sitemap(fetcher: Fetcher, url: str, seen: set[str], warnings: list[str]) -> list[dict]:
    """Entries ({url, lastmod}) of a sitemap, following sitemap indexes; [] (plus a warning) when it is missing or invalid."""
    if url in seen or len(seen) >= MAX_SITEMAPS:
        return []
    seen.add(url)
    result = fetcher.get(url)
    if result["status"] != 200:
        warnings.append(f"Sitemap {url} answered {result['status'] or result.get('error', 'no response')}.")
        return []
    body = result["body"]
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except OSError:
            warnings.append(f"Sitemap {url} is not valid gzip.")
            return []
    kind, urls, sitemaps = parse_sitemap_xml(body)
    if not kind:
        what = "HTML (a catch-all or error page)" if looks_like_html(body, result["headers"]) else "something that is not a sitemap (no <urlset> or <sitemapindex>)"
        warnings.append(f"Sitemap {url} returned {what}.")
        return []
    entries = list(urls)
    for location in sitemaps:
        entries.extend(parse_sitemap(fetcher, location, seen, warnings))
    return entries


def inspect(fetcher: Fetcher, url: str, lastmod: str = "") -> tuple[dict, list[str]]:
    """Fetches one URL and returns its inventory record plus the links found on it (HTML only)."""
    asset = is_asset(url)
    result = fetcher.get(url, method="HEAD" if asset else "GET")
    if asset and result["status"] in (405, 501):
        result = fetcher.get(url)
    headers = result["headers"] or {}
    content_type = (headers.get("Content-Type", "") or "").split(";")[0].strip()
    record = {
        "url": url,
        "final_url": normalize_url(result["final_url"]),
        "status": result["status"],
        "content_type": content_type,
        "title": "",
        "canonical": "",
        "lastmod": lastmod or last_modified(headers),
        **empty_page_fields(),
    }
    if "error" in result:
        record["error"] = result["error"]
    links: list[str] = []
    if content_type in ("text/html", "application/xhtml+xml") and result["body"]:
        parser = PageParser()
        parser.feed(decode_body(result["body"], headers))
        record["title"] = " ".join(parser.title.split())
        try:
            record["canonical"] = to_iri(urljoin(result["final_url"], parser.canonical)) if parser.canonical else ""
        except ValueError:
            record["canonical"] = parser.canonical
        record.update(page_facts(parser, result["final_url"]))
        links = [urljoin(result["final_url"], link) for link in parser.links]
    return record, links


def _absolute(base: str, url: str) -> str:
    try:
        return to_iri(urljoin(base, url))
    except ValueError:
        return url


def page_facts(parser: PageParser, base: str) -> dict:
    """The SEO and content fields of a parsed HTML page, URLs made absolute (readable form, like `url`)."""
    return {
        "description": parser.description,
        "h1": " ".join(parser.h1.split()),
        "h1_count": parser.h1_count,
        "lang": parser.lang,
        "hreflang": [{"lang": item["lang"], "url": _absolute(base, item["url"])} for item in parser.hreflang],
        "jsonld_types": parser.jsonld_types,
        "og_image": _absolute(base, parser.og_image) if parser.og_image else "",
        "images": [{**image, "src": _absolute(base, image["src"])} for image in parser.images],
        "word_count": parser.word_count,
        "forms": parser.forms,
    }


def classify_external(url: str) -> str:
    """Kind of an other-host target worth listing ("pdf", "jobs", "booking", "chat", "review"), else ""."""
    parts = urlsplit(url)
    host = parts.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    path = parts.path.lower()
    if path.endswith(".pdf") or any(host == h or host.endswith("." + h) for h in FILE_HOSTS):
        return "pdf"
    for kind, fragments in EXTERNAL_HOSTS.items():
        if any(fragment in host for fragment in fragments):
            return kind
    if any(word in path for word in JOB_PATH_WORDS):
        return "jobs"
    return ""


RENDER_HINT = (
    "--render needs a headless browser and none was found. Install one of: `pip install playwright && playwright install chromium`, "
    "or `npm i -g agent-browser && agent-browser install`. Continuing with the static HTML only."
)
LINK_COLLECTOR_JS = (
    "[...document.querySelectorAll('a[href],area[href],iframe[src],embed[src],object[data],source[src]')]"
    ".map(e=>e.href||e.src||e.data).filter(Boolean)"
)


def find_renderer():
    """A function url -> rendered link URLs (None on failure), or None when no headless Chrome is available."""
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        pass
    else:
        return render_links_playwright
    if shutil.which("agent-browser"):
        return render_links_agent_browser
    return None


def render_links_playwright(url: str, timeout: float = 20.0) -> list[str] | None:
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
                page.wait_for_timeout(1000)
                return [link for link in page.evaluate(LINK_COLLECTOR_JS) if isinstance(link, str)]
            finally:
                browser.close()
    except Exception:  # noqa: BLE001 - a failing render must never abort the inventory
        return None


def render_links_agent_browser(url: str, timeout: float = 45.0) -> list[str] | None:
    def run(*args: str) -> str:
        return subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout, check=True).stdout.strip()

    try:
        run("open", url)
        try:
            run("wait", "--load", "networkidle")
        except (subprocess.SubprocessError, OSError):
            run("wait", "2000")
        value = json.loads(run("eval", f"JSON.stringify({LINK_COLLECTOR_JS})"))
        if isinstance(value, str):
            value = json.loads(value)
        return [link for link in value if isinstance(link, str)]
    except (subprocess.SubprocessError, OSError, ValueError):
        return None
    finally:
        try:
            run("close")
        except (subprocess.SubprocessError, OSError):
            pass


def crawl(start: str, max_pages: int, fetcher: Fetcher, log=print, render: bool = False, render_limit: int = 20, renderer=None) -> dict:
    start = normalize_url(start)
    site = host_key(start)
    warnings: list[str] = []
    robots, sitemap_urls = load_robots(fetcher, start, warnings)
    if not sitemap_urls:
        sitemap_urls = [urljoin(start, "/sitemap.xml"), urljoin(start, "/sitemap_index.xml")]

    seen_sitemaps: set[str] = set()
    sitemap_entries: list[dict] = []
    for sitemap_url in sitemap_urls:
        sitemap_entries.extend(parse_sitemap(fetcher, sitemap_url, seen_sitemaps, warnings))
        if sitemap_entries:
            break

    sitemap_pages: dict[str, str] = {}
    for entry in sitemap_entries:
        try:
            sitemap_pages.setdefault(normalize_url(entry["url"]), entry["lastmod"])
        except ValueError:
            warnings.append(f"Sitemap entry {entry['url']!r} is not a valid URL, skipped.")

    follow_links = len(sitemap_pages) < MIN_SITEMAP_URLS
    if sitemap_pages and follow_links:
        warnings.append(f"The sitemap lists only {len(sitemap_pages)} URL(s) (fewer than {MIN_SITEMAP_URLS}): also crawling links from the start page.")
        source = "sitemap+crawl"
    else:
        source = "sitemap" if sitemap_pages else "crawl"

    if render:
        renderer = renderer or find_renderer()
        if renderer is None:
            warnings.append(RENDER_HINT)
            log(RENDER_HINT)

    records: list[dict] = []
    external: dict[str, dict] = {}
    queue: deque[str] = deque(sitemap_pages)
    if follow_links and start not in sitemap_pages:
        queue.append(start)
    queued = set(queue)
    rendered = 0

    def enqueue(links: list[str], found_on: str, how: str) -> None:
        for link in links:
            if link.lower().startswith(SKIP_SCHEMES):
                continue
            try:
                link = normalize_url(link)
            except ValueError:  # unparsable href such as "http://[broken"
                continue
            if urlsplit(link).scheme not in ("http", "https"):
                continue
            if host_key(link) != site:
                kind = classify_external(link)
                if kind and link not in external:
                    external[link] = {"url": link, "kind": kind, "host": urlsplit(link).netloc.lower(), "found_on": found_on, "via": how}
            elif follow_links and link not in queued:
                queued.add(link)
                queue.append(link)

    while queue and len(records) < max_pages:
        url = queue.popleft()
        if not robots.can_fetch(fetcher.user_agent, to_uri(url)):
            records.append({"url": url, "final_url": url, "status": None, "content_type": "", "title": "", "canonical": "", "lastmod": "", **empty_page_fields(), "error": "disallowed by robots.txt"})
            continue
        record, links = inspect(fetcher, url, sitemap_pages.get(url, ""))
        records.append(record)
        log(f"{record['status']} {url}")
        if host_key(record["final_url"]) != site:
            continue
        if follow_links and record["final_url"] not in queued:
            queued.add(record["final_url"])
            queue.append(record["final_url"])
        enqueue(links, record["final_url"], "html")
        if renderer is not None and record["content_type"] in HTML_TYPES and rendered < render_limit:
            rendered += 1
            rendered_links = renderer(to_uri(record["final_url"]))
            if rendered_links is None:
                warnings.append(f"Rendering {record['final_url']} failed; static links only.")
            else:
                enqueue(rendered_links, record["final_url"], "render")

    if not render and len(records) <= 1 and not external:
        warnings.append("Only one URL was found and it links nowhere: the site is probably built with JavaScript (Readymag, Wix, SPA). Retry with --render.")

    return {
        "site": start,
        "source": source,
        "rendered": render and renderer is not None,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "count": len(records),
        "pages": records,
        "external": sorted(external.values(), key=lambda item: (item["kind"], item["url"])),
        "warnings": warnings,
    }


def sitemap_xml(inventory: dict) -> str:
    """A sitemap of the reachable HTML pages (status 200, not redirected), sorted; `<loc>` percent-encoded as the
    sitemap protocol requires (import-redirects decodes it, so it matches the readable form in urls.json)."""
    pages = sorted(
        {page["final_url"]: page for page in inventory["pages"]
         if page["status"] == 200 and page["content_type"] in ("text/html", "application/xhtml+xml")
         and normalize_url(page["url"]) == page["final_url"]}.values(),
        key=lambda page: page["final_url"],
    )
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page in pages:
        lastmod = f"<lastmod>{escape(page['lastmod'])}</lastmod>" if page["lastmod"] else ""
        lines.append(f"  <url><loc>{escape(to_uri(page['final_url']))}</loc>{lastmod}</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory every URL of a website (sitemap first, then crawl).")
    parser.add_argument("url", help="Start URL, e.g. https://www.example.de")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum number of URLs to inspect (default 500)")
    parser.add_argument("--out", default="urls.json", help="JSON inventory path (default urls.json)")
    parser.add_argument("--sitemap-out", default=None, help="Generated sitemap path (default: sitemap.xml next to --out)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default 0.5)")
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds (default 15)")
    parser.add_argument("--user-agent", default=USER_AGENT)
    parser.add_argument("--render", action="store_true", help="Also read links built by JavaScript with headless Chrome (playwright or agent-browser)")
    parser.add_argument("--render-pages", type=int, default=20, help="Maximum number of pages to render with --render (default 20)")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary")
    args = parser.parse_args(argv)

    if urlsplit(args.url).scheme not in ("http", "https"):
        parser.error("url must start with http:// or https://")

    fetcher = Fetcher(delay=args.delay, timeout=args.timeout, user_agent=args.user_agent)
    log = (lambda _message: None) if args.quiet else (lambda message: print(message, file=sys.stderr))
    inventory = crawl(args.url, args.max_pages, fetcher, log, render=args.render, render_limit=args.render_pages)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sitemap_path = Path(args.sitemap_out) if args.sitemap_out else out.with_name("sitemap.xml")
    sitemap_path.write_text(sitemap_xml(inventory), encoding="utf-8")

    broken = sum(1 for page in inventory["pages"] if not page["status"] or page["status"] >= 400)
    print(f"{inventory['count']} URLs from {inventory['source']} → {out} and {sitemap_path} ({broken} broken)")
    if inventory["external"]:
        print(f"External targets ({len(inventory['external'])}):")
        for item in inventory["external"]:
            print(f"  [{item['kind']}] {item['url']}  (on {item['found_on']})")
    for warning in inventory["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
