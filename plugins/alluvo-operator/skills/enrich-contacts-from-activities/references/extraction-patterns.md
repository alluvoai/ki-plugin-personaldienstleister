# Extraction & Derivation Patterns

How to turn raw communication text into proposed Contact field values, with confidence scoring.
German-market focus (DE primary, EN secondary).

## Table of contents
- Locating the signature block
- Field-by-field extraction
- Normalization rules
- Language detection → preferred_language
- Engagement signals (read-only)
- Confidence scoring
- What NOT to extract

## Locating the signature block

In an email body, the signature is the trailing block after the last salutation/closing. Anchor on:
- German closings: `Mit freundlichen Grüßen`, `Viele Grüße`, `Beste Grüße`, `Freundliche Grüße`, `MfG`, `i. A.`, `i. V.`, `ppa.`
- English closings: `Best regards`, `Kind regards`, `Regards`, `Best`, `Sincerely`, `Cheers`
- Or the `-- ` (dash-dash-space) signature delimiter.

Take the lines AFTER the closing up to quoted history (`>`, `Von:`/`From:`, `Am … schrieb`,
`On … wrote`, `Gesendet von meinem iPhone`). Prefer the **most recent** email; corroborate a value
if it recurs across several emails (raises confidence). Calls/meetings/notes are secondary, free-text
sources — extract the same fields when explicitly stated ("erreichbar mobil unter …", "ihr LinkedIn …").

## Field-by-field extraction

| Field | Where it shows up | Notes |
|-------|-------------------|-------|
| `mobile` | lines `Mobil`, `Mobile`, `Handy`, `M:`, `Cell`, a `+49 1xx` number | German mobiles start `01`/`+49 1`. Distinguish from landline. |
| `phone` | `Tel`, `Telefon`, `T:`, `Fon`, `Direkt`, `Durchwahl`, `Office`, landline `+49 <area>` | If only one number and it's a landline → `phone`. If labelled "Durchwahl/Direkt" it's still `phone`. |
| `title` | the **role/job line** under the name: `Geschäftsführer`, `Pflegedienstleitung` (PDL), `Einrichtungsleitung` (EL), `Heimleitung`, `Personalleitung`, `HR Manager`, `Prokurist`, `Inhaber` | This is the person's professional/role title. NOTE: academic prefixes (`Dr.`, `Prof.`) belong to the person's name prefix, not this `title` — if the field model already separates them, keep academic prefixes out of `title`. When unsure, propose the role string and flag for review. |
| `salutation` | derived from how they sign / how they're addressed: `Herr`/`Frau` → `Herr`/`Frau`; `Dear Mr/Ms` → map | Low-confidence from signature alone; prefer explicit `Sehr geehrte Frau …` in the body addressing them. |
| `linkedin_url` | `linkedin.com/in/…` anywhere in the block or notes | Canonicalize (below). |
| `xing_url` | `xing.com/profile/…` or `xing.com/…` | Canonicalize. |
| `website_url` | a company/personal URL line, or the domain after `www.` | Prefer an explicit website line; the email domain is a weaker signal. |

A signature usually clusters several of these — extract them together and attribute them all to
"email sig" with a single evidence pointer.

## Normalization rules

- **Phone / mobile → E.164-ish German format**: strip spaces/`/`/`-`/`(0)`; `0049…`→`+49…`;
  leading `0`→`+49` (drop the 0); keep a single leading `+`. Reject anything that isn't a plausible
  DE/international number. Example: `0171 / 555 12 34` → `+49 171 5551234`.
- **URLs → canonical https**: lowercase host, add `https://`, strip tracking query params and
  trailing slash. LinkedIn → `https://www.linkedin.com/in/<slug>`. Xing → `https://www.xing.com/profile/<slug>`.
  Website → `https://<host>` (keep path only if meaningful).
- **title**: trim, collapse whitespace, keep original German casing/term (do not translate
  `Pflegedienstleitung` → "Nursing director").
- Reject values equal to the tenant's own domain/role boilerplate (e.g. the agency's own footer).

## Language detection → preferred_language

Set `preferred_language` ONLY on strong signals (else leave for review):
- The person's own emails are consistently written in German → `de`; in English → `en`.
- An explicit statement ("bitte auf Deutsch", "please write in English").
- A German closing + German role line is a strong `de` signal.
Do not infer language from a single short message. Values are strictly `de` / `en`.

`preferred_language` is an **app/UI locale** — the language alluvo renders emails,
notifications and AI replies in — so it is limited to the locales that actually have
translations (`de` / `en`). It is *not* a "which languages does this person speak" field,
even though both use the same ISO-code vocabulary. Anything else (`tr`, `ru`, `ar`, …) is
rejected with a validation error on the `manage-model` preview.

So when the evidence says the person **speaks** a third language (a Turkish signature, "ich
spreche auch Russisch"), do **not** force it into `preferred_language`. That is a spoken-language
fact belonging to `ContactLanguage` (`0-185`) — out of scope for this skill's identity-field
enrichment; report it and let `→ onboard-new-employee` (step 2, CV buckets) write it. Their
`preferred_language` stays `de` unless they write to you in English.

## Engagement signals (read-only — report, never write)

From the timeline, summarize per contact (for the report + ranking, not as field writes):
- **Last contact date** ← `last_activity_at` (already on the contact).
- **Channel mix** ← counts of emails vs calls vs meetings in the window → suggests a preferred
  contact channel (report-only; no column to write — optionally a custom field).
- **Communication language** ← from language detection above (this one DOES map to writable
  `preferred_language`).
- **Responsiveness / recency** ← gap since last inbound; useful for prioritizing the batch.

## Confidence scoring

- **high**: value appears in an email signature block, normalized cleanly, and either recurs across
  ≥2 emails or is unambiguous (e.g. an explicit `Mobil:` line).
- **med**: single occurrence, or from a free-text call/meeting note, or required light inference.
- **low**: weak inference (salutation from tone, website = email domain, role guessed). Exclude from
  the default table unless asked.
Always attach the evidence (source type + which record) to every proposed row.

## What NOT to extract

- Anything not volunteered by the person in their own communication (no web scraping here).
- Other people's details quoted in the thread (CC'd colleagues, forwarded signatures) — only the
  Contact's own signature.
- Marketing/footer boilerplate, disclaimers, Handelsregister/USt-IdNr legal lines, bank details.
- Values that would overwrite a populated field without an explicit conflict decision.
