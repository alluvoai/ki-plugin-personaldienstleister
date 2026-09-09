---
name: triage-data-quality
description: Review, prioritize, and resolve data quality problems (Datenqualität) after an import or as a regular quality routine, including Rollenkatalog hygiene (Rollen ohne Gruppe/Level/Fachweiterbildung). Use when the operator says "Datenqualität prüfen", "Issues triagieren", "nach Import aufräumen", "check data quality", "triage issues", "bulk-resolve issues", "Rollenkatalog aufräumen", "Rollen ohne Level", "Rollen ohne Fachweiterbildung", "Fachweiterbildung setzen", "Rollen-Hierarchie pflegen", "Profil aufräumen", "Berufsstation ausblenden", or wants a structured review of data quality findings. For merging duplicate companies specifically, use merge-duplicate-companies.
---

# Triage-Data-Quality (Datenqualität sichten & beheben)

## Purpose

Systematically review data quality issues (Issues), prioritize them by severity,
and — where possible — resolve or delegate them directly. Typical use: after a
candidate or employee import, or as a regular data-quality routine.

> Issues are pure detectors — they never carry a bespoke write path. Every open
> issue names exactly which ordinary tool call fixes it (`manage-model`,
> `manage-address`, or `manage-record-action` on the issueable record); fixing
> the underlying record auto-resolves the issue. Only bookkeeping
> (resolve/dismiss/reopen, and manual fixes made outside the system) goes
> through `manage-record-action` on the Issue itself, and that call is always
> two-stage: `confirmed: false` (preview) → operator approval → `confirmed: true`.

## Prerequisites

- Tenant has active issues (e.g. after an import or during a regular quality check).
- Only use `mcp__alluvo__*` tools.

## Steps

### 1. Get an overview

Call `get-issues-overview` (`action: "overview"` is the default) — returns issue
counts by status, severity, category (`by_category`, including `formatting`),
and the `by_remediation_kind` breakdown (how many issues you fix via
`update_record`/`create_related`/`run_action`, vs. `manual`/`informational`, vs.
`auto_fix`/`agent_fix` which the automation pipeline handles — see Step 3). The
payload also carries `formatting_pending` (pending rows per deterministic
AutoFix rule, e.g. `phone_e164`, `email_lowercase`), `enrichment_pending`
(EnrichmentSuggestions awaiting operator review, per provider), and
`dashboard_url` — a deep link to the in-app Data Quality Dashboard (tabs
`overview`, `issues`, `duplicates`, `formatting`, `enrichment` via `?tab=`).
Show the summary to the operator.

### 2. List and group issues

Call `query-model` with `model_type: "0-190"` (Issue). Recommended filters, in order:

1. `status: "open"`, `severity: "high"` — block core processes or significantly
   impair reporting (e.g. a missing required field)
2. `severity: "medium"` — a judgment call for the operator, nothing is broken but
   something needs deciding (e.g. a possible duplicate contact, see 3e)
3. `severity: "low"` — cosmetic problems, completion hints

**There are exactly three severities: `high`, `medium`, `low`.** `critical` and
`info` are not values the enum carries, and filtering on either returns nothing —
`get-issues-overview`'s `by_severity` block has the same three keys. Don't skip
`medium`: it is where the possible-duplicate finding lands, so a ladder that jumps
from `high` to `low` never surfaces it.

Useful additional filters: `category`, `identifier`, `remediation_kind`,
`owner_id`, `issueable_id`. Request fields including `issueable_title` and
`remediation_kind` so each row already shows what's affected and how fixable it
is without a second call.

**Category gotcha:** `category: "contract"` means a contract is *expiring*
(Überlassungshöchstdauer, Rahmenvertrag term) — a scheduling concern, not a data
problem. A contract with missing/incomplete data is `category: "data_quality"`
even though the issueable is a contract. Don't filter contract data-quality
issues by `category: "contract"` — they won't be there. `category: "formatting"`
issues (normalization defects like un-normalized phone numbers) carry `auto_fix`
or `agent_fix` remediation and belong to the automation pipeline, not to this
triage loop — skip them here and point the operator at the dashboard instead.
`category: "staffing"` is likewise not a data problem — it is unfilled work
(see 3f) and belongs to Disposition, so route it rather than triaging it.

**Not every data-quality finding is an Issue (`0-190`).** The per-record checks the Data
Quality Dashboard and a record's own page run — including
**`dangling_contract_recipient`** on Rahmenverträgen (`0-30`) and Einsatzverträgen (`0-31`)
— are a separate surface with no MCP tool behind them. `query-model` on `0-190` will not
return them however you filter, and their absence is not a clean tenant. When the operator
asks about one, or when a contract behaves as if it has no recipient, send them to
`dashboard_url` (or the contract's page) rather than reporting nothing found. What that
particular finding means, and the one write that clears it, is in
`→ manage-contract-lifecycle`: a recipient Contact was deleted, the pivot row stayed, and
every reader now skips them — so the contract can neither be sent nor signed, and an unsigned
AÜV names a different signer. These are pre-2026-08 leftovers; the deletion that caused them
is refused today (see step 5). **When the deleted recipient has a living twin** — same person,
same email, still in the tenant — the resolution is to **merge** the two contacts, not to
attach some unrelated substitute: the merge pulls the stale recipient row onto the survivor and
clears the finding while keeping the contract pointed at the right person
(`→ merge-duplicate-companies`).

**Incomplete-employee issues deliberately exclude document gaps.** The
incomplete-employee-data issue covers missing *blocking* required fields only
(name, contact data, home location, salary, employment period, …). Document
gaps (Personalfragebogen, Arbeitsvertrag, Merkblatt §11 AÜG, …) are mandatory
but non-blocking: they never raise or resolve this issue, and issue volume does
not move when documents are filed. They are reported separately as
`missing_non_blocking` by `get-profile` `resource: "completeness"`
(`→ onboard-new-employee`) and as red cells in the Employee coverage matrix.

> **Missing-document triage lost five identifiers (2026-08).** `id_document`,
> `social_security_card`, `tax_id`, `bank_details` and `health_insurance_proof`
> were removed from the product: each only proved a value held structurally
> elsewhere (`social_security_number` / `tax_id` on the Employee, the IBAN on the
> BankAccount) or owned by payroll, and all five were always-mandatory — which
> alone produced ~1000 permanently-open "document missing" rows in a single
> tenant. Those rows are gone; a sharp drop in missing-document volume is that
> cleanup, not a triage win. Never quote one of the five as an example gap, and
> never propose refiling one — `manage-employee-document` rejects the codes with
> `Unknown document type: '<code>'`. Read the live set with
> `manage-employee-document` `action: "list-types"` rather than naming codes from
> memory; tenants also define their own.

Per group: display issue type, affected model (`issueable_title` + ID), severity,
and `remediation_kind`.

### 3. Read the fix for each issue

Call `data-quality-review-prompt` for a systematic walkthrough, or work issue by
issue: `get-model` on `model_type: "0-190"` for the issue's `id` returns the full
`remediation` payload — the exact generic call that fixes it, with field shapes
and an example payload. Read the payload's `kind` and act accordingly:

- **`update_record`** → `manage-model` `action: "update"` on the issueable
  (`issueable_type_id` / `issueable_id` from the detail read), `data` shaped per
  the payload's `fields`.
  **Exception — Unresolvable Federal State (Address, `0-446`, severity high):** fix it with
  `manage-address` `action: "correct"` on the **owner** (`model_type` + `model_id` from the
  Address's `addressable_type`/`addressable_id`, plus its `purpose`) — a typo fix belongs on
  the current row, not in the address history, so never reach for `action: "set"` here.
  Prefer correcting **`zip`**: the Bundesland is derived from the postal code, and the zip also
  drives geocoding and matching, so fixing it repairs more than this one issue. Set
  `subdivision_code` directly only when the address genuinely has no usable postal code, or
  to override a wrong derivation — it is stored as **ISO 3166-2** (`"DE-NW"`), unlike the
  bare code (`"NW"`) other parts of the product store, but you may **write the name**
  (`"Nordrhein-Westfalen"`) and it is resolved to the ISO form for you.
  Treat these as urgent even though the record
  looks fine in the UI: public holidays — and therefore Feiertagszuschläge — follow the
  Bundesland of the **Einsatzort** (§ 9 ArbZG, § 2 EFZG), so every surcharge for an Einsatz
  at that address is uncertain. The billing run still calculates, but **invoice generation is
  refused for the entire run** — naming the affected Einsatzbetriebe — until the address is
  corrected, so one bad site holds up every invoice in that run. Only German addresses raise
  it; a foreign address (any
  `country_code` other than `"DE"`) has no Bundesland by definition and is never flagged, and
  only the **current** row is checked — closed historical rows are not.
  **The same defect can also show up on a legacy Location row (`0-95`, "Unresolvable Federal
  State" on the Location).** Those are not fixable over MCP any more — `manage-location` is
  retired and `0-95` is off the generic tools — so the honest handling is to fix the *owned
  Address* (which is what every reader now uses) and tell the operator the legacy row needs the
  web app, rather than reporting a failed tool call.
- **`create_related`** → `manage-model` `action: "create"` of the target
  `model_type`, `data` = `prefill` merged with the values gathered for `fields`;
  if `link_field` is set, follow up with `manage-model update` on the issueable.
  **Exception — Address targets (`0-446`):** the missing-address remediations (Missing
  Employee Home Address, Missing Company Headquarter Address, Missing Company Billing
  Address, ClientSite Missing Address) all name Address as the target and say so in their
  `note` — use `manage-address` `action: "set"` instead of `manage-model`, so the address is
  attached to the right owner with the right purpose. Map the prefill onto the tool's own
  parameters: prefill `addressable_type` → the owner's **`model_type`** (Contact → `"0-105"`,
  Company → `"0-3"`, ClientSite → `"0-341"`), `addressable_id` → **`model_id`**; pass
  `purpose` through verbatim and add the address fields from `fields`. `valid_from` is
  optional and defaults to today — set it explicitly only when the operator names a real
  move-in date.
  **Ask for the PLZ.** The write is *not* rejected without one any more, but a German address
  whose Bundesland cannot be resolved immediately raises the high-severity **Unresolvable
  Federal State** issue above — so gathering the postcode up front closes one issue instead of
  trading it for another. For an Austrian or Swiss address set `country_code` (`"AT"` / `"CH"`,
  it defaults to `"DE"` when omitted) **and** `subdivision_code` explicitly; there is no
  postal-code mapping there. Name the Bundesland/Kanton in words (`"Wien"`, `"Genf"`) rather
  than guessing a code — the name resolves and is stored as ISO.
  **A person's address always hangs off their Contact.** `model_type: "0-2"` (Employee) is
  rejected outright, with a pointer to the employee's `contact_id`; the Employee remediation
  already prefills the Contact as the owner for exactly this reason. Contact purposes are
  `home`, `second_residence`, `postal`, `work`; company-side purposes (`headquarter`,
  `postal`, `billing`) stay on `0-3`, the Einsatzbetrieb's on `0-341` (`site`). Only Contact
  `home`, Company `headquarter` and ClientSite / CompanyJobPosting `site` are geocoded — every
  other purpose is marked ineligible on purpose and never raises a geocode issue.
  **Creating a person warns about look-alikes.** A `manage-model` `create` of a Contact
  (`0-105`), Employee (`0-2`) or Candidate (`0-81`) can come back with a
  `⚠️ **POSSIBLE DUPLICATE**` block listing up to 5 existing records (id · name · email ·
  created date). It is a **warning, never a rejection** — the record *was* created, so do
  not retry the call and do not report it to the operator as a failure. Show the listed
  candidates instead: if one is the same person, merge it away with `manage-duplicates`
  (step 5) rather than leaving both. Two paths produce the block, and they differ: a direct
  Contact create matches on exact email, on phone/mobile digits, or on a full name folded
  across German umlauts ("Göbel" = "Goebel"); an Employee/Candidate create *without*
  `contact_id` warns in two cases — the identity resolver found 2+ Contacts with the same
  name **and** date of birth and refused to pick one for you, or it found no match at all
  and existing Contacts carry the same folded full name. **A missing date of birth no
  longer hides a look-alike:** the name-only check runs regardless, so expect the block on
  a name-only create. Auto-linking still requires a date of birth — a bare name match only
  warns and never links, so the new record is always created. Passing an explicit
  `contact_id` reuses that Contact and never warns, and an `update` never warns at all.
  **`bulk-manage-model` warns too, once per call.** Instead of a block per row it appends a
  single `⚠️ **POSSIBLE DUPLICATES**` summary — "N of M created record(s) look like they
  might already exist" — listing each flagged row by its `[index]` with its candidates
  underneath. Same contract: every row *was* created, nothing was rejected, do not re-run
  the batch. Work the flagged indexes one by one against step 5; unflagged rows need no
  follow-up.
- **`run_action`** → `manage-record-action` `operation: "execute"`, the payload's
  `action` name, **on the issueable** (e.g. `set-primary-staffing-role` on an Employee) —
  not on the Issue.
  **Exception — Missing Geocodes on an Address (`0-446`).** Its remediation names a `geocode`
  action, but no such action is bound to Address (alluvo#4903) — executing it fails. The
  address re-geocodes by itself whenever one of `street_name`, `street_number`, `zip`, `city`
  or `country_code` actually changes, so the working handling is: if a field is genuinely
  wrong or missing, fix it with `manage-address` `action: "correct"` and the geocode
  re-dispatches on its own; if the address is already right and Google simply returned
  nothing, say so and dismiss the issue rather than reporting a failed tool call. A no-op
  `correct` that changes nothing does **not** retrigger anything.
- **`manual`** → explain the payload's `instructions` (and `url` if present) to
  the operator. After they confirm the fix was made outside the system, resolve
  it via `manage-record-action` `operation: "execute"`, `action: "resolve-issue"`
  on the Issue — the only kind you resolve by hand, since there's no record write
  for the auto-resolve sweep to detect.
- **`informational`** → nothing to fix. Dismiss via `manage-record-action`
  `action: "dismiss-issue"` (requires a `resolution_note`) if it doesn't need
  tracking, or leave it open.
- **`auto_fix`** (payload: `rule`, `fields`, `note`) → **do not fix yourself.**
  The deterministic AutoFix engine applies the named rule once it is enabled on
  the Data Quality Dashboard's Formatting tab. Explain the pending fix to the
  operator and point them at the dashboard (`dashboard_url` from the overview).
- **`agent_fix`** (payload: `agent`, `summary`) → **do not fix yourself.** The
  automation pipeline proposes an EnrichmentSuggestion the operator accepts or
  rejects on the dashboard's Enrichment tab. Only review or explain a pending
  suggestion if the operator explicitly asks.

**Do not call `resolve-issue` after an `update_record` / `create_related` /
`run_action` fix** — the system re-checks on save and auto-resolves the issue
the moment the underlying problem is gone. Calling it anyway is redundant, not
harmful, but skip it.

`owner_id` on a MissingOwner-type issue is the **internal responsible user**
(Disponent/BDR), never the employee or contact the record is about — don't
confuse the two when filling that field.

### 3b. Ask who set a suspicious value (`get-field-history`)

When an issue turns on whether a field was a real decision or an import artifact
— a wrong `status`, an implausible `owner_id`, a value that contradicts the rest
of the record — read its audit trail before deciding. Call `get-field-history`
with `model_type` + `record_id` of the issueable, plus `field` to scope to one
attribute (omit `field` to see every attribute per audit event) and optionally
`limit` (1–50, default 20 events, newest first).

`get-timeline` cannot answer this: it returns only logged activities (calls,
notes, emails, meetings, tasks, resource actions) and **never** a plain attribute
change made through an edit form, a board drag, a bulk edit, or an import.

**"No audit history found" on an Employee (`0-2`) / Candidate (`0-81`) is not the
end of the trail.** Identity and profile fields (`bio`, `first_name`, …) are held
on the linked **Contact** (`0-105`), the identity root — the role record only
points at them, so asking it for such a field comes back empty even though the
value is plainly visible in its payload. When the Contact actually holds history
for that field, the empty answer now names it: it gives the `model_type` and
`record_id` to query instead. Follow that pointer and call the tool again rather
than reporting "nobody changed this".

Each event is attributed as exactly one of:

- **a named user** — a deliberate, attributable edit.
- **a machine source** (import, mcp, api, agent, …), labelled `(system)` — an
  automated write, correct by construction only if the source was.
- **`⚠️ UNATTRIBUTED`** — no user and no recognised machine source. Treat this as
  evidence of a legacy or unverified bulk write, **not** as proof that anyone
  reviewed the value. This is the case worth flagging to the operator when
  deciding whether to overwrite.

Read-only, and gated by the same `view` permission as `get-model`. It cannot
correct or annotate a field — fix the value through the issue's own remediation
path above. No events returned is not an error: either nothing changed, or the
model isn't audited.

### 3c. Rollenkatalog: roles with no Gruppe, Level or Fachweiterbildung

**No detector flags these**, so they never appear in step 2 — check for them explicitly when
the operator asks for a data-quality pass. A `StaffingRole` (`0-100`) carries **three**
hierarchy fields, and `#NachUntenGehtImmer` substitution reads all three:

| Field | Meaning |
|---|---|
| `staffing_role_group_id` | the Berufsfeld (a `StaffingRoleGroup`, `0-345`). Level substitution happens **only inside one group**. |
| `level` | integer ordinal from 1 up, higher = more qualified. |
| `specialty` | the Fachweiterbildung the role carries — optional, independent of Gruppe/Level. |

An unclassified role does not merely blur its match lists — it **loses candidates**. An
employee whose role has no `level` scores **0.0** against a demand whose level *is* known
(unknown is never treated as possibly-qualified); only the reverse, an unclassified *demand*,
falls back to 0.6. So this pass changes who gets shortlisted, not just how confidently.

Find the gaps with `search-model` on `0-100`,
`fields: ["id","label","level","specialty","group.name"]` — all three hierarchy columns are
`hiddenByDefault`, so request them explicitly:

```json
{"filter_groups": [{"conditions": [{"field": "level", "operator": "is_null"}]}]}
```

Same shape with `staffing_role_group_id` for roles with no Gruppe, and with `specialty` for
roles with no Fachweiterbildung tag:

```json
{"filter_groups": [{"conditions": [{"field": "staffing_role_group_id", "operator": "is_null"}]}]}
```

`staffing_role_group_id` and `level` filter as **numbers**, not as relationships: `eq`, `neq`,
`gt`, `gte`, `lt`, `lte`, `between`, `is_null`, `is_not_null`. There is no `in` — one Gruppe is
`eq <id>`, several Gruppen means one query per group. `specialty` is an **enum** and takes the
opposite set: `in`, `not_in`, `is_null`, `is_not_null` — there is no `eq`, so a single
Fachweiterbildung is `{"field": "specialty", "operator": "in", "value": ["psychiatrie"]}`. An
operator the field does not carry is **not applied**: it comes back in the response's
`skipped_conditions` and the result set is quietly wider than asked for, so read that array
before trusting a count.

Allowed `specialty` values (exactly these, lowercase): `intensiv`, `anaesthesie`,
`intensiv_anaesthesie`, `imc`, `op`, `notfall`, `psychiatrie`, `onkologie`, `palliativ`,
`paediatrie`, `beatmung`. Which one covers which other is fixed in code (e.g.
`intensiv_anaesthesie` also covers `intensiv`, `anaesthesie` and `imc`; `intensiv` covers
`imc`) — not something you configure here.

The existing Gruppen are `search-model` on `0-345`, which is readable **and** writable over MCP.

Before writing, read the target group's current ladder (`0-100`, filter
`staffing_role_group_id eq <id>`, sorted by `level`) — you are slotting a role into an existing
order, not onto a blank sheet. Then `manage-model` `action: "update"` on `0-100` for one role,
or `bulk-manage-model` (max 50 operations) for a batch, `confirmed: false` first as always:

```json
{"model_type": "0-100", "confirmed": false, "operations": [
  {"action": "update", "id": 132, "data": {"staffing_role_group_id": 1, "level": 1}},
  {"action": "update", "id": 134, "data": {"staffing_role_group_id": 1, "level": 6, "specialty": "psychiatrie"}}
]}
```

- **A `level` without a `staffing_role_group_id` in the same operation is rejected with a
  422** naming both fields — the write path enforces it now. Always send the pair, and
  **re-send `staffing_role_group_id` even when the role already has one**: validation looks at
  your payload, not at the stored row, so `{"level": 4}` alone fails on an already-grouped role.
  The reverse is deliberately fine — a Gruppe **without** a Level is the honest "not yet
  classified" state, not an error.
- **`specialty` is independent.** Set or clear it (`null`) on its own; it is not subject to the
  group/level guard.
- **Check the preview's `IGNORED FIELDS` warning.** A field listed there is not written,
  however successful the response reads.
- A missing Gruppe is a `manage-model` create on `0-345` (`name` and `code` required, optional
  `sector_id`, `sort_order`); use the returned `id`.
- **Read the roles back** with `search-model` afterwards — a success message is not evidence
  the value landed.

Limits: **don't guess the fachliche Rangfolge.** Whether an unfamiliar qualification sits above
or below another is a fachliche decision — leave the role unclassified and ask. Unclassified is
visibly imprecise (and, per the 0.0 case above, visibly costly); a wrong `level` is silently
wrong, which is worse. **Don't guess a
`specialty` either** — set it only where the role's own label names the Fachweiterbildung
unambiguously (`Pflegefachkraft mit Fachweiterbildung Notfallpflege` → `notfall`); do not infer
one from a description. Note that `specialty` is not a rank: unlike `level` it expresses a *kind*
of qualification, so it never orders two roles.

> **`specialty` now moves Personalbedarf shortlists, so a wrong one is expensive.** A
> `StaffingDemand` (`0-415`) passes its role's Fachweiterbildung into matching: a candidate of the
> same Gruppe and a sufficient Level but a *different* specialty scores **0.4** on the role
> feature instead of counting as an exact hit, and a covering specialty bridges across Gruppen at
> 0.5. Combined with the shortlist's minimum score, mis-tagging a role can drop a genuinely
> suitable person out of every proposal. A **missing** specialty is the safe state — it imposes
> no constraint — which is exactly why guessing one is worse than leaving it null here.

Moving an **already-classified** role into
another Gruppe instantly changes who matches whom for every employee holding it — confirm with
the operator before doing it. Two near-identical labels (`Pflegefachkraft` and
`Pflegefachkraft 1`) are a Dublette, not a hierarchy gap: report them rather than classifying
both. The MCP prompt `manage-staffing-role-hierarchy-prompt` (optional `group` /
`staffing_role_id` arguments) walks the whole procedure with all six score thresholds and the
Fachweiterbildung axis.

> **Who holds a role: `get-model` on a `0-100` lists **Contacts**, not Employees.** The
> section is headed `Contacts` and `_relationship_counts` reports `contacts` — the
> qualification belongs to the person, so one row covers them as Employee *and* as Candidate.
> Count that list as "people qualified for this role", not as "employees"; a Kandidat with no
> Employee record is in it, and a person holding two Employee records is in it once.
>
> Consequences for this pass:
> - **"Mitarbeiter ohne primäre Rolle"** (the *Missing Primary Staffing Role* issue) is still
>   raised on the Employee (`0-2`) and still fixed with the `set-primary-staffing-role`
>   action on the Employee — but it writes the shared, Contact-rooted row, so it settles the
>   primary role for every record of that person at once. **One primary per person**, not per
>   employment: a second Employee record of the same human cannot carry a different primary.
> - Attaching a role goes through `manage-association` with `source_type: "0-105"` (Contact)
>   or `"0-2"` (Employee) — both write the same row. Candidate (`0-81`) is **not** an accepted
>   source; use the linked Contact. Recipe: `→ onboard-new-employee` step 2f.
> - An employee whose roles look empty is worth checking on the **Contact** before you file it
>   as missing data — and a role wrongly attached is removed once, from either side, not once
>   per record.

### 3d. Rahmenverträge: role rows and safety agreements

**No detector flags these either** — check them when the operator asks for a contract-side
pass. All three model types below are **read-only** over MCP: the fixes go through
`manage-framework-contract` or the contract wizard, never `manage-model`. Report the gaps,
then hand them to `manage-contract-lifecycle`.

| Check | Query |
|---|---|
| Role rows with no Arbeitsschutzvereinbarung — the gap that blocks `send_for_signoff` | `search-model` on `0-344` (FrameworkContractStaffingRole), `client_site_safety_agreement_id is_null` + `is_current` true |
| Rahmenverträge with no Einsatzbetrieb or no safety agreement | `search-model` on `0-30`, `client_site_id is_null` / `client_site_safety_agreement_id is_null` |
| Safety agreements the client never accepted | `search-model` on `0-342`, `accepted_at is_null`, `is_template` false |
| Agreements not cloned from a template (hand-built, so drifting from the tenant standard) | `search-model` on `0-342`, `cloned_from_safety_agreement_id is_null`, `is_template` false |

```json
{"model_type": "0-344",
 "fields": ["id","role_label","framework_contract_id","client_site_safety_agreement_id","is_current"],
 "filter_groups": [{"conditions": [
   {"field": "client_site_safety_agreement_id", "operator": "is_null"},
   {"field": "is_current", "operator": "eq", "value": true}
 ]}]}
```

- **Request the columns explicitly.** `client_site_safety_agreement_id` (on `0-344` and
  `0-30`), `framework_agreement_group_id` (`0-30`), and `cloned_from_safety_agreement_id` /
  `accepted_at` / `accepted_by_name` (`0-342`) are all `hiddenByDefault` — omit them from
  `fields` and they come back missing, not empty.
- These FKs are **relationship** filters: `in`, `not_in`, `is_null`, `is_not_null` (a bare
  `eq` is coerced to `in`). As in 3c, read `skipped_conditions` before trusting a count.
- **Never judge template identity by `label`.** Two houses routinely carry identically
  labelled safety agreements that are unrelated records; `cloned_from_safety_agreement_id` is
  the only sound answer to "are these the same agreement?".

**Kunde ohne Firmensitz — a contract defect, not just a thin company record.** A customer
company carrying no address at all (or only a `billing` one) makes every
AÜV-family document name it in the Vertragskopf ("Zwischen … und …") **without an address** —
the Rechnungsadresse is deliberately not used as a stand-in, and the Company's own
`headquarter` Address is what the preamble looks for first (then `postal`, then any other
current non-`billing` Address). The detector does not flag this;
`manage-framework-contract` / `manage-assignment-contract` `action: "completeness"` does, as
the **`client_party_address`** check. Two remediations, both over MCP: fix it **on the company**
— `manage-address` `action: "set"`, `model_type: "0-3"`, `purpose: "headquarter"` with the
address fields, which covers every contract of that company — or fix
it **on a single contract** by setting `client_party_address_override` via
`manage-framework-contract` / `manage-assignment-contract` `action: "update"` (DRAFT only). That
override is a free-text snapshot object (`recipient_name`, `care_of`, `street_name`,
`street_number`, `address_supplement`, `zip`, `city`, `subdivision_code`, `country_code`), not a
record reference. An explicit contract-level override wins over the
company address, so prefer the company fix when the company record is simply thin. Setting a
billing address does **not** help; `billing_location_id` is a retired parameter and is rejected
with a "did you mean `billing_account_id`" steer.
Report it as a gap worth closing before the contract is sent — but it blocks no stage
transition, so never present it as "this contract cannot be sent" (`→ manage-contract-lifecycle`).

**Missing Company Site Location — the one address-family finding that is NOT a
`manage-address` call.** An **active** company (`stage = Active`) with no Einsatzbetrieb
raises *Missing Company Site Location* (`App\Issues\DataQuality\Company\MissingSiteLocation`,
severity **high**, **not dismissible**). It looks like its siblings — Missing Company
Headquarter Address, Missing Company Billing Address — but its `create_related` target is
**ClientSite (`0-341`)**, not Address, because a Company cannot own a site address at all.
Two writes, in this order:

1. `manage-model` `action: "create"`, `model_type: "0-341"`, `data` = the prefill's
   `company_id` plus the `name` the `fields` block asks for (confirm the site's name with the
   operator — never invent one from the company name).
2. `manage-address` `action: "set"`, `model_type: "0-341"`, `model_id` = the **new**
   `client_site_id`, `purpose: "site"` plus the address fields.

- **Do not try to shortcut step 2 onto the company.** `manage-address` on `0-3` with
  `purpose: "site"` is rejected — *"Purpose 'site' is not allowed for Company. Allowed:
  headquarter, postal, billing"*. There is no company-owned Einsatzort any more; the
  Einsatzort is the ClientSite's own address, which is also what `manage-contract-lifecycle`
  and the Feiertags-/Bundesland resolution read.
- **Step 1 alone does not clear the issue.** The detector clears only once one of the
  company's ClientSites carries a **current** `site` address, so a ClientSite created without
  step 2 leaves the finding open — do both writes in the same pass, and re-read the issue
  before reporting it fixed.
- Because it cannot be dismissed, "wontfix" is not an option here: either close it or hand it
  over with the missing site name as the open question.

### 3e. Contact: **Possible Duplicate Contact** — the retroactive dedup finding

A Contact can carry an issue titled **"Possible Duplicate Contact"** (DE: *Kontakt: Mögliche
Dublette*), identifier `App\Issues\DataQuality\Contact\PossibleDuplicateContact`, in
`category: "data_quality"` at `severity: "medium"` with `remediation_kind: "manual"`. It also
counts toward the Contact's `open_issues_count` and shows up in `get-issues-overview`.

**It can appear without anyone editing the record in a way the operator would recognise.**
Two triggers raise it:

- **On a backfill.** When one of `email`, `phone`, `mobile`, `first_name`, `last_name` flips
  from **empty to set** on an already-saved Contact — an enrichment agent filling in a
  signature address, an operator edit, an MCP write, a CRM sync — the duplicate check re-runs
  immediately and matches on exact email, on phone/mobile digits, or on a full name folded
  across German umlauts ("Göbel" = "Goebel").
- **Nightly.** `alluvo:issues:check-all` re-checks every Contact, so standing duplicates
  surface even when nobody wrote to either record.

Read it as **advisory**: the write that triggered it always succeeded — the finding never
blocks or rolls anything back, exactly like the `⚠️ POSSIBLE DUPLICATE` block on a create
(step 3). Do not report it to the operator as a failed edit or re-run the write.

Facts worth knowing before you triage one:

- **Only the record that was written to carries the issue.** The counterpart(s) are named in
  the issue's `description` (up to 5) — read them from there rather than expecting a second
  issue on the other side.
- **A corrected value does not raise it.** Only empty→set counts; changing an existing email
  to a different one is treated as a typo fix, even when the new value collides. Those pairs
  are caught by the nightly sweep instead, not the instant the edit lands.
- **Two contacts can become duplicates days after they were created.** The known case: an
  anonymous inbound call created a phone-only Contact, a chat lead created a name+email
  Contact minutes later — no shared identity key at all, so no create-time check could have
  found them; they only became findable once an enrichment write filled in the missing field.
  A late finding is the detector working, not a create-time check that failed.
- **The fix is a merge, not a field edit.** Hand it to `manage-duplicates`
  `preview-merge` → `merge` (`→ merge-duplicate-companies`, which covers Contact).
- **Resolve it explicitly afterwards.** Contact does not re-check its issues on every save, so
  unlike an `update_record` issue this one does not reliably clear itself the moment the merge
  goes through — resolve it by hand per the `manual` path in step 3, or let the nightly sweep
  close it.
- **Dismissal sticks.** If the two really are different people who share a name, dismiss with
  `manage-record-action` `action: "dismiss-issue"` plus a `resolution_note`. The definition
  does not re-create a dismissed or resolved finding for that Contact, so the operator is not
  asked the same question every night.

**Which record survives is the operator's judgment, and "richer-looking" is the wrong
tiebreaker.** Prefer the side with more relationships, an active workflow (open tickets, a
running task, logged calls) and operator-curated fields over the one that merely has more
columns filled. In the production case behind this check, the correct survivor was the
phone-only record — it held the calls, the tickets, an open task and a human-typed
availability profile, while the fuller-looking chat record held a name and an email a form
had captured. Present both records (step 2's `get-field-history` answers who wrote which
value) and let the operator pick `keep_id`.

### 3f. Assignment: **Uncovered shifts during absence** — a `staffing` finding, not a data defect

`category: "staffing"` is a category of its own alongside `data_quality`, `compliance`,
`contract`, `billing` and `formatting`. Its only member today is
`App\Issues\Staffing\Assignment\UncoveredShiftsDuringAbsence` on an Assignment (`0-401`) —
`severity: "high"`, `remediation_kind: "manual"`. Nothing is wrong with the record: the assigned
employee has an approved Krankmeldung or Urlaub and Schichten inside that window still have nobody
to work them.

- **Route it, don't triage it.** This is a Disposition job with a deadline, not a hygiene item —
  hand it straight to the Umbesetzung (`reassign_shifts` on that Assignment,
  `→ build-dienstplan` step 6c), or, only when no replacement can be found, to cancelling the
  Schichten (`→ record-absence`, step 9). Never propose "fix the record" for one.
- **One issue per Einsatz, not per Schicht** — a two-week Krankmeldung hitting ten Schichten raises
  a single finding, because the remediation is one assignment-scoped decision. The `description`
  carries the count.
- **It closes itself — but on the nightly sweep, not on the spot.** Once the last uncovered Schicht
  is reassigned or cancelled the definition goes false, and the issue closes the next time the
  record is re-checked. No shift write triggers that re-check, so in practice it is the nightly
  data-quality sweep (06:00). Do not resolve it by hand as bookkeeping, and do not read one that is
  still open an hour after a completed Umbesetzung as a failure — verify against the Einsatz's
  Schichten. It is dismissible where the operator deliberately accepts the gap.
- **This is also the queryable surface the Schicht itself does not offer.** Shift (`0-111`) stays
  off the MCP allowlist, so `query-model` on Issue (`0-190`) filtered to
  `category: "staffing"`, `status: "open"` is the way to answer "wo fehlt gerade Besetzung?" —
  especially after a bulk absence approval, whose response never lists the affected Schichten
  (`→ record-absence`).

### 3g. Profile cleanup: hide an entry instead of deleting it

**No detector flags these either** — this is the pass an operator asks for by name
("das Profil aufräumen", a station an import duplicated, an outdated entry a client
should not see). It used to be a dead end: `delete-model` refuses ContactWorkExperience
(`0-184`) — the model has no soft-delete and the tool declines hard deletes on purpose —
and there was no visibility field, so cleanup happened entry by entry in the app. It is a
`manage-model` write now.

`manage-model` `action: "update"`, `model_type: "0-184"`, `data: {profile_visibility: …}`,
`confirmed: false` first as always:

| Value | Effect |
|---|---|
| `auto` | the default — the tenant's rolling window decides on the published profile |
| `always` | keep this station on the published profile even when the window would drop it |
| `never` | hide it on the published profile, the client-portal profile **and** the profile PDF |

- **Reach differs between the two mechanisms, deliberately.** `never`/`always` are
  statements about the record and hold on every profile surface. The tenant's rolling
  window (`talent_hub.profile_work_experience_visible_years`) is a presentation choice for
  the **published** profile alone — it never shortens what a client sees in the portal or
  in the PDF. The window defaults to `null` (show everything); a station that has not ended
  is never dropped by it, however long ago it started.
- **The window is not adjustable from here.** `manage-settings`' `talent_hub` group neither
  reports nor accepts `profile_work_experience_visible_years` (tracked in alluvo#3671), so
  do not offer to change it — per-entry `profile_visibility` is the operator-side lever.
- **Nothing is deleted, and nothing is repaired.** The row keeps its dates, `auto`/`always`
  brings it straight back, and a hidden station still counts for `work_history_coverage` in
  `get-profile` `resource: "completeness"` (`→ onboard-new-employee`). Say that when the operator asks to
  "remove" a station — and never hide one to make a gap report go green.
- **Only the three values validate.** A plausible-looking `hidden`, `false` or `null` is
  rejected and the stored value is unchanged — do not retry with a synonym.
- **Hiding a duplicate is a workaround, not a merge.** There is no merge for CV rows, so
  both rows stay on the record. Hide the weaker one, and name it in the summary as an
  outstanding cleanup rather than as a resolved duplicate.

**Lizenzen, Ausbildungen und Sprachen: `hidden_on`, per output surface.** Same reflex, a
different field. The entry lists the surfaces it is **not** shown on, so `null` / `[]` is
"visible everywhere" — no existing row changed behaviour when the field appeared.

`manage-model` `action: "update"`, `data: {hidden_on: [...]}`, `confirmed: false` first,
on one of:

| Model type | Entry |
|---|---|
| `0-183` | ContactEducation — Ausbildung / Berufsabschluss |
| `0-185` | ContactLanguage — Sprache |
| `0-186` | ContactLicense — Lizenz / Berufserlaubnis |

and one or both of:

| Value | Suppresses the entry on |
|---|---|
| `profile` | the published profile, the client-portal profile, the profile PDF |
| `contract` | the AÜV and the Einzel-AÜV |

- **Hiding is the answer to a badly parsed or unflattering qualification, not deleting.**
  A CV import that read "Erste-Hilfe-Kurs 2009" as a Lizenz, an Ausbildung that is real but
  says nothing for the Einsatz, a language at a level the person would rather not advertise
  — `hidden_on: ["profile"]` takes it out of what a client sees while the row, its dates and
  its evidence stay on the Personalakte. Reserve `delete-model` for a row that is simply
  **wrong**. Say which of the two you are proposing; "entfernen" reads as delete to an
  operator and this usually isn't that.
- **Two entries an operator cannot hide from the contract, by design.** § 12 AÜG requires the
  agreement to name the qualification the Überlassung rests on, so `hidden_on: ["contract"]`
  is ignored for the person's **primary** Ausbildung (`is_primary`) and for **any Lizenz the
  Einsatzrolle lists as required**. Both keep printing. Never present hiding as a way to keep
  a required Berechtigung out of the AÜV, and don't report the entry as "still showing" —
  that is the guard, not a failed write.
- **`profile` and `contract` are independent.** Hiding on one surface says nothing about the
  other; an entry can sit on the client-facing profile and be out of the contract, or the
  reverse. Set both values when the operator means "nowhere".
- **The flag rides the entry, so it holds for Employee and Candidate alike** — these rows
  live on the Contact (`0-105`), the same rows both records read
  (`→ onboard-new-employee` step 2).
- **`get-profile` shows the record, not the client's view.** It reports every entry
  regardless of `hidden_on` and does not print the flag, so never read its output as "this
  is what the client sees". Read the flag back on the entry itself with `get-model` /
  `query-model` on `0-183` / `0-185` / `0-186` before telling an operator an entry is
  visible.
- **The pivot-borne entries have no MCP write.** Staffing experiences and staffing trainings
  carry the same flag, but it sits on the association row, and neither `manage-model` nor
  `manage-association`'s `pivot` exposes it — those stay an in-app edit. Say so instead of
  attempting a write that silently drops the key.

### 4. Confirm and execute

Every write — the record fix itself, and any `resolve-issue`/`dismiss-issue`/
`reopen-issue` bookkeeping — goes through the standard preview → confirm gate:
`confirmed: false` first to show the operator exactly what will change, then
`confirmed: true` after they approve.

For a batch of same-shaped issues (e.g. all missing-email issues for employees),
use `manage-record-action` `operation: "execute_bulk"` (max 100 records) for
bulk resolve/dismiss with the same note, rather than confirming one at a time.

### 5. Wrap up

Summarize remaining open issues. If issues point to duplicates
(`duplicate_contact`, `duplicate_employee`): **Company (`0-3`) and Contact (`0-105`)
are mergeable over MCP** — `manage-duplicates` (`find` → `preview-merge` → `merge`,
which fills missing columns on the kept record and re-points relationships before
deleting the other) handles both, via the `merge-duplicate-companies` skill, which
covers the Contact case too. `preview-merge` also reports the values that will **not**
survive; if any is a `conflict` (both records hold a differing value and there is nowhere
to keep the second one), the `merge` is refused until the operator has copied what matters
onto the kept record and the call is re-run with `confirm_data_loss: true` — that refusal
is the gate working, not a bug. Not every difference gets there: a Contact's second `phone`
overflows into an empty `mobile`, recency columns keep the newest date, and a merged-away
email/name is absorbed into `alternative_emails` / `alternative_names`.
A `duplicate_employee` is worked through the two Contacts: when both carry a linked
Employee, `preview-merge` returns an Employee merge preflight (columns, relations, unique
collisions, open decisions) and the `merge_employee` record action on the kept Employee does
the mechanical half before the Contact merge is re-run — see that skill, step 3. The
preflight now counts **every** table that points at the duplicate, keyed by table name, and
`merge_employee` refuses the confirmed run without `data.acknowledge_relations: true` as soon
as any of those rows are payroll, working-time or legal ones (timesheets, time entries,
absences, salaries, payslips, documents, bank accounts, tax profiles, shifts, invoices,
reimbursements, …). Put the counts in front of the operator and get their go-ahead before
sending that flag — never set it to get past the refusal. A Contact
pair where both sides carry a linked Candidate works the same way: a Candidate merge
preflight and the `merge_candidate` record action on the kept Candidate (`0-81`); when both
roles block, both preflights come back and both merge actions run first.
Every other model type is rejected by that tool, so send
the operator to the Data Quality Dashboard's Duplicates tab (`dashboard_url` +
`?tab=duplicates`) for those.
**A Contact merge is blocked while the duplicate side is attached to a live contract.** The
merge ends by deleting the duplicate, and that delete is refused while the person is still a
recipient of a Rahmenvertrag or Einsatzvertrag that is neither deleted nor abandoned
(`lost` / `cancelled`), or the Ansprechpartner of a live Einsatz — the message names each one
(`RV #72`, `AÜV #685`, `Einsatz #2040`). The merge runs in one transaction, so nothing is
half-applied. Move those records onto the kept Contact first, then re-run the merge; the steps
are in `→ merge-duplicate-companies`, step 3a. **Never offer "just delete the duplicate"
instead** — the same guard blocks a bare `delete-model` on a Contact (`0-105`), and a delete
would throw the record's history away rather than folding it into the survivor.
**Expect more contact duplicate groups than before.** `find` and the Duplicates tab share
one engine, and its name-match gate — required by every Contact rule except the name-only
one, so it also gates the email and phone rules — now folds German umlauts and diacritics
(`ö`=`oe`, `ü`=`ue`, `ä`=`ae`, `ß`=`ss`). Two Contacts with the same email whose surname is
spelled "Göbel" on one record and "Goebel" on the other were previously not grouped at all;
they now are. A rising duplicate count after this change is the detector catching up, not a
data regression — work the new groups through step 5 rather than reporting a spike. For pending formatting/enrichment work
(`formatting_pending` / `enrichment_pending` in the overview), point the operator
at the dashboard's Formatting and Enrichment tabs.

## Output

- Issue count before / after triage (by severity)
- List of resolved issues (type · affected model · fix applied)
- Rollenkatalog: roles still without Gruppe/Level (id · label) and roles still without a
  `specialty` where the label names one, plus anything classified this pass
- Work-history stations hidden this pass (Contact · station · reason), flagged as hidden
  rather than removed — and any duplicate pair still standing behind one
- Remaining issues with recommendation (auto-fixable / manual / web app)
- Pointer to `get-issues-overview` with `action: "open-dashboard"` for interactive
  follow-up (opens the Data Quality Dashboard app; the standalone
  `open-data-quality-dashboard` tool has been **removed** from the MCP server — this is
  the only way to open it)

## Related skills
- `→ merge-duplicate-companies` — when issues point to duplicate companies **or contacts**
  (`manage-duplicates` merges both), or after a create surfaced a POSSIBLE DUPLICATE block.
- `→ enrich-contacts-from-activities` — fill sparse Contact records flagged as incomplete.
- `→ onboard-new-employee` — completeness gate for newly imported employees.
- `→ manage-contract-lifecycle` — close the contract-side gaps from 3d (role prices, safety
  agreements, Einsatzbetrieb); none of them is writable from here.
- `→ approve-stundenfreigabe` — the Abweichungsgrund catalogue (`ShiftDeviationReason`) is a second
  tenant-maintained catalogue alongside the Rollenkatalog above: rows can be added, relabelled and
  deactivated over MCP, but a system row is never deletable and a `code` is fixed once created.
