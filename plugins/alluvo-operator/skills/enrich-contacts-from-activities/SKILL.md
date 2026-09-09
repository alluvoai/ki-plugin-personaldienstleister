---
name: enrich-contacts-from-activities
description: "Enrich alluvo Contacts (Kontakte anreichern) by mining their recent activity (emails, logged calls, meetings, notes) — especially email signatures — for missing contact-info fields, then writing approved changes back through the MCP so each edit is attributed to the operator and shown as 'via MCP' in the field-history sheet. Use when the user says 'enrich contacts', 'Kontakte anreichern', 'fill in contact details from their emails', 'pull phone numbers / titles / LinkedIn from email signatures', 'update contacts from recent activity', 'Kontaktdaten aus Aktivitäten befüllen', 'what can we derive from contacts emails/calls', or asks to clean up sparse Contact records using communication history. Targets contact-info identity fields (phone, mobile, title, salutation, linkedin_url, xing_url, website_url, preferred_language) and surfaces engagement signals. Also covers recording a WhatsApp consent the person gave outside alluvo, on a signed form, by phone or in person ('WhatsApp-Einwilligung erfassen', 'Kontakt hat WhatsApp zugestimmt', 'Opt-in für WhatsApp hinterlegen', 'record a WhatsApp opt-in', 'darf ich diesen Kontakt per WhatsApp anschreiben'), and pinning the du/Sie form for a contact ('Anrede festlegen', 'diesen Kontakt duze ich', 'Du/Sie für diesen Kontakt setzen', 'set the formality for this contact'). Review-first; always proposes a change table before writing."
---

# Enrich Contacts From Activities

## Purpose
Mine a Contact's own communication history (emails, calls, meetings, notes) for facts the
person volunteered — most valuably their **email signature** — and propose updates to sparse
Contact fields. Writes go through the **MCP `manage-model`** path so they are attributed to the
operator and tagged `source:mcp`, which is exactly what the field-history sheet renders as
"<operator> · via MCP". Never bulk-write blindly: produce a review table, get approval, then write.

## Identity-root rule (non-negotiable)

`Contact` (model_type **`0-105`**) is the identity root. ALWAYS read/write these fields on the
**Contact**, never on Employee (`0-2`) / Candidate (`0-81`) — those delegate to Contact and MCP
rejects identity writes on them. If you start from an Employee/Candidate, resolve its `contact_id`
first and operate on that Contact.

**Addresses are identity data too.** A person's postal address is an owned *Address* record on
the Contact, not a scalar field: read it with `manage-address` `action: "list"`
(`model_type: "0-105"`, the Contact id — current row plus history), and write it with
`manage-address` `action: "set"`, `purpose: "home"` for the private address or `"work"` for the
workplace, plus the address fields. `manage-location` no longer exists and Location (`0-95`) is
off MCP entirely — see `→ using-alluvo-operator`, *Addresses*. A Contact may hold `home`,
`second_residence`, `postal` and `work`; `model_type: "0-2"` (Employee) is rejected with a
pointer back to the linked Contact. Never try to `manage-model` an address onto the Contact.

**Enrichment is almost always a `correct`, not a `set`.** `set` closes the current row and opens
a new one — that is the record of a genuine move. Filling in a street that was missing, or fixing
a misspelt one from a signature block, is `action: "correct"`: it edits the current row in place
and writes no move into the person's address history. Only use `set` when the source actually
says the person moved.

**Give the Bundesland something to derive from.** Enriched web data often carries street + city
but no postcode. For a German address supply a correct five-digit **`zip`** and leave
`subdivision_code` empty — it is derived from the zip, more reliably than you can guess it. For
an Austrian or Swiss address there is no postcode mapping, so set `country_code` (`"AT"` / `"CH"`
— it defaults to `"DE"`) **and** `subdivision_code` explicitly. Enriched web data usually names
the region in words, and that is enough: `subdivision_code` accepts the spelled-out
Bundesland/Kanton (`"Wien"`, `"Zürich"`, `"Genf"`) as well as the ISO code and stores the ISO
form (`"DE-NW"`). If the source has no postcode, ask rather than invent one — a wrong zip
silently mislabels the Bundesland, and Feiertagszuschläge are computed from it. A German address
whose Bundesland stays unresolvable raises an **Unresolvable Federal State** issue on the Address
(`→ triage-data-quality`) rather than failing the write.

## Prerequisites

The `alluvo` MCP must be connected to the **production** org. If a call returns
"requires re-authorization", stop and ask the user to re-auth via `/mcp` → alluvo → authorize,
confirming the production org. Do not fall back to tinker for writes — tinker writes are NOT
attributed as the operator and would show as system/manual in field history (defeating the point).

## Writable vs read-only fields

**Writable enrichment targets** — confirm against `get-model-schema` (context `update`); only
fields it lists are accepted, others are **silently dropped** (no error):
`first_name`/`last_name` (data-quality fixes), `title`, `position`, `phone`, `mobile`,
`gender`, `address_formality`, `email`, `alternative_emails`, `notes`, `timezone`.

**NOT writable via MCP** (appear in `get-model` output but rejected/ignored by `manage-model`):
`salutation`, `linkedin_url`, `xing_url`, `website_url`, `preferred_language`, and the whole
`whatsapp_*` consent block (`whatsapp_opt_in_at`, `whatsapp_opt_in_source`,
`whatsapp_opt_in_reason`, `whatsapp_opt_out_at`, `whatsapp_opt_out_reason`,
`whatsapp_undeliverable_at`, `whatsapp_undeliverable_reason`) — deliberately, because a
consent needs a documented legal basis that a generic field write has nowhere to put. Read
them with `search-model` / `get-model` (naming them in `fields`), record one with the
`record-whatsapp-consent` action below. The gendered
salutation (Herr/Frau) is **derived from `gender`** — set `gender` instead. For formal vs informal
address (Sie/Du) set `address_formality` (`formal`/`informal`); B2B Kundenkontakte = `formal`.
That is the contact's **default** — a per-user override beats it, see *Pinning a du/Sie
preference* below.
Surface linkedin/xing/website/language findings in the report (and tell the user they need the UI
or a schema change to persist) rather than attempting a write that silently no-ops.

**Read-only engagement signals** — `last_activity_at`, `first_activity_at`, `next_activity_at`
are auto-maintained by the activity system. READ them to *select and rank* contacts; never write
them. There is **no** `preferred_contact_channel` column — surface that as a report-only
suggestion (optionally a custom field via `manage-custom-field`), do not try to write it.
`manage-custom-field` `create` / `update` / `archive` are now two-stage: they return a
`confirmed: false` preview first and only apply on `confirmed: true` — so defining or setting
a custom field takes two calls, not one.

## Recording a WhatsApp consent given outside alluvo (`record-whatsapp-consent`)

Activity mining does surface consent: a call note reading "hat der Kontaktaufnahme per
WhatsApp zugestimmt", a returned signed form. That fact has its own action on the Kontakt —
`manage-record-action`, `model_type: "0-105"`, `action: "record-whatsapp-consent"` — because
the consent columns are not writable through `manage-model`. It writes `whatsapp_opt_in_at`
with source `manual`, which is what puts the person into WhatsApp campaign audiences.

- **`reason` is required, 10–1000 characters, and is the point of the action** — the legal
  basis under DSGVO / UWG § 7. Write who gave the consent, when, and by what route ("Am 12.08.
  telefonisch gegenüber M. Weber der WhatsApp-Kontaktaufnahme zugestimmt"). It is stored on the
  Kontakt and shown in the timeline. Never pad it to clear the minimum — a two-word entry is
  what makes the audit trail worthless when someone asks in two years.
- **`opt_in_at` is optional, `YYYY-MM-DD`, defaults to today.** Pass the day the consent was
  *actually* given, never a later one. Any other date format is rejected, and a future date is
  refused outright.
- **Only record a consent that exists.** The evidence rule of this skill applies at its
  strictest here: no note, no mail, no form → no action. Do not run it to unblock a campaign
  send or a delivery test.
- **Two different blocks, two different answers.** The action refuses when the person already
  has an opt-in (`bereits eine WhatsApp-Einwilligung hinterlegt — sie wird nicht
  überschrieben`) and when they have opted out (`hat der Kontaktaufnahme per WhatsApp
  widersprochen …`). The first means there is nothing to do; the second means **stop** — a
  withdrawn consent is never re-recorded here, it needs its own newly documented decision.
  Read the `Unavailable reason:` from `manage-record-action` `operation: "list"` with the
  Kontakt's `record_id` and report which one you hit; never present an opt-out as a
  correctable data gap.
- Two-stage as always: `confirmed: false` preview → operator yes → `confirmed: true`. Needs
  the `contacts.update` right.

## Pinning a du/Sie preference for a contact (`set-formality-override`)

`address_formality` is the contact's own default. On top of it sits a **per-user override** —
how *one operator* addresses this person — and the override wins. Writing
`address_formality` therefore changes nothing for anybody who has pinned their own form. That
override is the only thing this action touches: `manage-record-action`,
`model_type: "0-105"`, `action: "set-formality-override"`.

- **`formality`** is `formal` (Sie) or `informal` (du). Leave it **empty to clear** the
  override — resolution then falls back to the contact default (`address_formality`), then the
  tenant's Employee/Candidate role default, then the brand setting.
- **It writes YOUR OWN preference by default.** The optional **`user_id`** pins somebody
  else's instead. The value is a **tenant User id** (resolve it with `search-model` on
  `0-1`) — not a contact and not an employee id.
- **`user_id` is gated on `users.impersonate`.** Without that permission the parameter is not
  even listed on `manage-record-action` `operation: "list"`, and a `user_id` sent anyway is
  **refused with a `user_id` validation error** — never silently rewritten to your own
  override. Passing your own id is the same as omitting it.
- Only write a colleague's preference when that colleague asked for it. Name **whose**
  preference the call will change in the preview and get the operator's yes on that name, not
  just on du/Sie.
- Two-stage as always: `confirmed: false` preview → operator yes → `confirmed: true`. Needs
  `contacts.update` on the Kontakt, plus `users.impersonate` for a foreign `user_id`.

The resolved form is what `{{contact.greeting}}` renders in an email template
(`→ profilvertrieb`, `→ call-summary`) and what `→ call-prep` reports as the formality — so when
a greeting comes out in the wrong register, fix the override or the contact default, never
the salutation inside the template.

## Steps

### 1. Select target contacts
Find contacts that (a) had recent activity and (b) have at least one empty enrichable field.
See `references/mcp-recipes.md` → "Selecting candidates". Default window: activity in the last
90 days. Prefer contacts linked to active companies/deals. Cap the first batch (~20–30) so the
review table stays reviewable.

### 2. Gather evidence per contact
For each candidate pull the timeline and the underlying records (emails, calls, meetings, notes).
See `references/mcp-recipes.md` → "Pulling evidence". Email bodies are the richest source — the
**signature block** typically carries mobile, direct line, title/role, company, website, LinkedIn/Xing.

### 3. Extract & derive
Parse signatures and note/call text into candidate field values, and detect communication
language. Follow `references/extraction-patterns.md` for the signature-block heuristics, German
salutation/title maps, phone/URL normalization, and confidence scoring. Only derive
`preferred_language` from strong signals.

### 4. Build the review table
One row per proposed change, grouped by contact:

```
Contact (id)        Field           Current → Proposed              Evidence                Conf
Dr. M. Weber (123)  title           — → Pflegedienstleitung         email sig ×3            high
Dr. M. Weber (123)  mobile          — → +49 171 5551234             email sig              high
S. Klein (456)      linkedin_url    — → linkedin.com/in/sklein      call note             med
```

Rules:
- **Only propose filling EMPTY fields by default.** If the new value conflicts with a non-empty
  current value, show it as a CONFLICT row and require an explicit decision — never silently overwrite.
- Show the evidence and a confidence (high/med/low) per the patterns file. Drop low-confidence rows
  unless the user asks to see them.
- Also print a short read-only engagement summary per contact (last contact date, channel mix,
  detected language) and any report-only suggestions (e.g. preferred channel).

### 5. Approve
Present the table and ask the user to approve all / a subset / none. Wait for an explicit go.

### 6. Write via MCP
For each approved change, write to the Contact through `manage-model` (model_type `0-105`).
See `references/mcp-recipes.md` → "Writing changes". Batch by contact (one update call per contact
with all its approved fields). This attribution path makes each edit show as
"<operator> · via MCP (manage-model)" in the field-history sheet.

### 7. Confirm
Summarize what was written per contact, note that the field-history sheet now shows the operator +
"via MCP", and list anything skipped (conflicts left unresolved, low-confidence, report-only).

## Guardrails
- GDPR/data-minimization: only use data the person volunteered in their own communications to/with
  the tenant. Do not invent or web-scrape values here.
- **Art. 9 GDPR special categories never go into a free-text field** — health, disability,
  pregnancy, religion, union or party membership, sexual orientation, criminal records. However
  plainly the person stated it in a call note or a mail, it must not land in `notes` (nor in
  `bio`, `summary`, `headline`, `availability_notes`): those fields are read far from the
  conversation that produced them, and `bio` is rendered on the **customer-facing** profile.
  alluvo has structured fields for these facts (e.g. `Employee.is_severe_disability` /
  `degree_of_disability`) — propose the structured field or a task for the responsible
  colleague, say so to the operator, and do not paraphrase the fact into somewhere it fits more
  easily. The automated write paths (AI takeover, inbox agent) refuse such a payload outright
  and name the offending field and terms; the same rule binds you on the MCP path, which does
  not refuse it for you.
- Normalize before proposing (phone → `+49…`, URLs → canonical https). Reject malformed values.
- `preferred_language` values are `de` / `en` only — it is the **app/UI locale** we render
  in, not a spoken-language field. A third language the person speaks (`tr`, `ru`, …) is
  rejected here; report it instead and let `→ onboard-new-employee` record it as a
  ContactLanguage (`0-185`).
- Idempotent: re-running must not re-propose fields already filled with the same value.

## Related skills
- `→ triage-data-quality` — the broader data-quality routine that surfaces sparse records.
- `→ merge-duplicate-companies` — when evidence reveals two records for the same company.
- `→ account-research` — use the enriched contact in a company/contact dossier.
