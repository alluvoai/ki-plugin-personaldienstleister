#!/usr/bin/env python3
"""Verify the redirects of a migrated website after the DNS cutover.

Usage:
    python3 verify-redirects.py redirects.csv [--base https://www.new-domain.de] [--json report.json]
        [--insecure | --cafile ca.pem]

The mapping is a CSV with the columns old,new (a header row is optional) or JSON: either
[{"old": "...", "new": "..."}] or {"old": "new"}. Relative URLs ("/stellenangebote.html") are resolved
against --base. Write targets as paths or URLs: "page:<id>" targets of import-redirects have no local lookup here —
manage-site (action "get", resource "page") returns each page's paths.

TLS: local Herd sites (*.test) use a CA that Python 3.13 rejects ("Missing Authority Key Identifier", strict X.509
checks). --cafile <ca.pem> trusts that CA without the strict flag; --insecure skips certificate checks entirely
(local checks only). SSL and network errors are printed with their reason.

For every old URL the check expects exactly ONE 301 redirect (max one hop) straight to the mapped target,
and the target must answer 200. An old URL equal to its target must answer 200 itself. Reported problems:
WRONG_STATUS (e.g. 302 instead of 301), WRONG_TARGET, CHAIN (more than one hop), LOOP, TARGET_NOT_200,
NOT_REDIRECTED, ERROR (network). Exit code 1 when anything failed. Python 3.9+, standard library only.

URLs may contain umlauts or IDN hosts ("/über-uns", müller-personal.de): they are requested as ASCII URIs (IDNA host,
UTF-8 percent-encoding, existing %XX escapes kept) and compared regardless of how they are percent-encoded.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

USER_AGENT = "AlluvoRedirectCheck/1.0 (+https://alluvo.ai)"
MAX_HOPS = 10
DEFAULT_PORTS = {"http": 80, "https": 443}


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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def configure_tls(insecure: bool, cafile: str | None) -> None:
    """Install the opener with the requested TLS context (default: system trust store, full verification)."""
    global OPENER
    if not insecure and not cafile:
        return
    if insecure:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context = ssl.create_default_context(cafile=cafile)
    # Python 3.13 enables VERIFY_X509_STRICT, which rejects local CAs such as Herd's (no Authority Key Identifier).
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    OPENER = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=context))


def error_reason(error: BaseException) -> str:
    """A readable reason, never \"None\": SSL verification details, socket errors, timeouts."""
    reason = getattr(error, "reason", None)
    if isinstance(reason, ssl.SSLCertVerificationError):
        return f"SSL: {reason.verify_message or reason} (local CA? use --cafile <ca.pem> or --insecure)"
    if isinstance(reason, BaseException):
        return f"{type(reason).__name__}: {reason}"
    if reason:
        return str(reason)
    return f"{type(error).__name__}: {error}" if str(error) else type(error).__name__


def resolve_reference(target: str, base: str | None, org: str | None, locale: str) -> str:
    """page:<id> / media:<id> (import-redirects notation): not resolvable offline — the mapping needs the URL."""
    raise SystemExit(f"{target}: write the target as a path or URL (manage-site action \"get\" resource \"page\" returns its paths).")

def canonical(url: str) -> str:
    """Comparable form: lowercase scheme/host (IDNA), no default port, "/" for an empty path, no fragment, escapes
    normalized (to_iri), so "/das-menü" and "/das-men%C3%BC" compare equal."""
    parts = urlsplit(to_iri(url))
    host = (parts.hostname or "").lower()
    port = f":{parts.port}" if parts.port and parts.port != DEFAULT_PORTS.get(parts.scheme.lower()) else ""
    return urlunsplit((parts.scheme.lower(), host + port, parts.path or "/", parts.query, ""))


def load_mapping(path: str, base: str | None, org: str | None = None, locale: str = "de") -> list[tuple[str, str]]:
    text = Path(path).read_text(encoding="utf-8-sig")
    pairs: list[tuple[str, str]] = []
    if path.lower().endswith(".json"):
        data = json.loads(text)
        items = data.items() if isinstance(data, dict) else ((row["old"], row["new"]) for row in data)
        pairs = [(str(old), str(new)) for old, new in items]
    else:
        for row in csv.reader(text.splitlines()):
            if len(row) < 2 or not row[0].strip() or row[0].strip().startswith("#"):
                continue
            if row[0].strip().lower() in ("old", "from", "source", "alt") and not pairs:
                continue
            pairs.append((row[0].strip(), row[1].strip()))

    def resolve(url: str) -> str:
        if url.split(":", 1)[0] in ("page", "media") and url.split(":", 1)[1].isdigit():
            return resolve_reference(url, base, org, locale)
        if urlsplit(url).scheme:
            return url
        if not base:
            raise SystemExit(f"Relative URL {url!r} needs --base https://new-domain")
        return urljoin(base.rstrip("/") + "/", url.lstrip("/"))

    return [(resolve(old), resolve(new)) for old, new in pairs]


def request(url: str, timeout: float) -> tuple[int, str]:
    """Status and absolute Location (may be "") of one request without following redirects.

    The URL is sent as its ASCII URI (umlaut paths and IDN hosts included); the Location is returned as an ASCII URI
    too, also when the server wrote raw UTF-8 bytes into the header.
    """
    req = urllib.request.Request(to_uri(url), headers={"User-Agent": USER_AGENT})
    try:
        with OPENER.open(req, timeout=timeout) as response:
            return response.status, ""
    except urllib.error.HTTPError as error:
        location = error.headers.get("Location", "") if error.headers else ""
        error.close()
        return error.code, to_uri(urljoin(req.full_url, header_text(location))) if location else ""


def check(old: str, new: str, timeout: float = 15.0) -> dict:
    result = {"old": old, "expected": new, "status": None, "location": "", "hops": [], "target_status": None, "problem": ""}
    try:
        chain: list[tuple[str, int]] = []
        url = old
        seen = set()
        while True:
            status, location = request(url, timeout)
            chain.append((url, status))
            if status not in (301, 302, 303, 307, 308) or not location:
                break
            if canonical(location) in seen or canonical(location) == canonical(url) or len(chain) > MAX_HOPS:
                chain.append((location, -1))
                result["hops"] = [hop for hop, _ in chain]
                result["status"] = chain[0][1]
                result["problem"] = "LOOP"
                return result
            seen.add(canonical(url))
            url = location
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
        result["problem"] = "ERROR"
        result["error"] = error_reason(error)
        return result

    redirects = chain[:-1]
    final_url, final_status = chain[-1]
    result["status"] = chain[0][1]
    result["location"] = chain[1][0] if len(chain) > 1 else ""
    result["hops"] = [hop for hop, _ in redirects]
    result["target_status"] = final_status

    if canonical(old) == canonical(new):
        result["problem"] = "" if not redirects and final_status == 200 else ("TARGET_NOT_200" if not redirects else "CHAIN")
    elif not redirects:
        result["problem"] = "NOT_REDIRECTED"
    elif redirects[0][1] != 301:
        result["problem"] = "WRONG_STATUS"
    elif len(redirects) > 1:
        result["problem"] = "CHAIN"
    elif canonical(final_url) != canonical(new):
        result["problem"] = "WRONG_TARGET"
    elif final_status != 200:
        result["problem"] = "TARGET_NOT_200"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that every old URL 301-redirects in one hop to its mapped target (200).")
    parser.add_argument("mapping", help="CSV (old,new) or JSON mapping")
    parser.add_argument("--base", help="New site base URL for relative paths, e.g. https://www.new-domain.de")
    parser.add_argument("--json", dest="json_out", help="Write the full report as JSON")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--locale", default="de", help="Language of page:<id> paths (default de, no prefix)")
    tls = parser.add_mutually_exclusive_group()
    tls.add_argument("--insecure", action="store_true", help="Skip TLS certificate checks (local Herd sites only)")
    tls.add_argument("--cafile", help="Trust this CA bundle (e.g. Herd's CA) without Python 3.13's strict X.509 checks")
    args = parser.parse_args(argv)
    configure_tls(args.insecure, args.cafile)

    results = [check(old, new, args.timeout) for old, new in load_mapping(args.mapping, args.base, None, args.locale)]
    failures = [result for result in results if result["problem"]]

    for result in results:
        label = result["problem"] or "OK"
        detail = f" → {result['location']}" if result["location"] else ""
        extra = f" (expected {result['expected']}, target {result['target_status']})" if result["problem"] else ""
        if result.get("error"):
            extra = f" — {result['error']}"
        status = result['status'] if result['status'] is not None else '---'
        print(f"{label:15} {status} {result['old']}{detail}{extra}")

    print(f"\n{len(results) - len(failures)}/{len(results)} redirects OK, {len(failures)} failed.")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps({"results": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
