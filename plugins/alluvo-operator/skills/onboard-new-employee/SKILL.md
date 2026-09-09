---
name: onboard-new-employee
description: Onboard a newly added employee — check profile completeness, send the digitaler Personalfragebogen (guest link) and apply the returned Stammdaten, capture Bankverbindung and Notfallkontakt, surface nearby placement opportunities, and optionally invite the employee to the self-service app. Use when the operator says "neuen Mitarbeiter anlegen", "Mitarbeiter onboarden", "onboard new employee", "Profil vervollständigen", "Personalfragebogen schicken", "digitalen Personalfragebogen senden", "Stammdaten anfordern", "Stammdaten übernehmen", "Fragebogen ausgefüllt", "Personalfragebogen erfassen", "Bankverbindung anlegen", "IBAN hinterlegen", "Notfallkontakt erfassen", "No-Go hinterlegen", "Schwerpunkt ausschließen", "macht keine Palliativpflege", "Einladung versenden", "Einladung erneut senden", "Mitarbeiter kann sich nicht anmelden", "bekommt keinen Code", "Passwort vergessen", "Passwort zurücksetzen", "check completeness", "Go-Live-Datum setzen", "go-live date", "bAV eintragen", "Versorgungsträger hinterlegen", "betriebliche Altersvorsorge", "Ziffer 9.11 fehlt im Arbeitsvertrag", "Mitarbeiter anschreiben", "Nachricht an den Mitarbeiter in der App", "Rückfrage an den Mitarbeiter", "message the employee in the app", or after a new employee record has been created.
---

# Onboard New Employee

## Purpose
Bring a new employee into the system end to end: create the record when it does
not exist yet, check profile completeness, capture missing required data,
identify nearby placement opportunities, and optionally invite the employee to
the self-service app (or resend their login link if they already have one).

> Mostly read-only. Creating the record (Step 0), filling missing fields,
> prospecting tasks (Step 4) and the
> invitation (Step 5) are two-stage: preview (`confirmed: false`) → operator approval →
> `confirmed: true`. The go-live date (Step 6) is the exception — `manage-record-settings`
> has **no** `confirmed` parameter, so `set` writes immediately; state the employee and the
> date and get an explicit yes before you call it.

## Prerequisites
Uses only the connected alluvo MCP tools (`mcp__alluvo__*`). No tokens, no shell.
Everything runs inside the operator's tenant.

## Steps

### 0. Create the employee record — only when it does not exist yet
Most runs start from a record somebody already created; skip straight to step 1
then. When the operator says "neuen Mitarbeiter anlegen" and there is no record,
create it here first.

1. **Resolve every name-typed reference to an id** with `search-model` before the
   create: Owner `0-1` (User), Manager `0-2`, Sector `0-70`, Position `0-71`,
   Branch `0-73`. Ambiguous hit or no hit → ask the operator; never guess.
   Omitting `owner_id` leaves the authenticated user as owner.
   **A Niederlassung that does not exist yet can be created from here** — `manage-model`
   `action: "create"`, `model_type: "0-73"` with `name` (required) and optionally
   `description`, `email`, `phone`, `owner_id`. Do that only when the operator
   confirms the branch is genuinely missing — a typo'd search is the far more common cause of
   no hit, and a duplicate Niederlassung splits the whole tenant's reporting. Its street address
   **is** writable now — pass a nested `address` object (`street_name`, `street_number`, `zip`,
   `city`, …) to the same `manage-model` call, or set it afterwards with `manage-address`
   `action: "set"`, `model_type: "0-73"`, `purpose: "branch"`. The Employee create does not need
   it either way.
2. **Create the Employee, never the Contact.** `manage-model` `action: "create"`,
   `model_type: "0-2"` with the identity fields (`first_name`, `last_name`,
   `email`, `phone`, `mobile`, `date_of_birth`, `gender`, …) alongside the
   resolved ids. Identity belongs to the **Contact** (`0-105`) and the create
   resolves it for you — it matches an existing Contact by email, then by name +
   date of birth, and only mints a new one when neither matches. Creating the
   Contact by hand first and passing `contact_id` is the wrong order and risks a
   split identity.
   Look-alike people come back as a **`⚠️ POSSIBLE DUPLICATE` warning, not a
   rejection** — the record is created either way. Read the named candidates out
   to the operator; if it is genuinely the same person, merge with
   `manage-duplicates` rather than leaving both.
   Preview with `confirmed: false`, then repeat the identical call with
   `confirmed: true` after approval.
3. **Home address** goes on the Contact via `manage-address` — see the
   `home_location` box in step 2; it is not a `manage-model` field.
4. **Activation is derived — never write `is_active`.** A new Employee starts
   inactive and flips to active by itself once an **EmploymentPeriod** (`0-18`)
   exists whose `started_at` is today or earlier and whose `ended_at` is empty or
   in the future. Create that period with `manage-model` `model_type: "0-18"`
   **only once you have the real Eintrittsdatum** — a guessed start date has AÜG
   and pay consequences, so ask for it instead. The period also carries the
   `personnel_number`; the employee's `employee_number` is derived from it.
5. **Arbeitsverhältnis** (`manage-association`, EmploymentRelationship) and the
   current **Salary** (`0-12`) are the two records that later gate the app
   invitation in step 5 — record them with the operator's real values, never with
   placeholders.

Bio, Qualifikationen, Sprachen and Berufserfahrung follow later in this skill
(step 2f and the CV writes under step 2), not here.

### 1. Identify the employee
Ask the operator for the name or ID of the new employee (model `0-2`).

> **A Personalnummer is not the record id.** Operators routinely name the
> `employee_number` ("PNr 1000241") — every tool here wants the record id.
> `employee_number` is searchable, so `search-model` on `0-2` with the number as
> `q` resolves it; take the `id` from the hit and use that from then on. The
> number itself is a per-stint fact stored on the EmploymentPeriod and cached
> onto the Employee, so it can differ between two stints of the same person.

Load the profile via `get-profile` with `resource: "profile"`, `model_type: "0-2"` and the employee's
`model_id` to see master data and position. `get-profile` is the single profile tool
for every person — pass `0-2` (Employee), `0-81` (Candidate) or `0-105` (Contact) —
and `resource` picks what you want out of it: `"profile"` (the CV/staffing profile),
`"url"` (a shareable link, see `→ profilvertrieb`) or `"completeness"` (step 2).
It always returns the shared CV data (education, work experience, languages, licenses,
staffing experiences and trainings, availability preferences, home location) plus the
role-specific section for the `model_type` you passed.

`get-profile` belongs to the **Recruiting** module. If it is absent or answers
`MODULE_LOCKED` for this tenant, do not abort the onboarding: read master data and
qualifications off the Employee with `query-model`, skip the completeness step in step 2,
and tell the operator which module the profile view needs.

### 2. Check completeness
Call `get-profile` with `resource: "completeness"` and `employee_id`.
The `employee_operational` block returns the weighted operational score, the
missing required and optional fields, and — separately — missing **documents**.
Two different axes here; do not conflate them when reporting:

- `required` says whether missing data is acceptable at all (optional gaps are
  amber hints, never blocking).
- `blocks_completeness` says whether a missing mandatory requirement counts
  towards `score` and `is_complete`. Document-backed requirements
  (`onboarding_questionnaire` Personalfragebogen, `employment_contract`
  Arbeitsvertrag, `temp_work_act_info_sheet` Merkblatt §11 AÜG, …) are
  mandatory but **non-blocking**: listed separately under
  `missing_non_blocking`, they do not move the score and do not make the
  employee "incomplete".

> **There is no document requirement for Ausweis, SV-Ausweis, Steuer-ID,
> Bankverbindung or Krankenkassen-Mitgliedsbescheinigung — those five types were
> removed from the product (2026-08).** Each only *proved* a value the system
> already holds structurally, so the scan never belonged in the Personalakte.
> Consequences for onboarding:
>
> - Do not ask the operator to collect or file those scans, and do not list them
>   as open Personalakte to-dos. They no longer appear in `missing_non_blocking`,
>   and completeness scores read higher than before for the same employee — that
>   is the removal, not a data fix.
> - `manage-employee-document` `action: "create"` with `id_document`,
>   `social_security_card`, `tax_id`, `bank_details` or `health_insurance_proof`
>   now fails with `Unknown document type: '<code>'`. Never guess a code — call
>   `action: "list-types"` (see step 2b's sibling flows in `→ clean-inbox`).
> - Capture the **data** instead: IBAN as a `BankAccount` record (step 2b),
>   `social_security_number` and `tax_id` as fields on the Employee (`0-2`) via
>   `manage-model` — confirm both are in the `update` schema with
>   `get-model-schema` before writing.
>
> `onboarding_questionnaire` (Personalfragebogen) is now the only always-mandatory
> Identity-category document — and the digital questionnaire files it for you when
> its submission is applied (step 2a), so send that rather than chasing a scan.
> For an employee whose citizenship is non-EU **or
> still unknown**, `residence_permit` + `work_permit` are additionally mandatory;
> everything else always-mandatory is employer-issued (Arbeitsvertrag, Merkblatt
> §11 AÜG), i.e. yours to hand over, not theirs to hand in. One tenant-wide input
> the Arbeitsvertrag needs before it is handed over is the bAV-Versorgungsträger
> list — see step 2g.

> **"Citizenship unknown" is now fixable over MCP — record the Staatsangehörigkeit.**
> The gate above reads the Contact's `nationality_id` → the country's ISO code → EU
> membership. A missing nationality is the *unknown* case, so it keeps Aufenthaltstitel
> and Arbeitserlaubnis listed as mandatory for a German or other EU citizen who will
> never hand one in. Until now there was no way to resolve a country id in this session
> at all; the **Country** catalogue is readable as model type **`0-90`**:
>
> - Resolve: `search-model` `model_type: "0-90"`, `q: "DE"` — **search by ISO 3166-1 code,
>   not by the German name.** The catalogue stores the English ISO short name and derives
>   the German label only when rendering, so it is not a searchable column: `q: "Deutschland"`
>   returns **0 hits**, `q: "DE"` (or `"DEU"`, or the English `"Germany"`) finds the record.
>   The code is also stable across the renames that make names a moving target
>   (Turkey→Türkiye). Never guess or invent an id.
> - Write on the **Contact** (`0-105`): `manage-model` `action: "update"`,
>   `data: {nationality_id: <id>}` — and `country_of_birth_id` the same way, which the
>   Personalfragebogen asks for as *Geburtsland*. Preview → confirm as always.
> - The catalogue is **read-only reference data**: `manage-model` `create`/`update` on
>   `0-90` is rejected. Never try to add a country.
>
> Setting a nationality that turns out to be non-EU does **not** clear the two
> documents — it confirms they are genuinely required. Record what the person stated;
> never pick an EU country to make the requirement disappear.

Show the result to the operator in a structured format:

- Missing **required data** (`missing` — gate: without these, no placement is
  possible). `home_location` is **required** and on this list when absent:
  without a home address the employee is invisible to geo-matching (step 3,
  bench, Profilvertrieb) — fix it first.
- Missing recommended data (`missing_optional` — profile photo, vehicle, etc.)
- Missing **documents** (`missing_non_blocking`) — present these as Personalakte
  to-dos. Never call the employee "incomplete" because of document gaps alone,
  and never report "complete" without mentioning outstanding documents. A
  document counts as filed only when the record also carries an attached file —
  a filed record without a file still reports as missing.

> A filed document is also the precondition for ever **sending** one:
> `manage-1on1-email` can attach an employee document to a customer email, but
> only an `active`, unexpired system type that carries a file **and** that the
> tenant has released for sending — filing it does not release it, that is a
> tenant setting which is empty by default. See `→ profilvertrieb`.

Every entry in `employee_operational.requirements` also carries a five-state
`status`: `satisfied` / `missing_required` / `missing_optional` / `pending` /
`not_applicable`. **`pending` means correctly future-dated, not missing** — a
new hire whose employment period, salary, or position starts next month is
pending; do not tell the operator to "fix" those, they resolve themselves on
the start date. `not_applicable` (e.g. a work permit for an EU citizen) is
excluded from the score entirely.

> **Report the effective date for a `pending` requirement — never its fix-hint as
> an instruction.** Only three requirements can be pending: `employment_period`,
> `salary`, and `current_position` (the position is derived from the future-dated
> salary). Their `fix_hint` is no longer the missing-case sentence ("Add a valid
> salary record (Entgelt)."); it reads "Recorded — effective from <date>" instead,
> and `meta` carries the raw facts: `meta.effective_at` (ISO `YYYY-MM-DD`, the date
> the row becomes valid) plus `meta.href` to the record itself, and on
> `current_position` a `meta.label` with the future position's name. Name that date
> when reporting the onboarding status ("Entgelt erfasst, wirksam ab 01.08.2026")
> rather than listing the item as an open task. `meta` is `null` for every
> non-pending requirement except `vehicle`, where it holds the Kennzeichen.
>
> Pending items never appear in `missing`, `missing_optional` or
> `missing_non_blocking`, and they do not make the employee incomplete
> (`is_complete` stays `true`) — so a correctly prepared starter whose employment
> period and Entgelt are dated to the Eintritt is not blocked. They do still count
> against `score` until they take effect, so a starter can legitimately read below
> 100 with nothing to fix; say why instead of inventing a gap.

If blocking fields are open, prompt the operator to fill them first via the
web app or `manage-model` (preview → confirm) before proceeding to step 3.

> **`home_location` is the exception — it is not a `manage-model` field.** A person's
> address is identity data on their **Contact** (`0-105`). Add it with `manage-address`
> `action: "set"`, `model_type: "0-105"` + the **Contact's** id (`model_type: "0-2"` is
> rejected outright, with a pointer to the employee's `contact_id`), `purpose: "home"` and the
> address fields; `valid_from` is optional and defaults to today. Contact `home` is one of the
> three geocoded owner+purpose pairs, so step 3's distances work right after the write — no
> separate geocode action.
> **Ask for the PLZ, not just Ort + Land.** The write is *not* rejected without one, but a
> German address whose Bundesland cannot be resolved immediately raises a high-severity
> **Unresolvable Federal State** issue on the address — and the Bundesland decides
> Feiertagszuschläge (§ 9 ArbZG, § 2 EFZG). For a German address a correct five-digit `zip` is
> all you need; leave `subdivision_code` empty and it is derived. For an Austrian or Swiss
> Privatadresse set `country_code` (`"AT"` / `"CH"` — it defaults to `"DE"`) **and**
> `subdivision_code` explicitly; there is no postcode mapping there. `subdivision_code`
> takes the **spelled-out name** as well as the ISO code (`"Wien"` or `"AT-9"`, `"Zürich"`
> or `"CH-ZH"`) and stores the ISO form — so write the Bundesland/Kanton in words rather
> than guessing a code, especially for Austria, whose codes are numeric.
> Full recipe and the tenant-defined-purpose caveat: `→ bench-check`.

The same tool covers **candidates** — pass `contact_id`, `candidate_id`, or
`employee_id` (**exactly one**; the candidate/employee id resolves to its linked
identity Contact). Alongside `employee_operational` it reports the public-profile
bucket (Kontakt-Basics, Sprachen, Ausbildung, Berufserfahrung, Fachbereiche & Technik,
Mobilität, Verfügbarkeit, Foto) and the non-public enrichment bucket. Every missing
item carries an exact fix-hint naming the tool and field; follow the hint verbatim
rather than inferring a `manage-model` call — with the exceptions below.

> **A "complete" section is not necessarily a filled one — read `has_required`.**
> Each entry in `sections[]` carries `complete`, and it means exactly one thing: *no
> **required** item is unfilled*. A section whose items are **all optional** therefore
> reports `complete: true` at 0 of N filled. Two sections are optional-only —
> **Fachbereiche & Technik** (Fachbereiche, Geräte/Medizintechnik, Pflegesoftware) and
> **Foto** — and they are precisely the blocks that make a profile presentable to a
> client. Iterating `sections[]` on `complete` alone ticks both off as done while they
> are empty.
>
> Each section now also carries **`has_required`** (`false` = the section has no required
> items at all). `complete: true` **and** `has_required: false` **and** `filled < total`
> means *nothing is blocking, but the section is still empty* — report it as an open
> recommendation, never as done. The markdown output already distinguishes it: such a
> section renders as `➖ Fachbereiche & Technik — 0/3 (alle optional)` plus the missing
> item names, not a bare ✅. `complete` itself is unchanged — do not read the new field
> as a stricter completeness rule, and do not report those sections as required gaps.

> **Berufserfahrung is a timeline check now, not a presence check.** One
> ContactWorkExperience row no longer satisfies the public bucket. The **required**
> criterion `work_history_coverage` additionally demands that the captured entries cover
> the timeline from the person's working-life start point to today with no unexplained gap
> longer than **6 months**. A profile that reported `is_complete: true` before this landed
> can now report `false` with nothing else changed — say that plainly instead of treating
> it as a regression or a lost record.
>
> Read `public_profile.work_history_coverage`:
> - `start_date` — the resolved start point, taken in this order: earliest education
>   `earned_on` → earliest license `issued_on`/`valid_from` → earliest work-experience
>   `start_date`.
> - `gaps[]` — the uncovered `{from, to}` ranges, only those over the 6-month threshold.
> - `covered_ranges[]` — what is actually on file. Report coverage from this, **not** from
>   the complement of `gaps`: a short uncovered stretch appears in neither list.
> - `start_point_known: false` — no start point could be resolved at all. The criterion
>   then reports `is_filled: true` (**fail-open**, so nobody is blocked by a date they
>   cannot know). Never invent a date to "fix" this state.
>
> When it fails it is mirrored into `missing_required` under the key
> `work_history_coverage`, and that entry carries `gaps` and `start_point_known`. **Its fix
> is a date range, not another row:** create or update the ContactWorkExperience (`0-184`)
> whose `start_date`/`end_date` closes the named gap (leave `end_date` null for an ongoing
> station), then re-read. Ask the person what they did in that period — never file a
> placeholder station to turn the report green. Overlapping entries (parallel
> Zeitarbeit-Einsätze) are merged before gaps are computed, so overlap is not read as two
> gap-bounded stations; an entry without a `start_date` cannot close a gap at all.

> **Einsatzumfang (`monthly_hours`) is a *required* public-profile field (2026-08).** It
> used to be optional. A candidate with no `desired_monthly_hours` now appears in
> `public_profile.missing_required`, reports `is_complete: false` and a lower
> `required_progress` — a profile that read complete before this landed can flip to
> incomplete with nothing else changed. Say that plainly rather than treating it as a lost
> value. The reason it was promoted: matching and Buchung price and staff against the
> monthly volume, so an empty Einsatzumfang silently weakens both.
>
> Fix per the hint — `manage-model` `action: "update"`, `model_type: "0-105"` (Contact),
> `data: {desired_monthly_hours: <number>}` (preview → confirm). **The stored field is a
> number of hours per month, not a label**: write `160`, never `"Vollzeit"`. The
> Personalfragebogen chat offers the person the labels *Vollzeit / Teilzeit 30h /
> Teilzeit 20h / Minijob / Andere* and converts the answer to hours itself; when you write
> the field for an operator, ask for the hours. The rest of the Verfügbarkeit section
> stays as before — `shifts` (Schichtbereitschaft) required, `weekend_availability`,
> `availability_notes` and `earliest_start_date` optional.

> **`earliest_start_date` (Frühestmöglicher Start) is a tracked field.** Optional, in the
> Verfügbarkeit section of the public bucket, and also listed in the non-public Bewerbung
> group. It lives on the **Candidate** (`0-81`), not the Contact: `manage-model`
> `action: "update"`, `model_type: "0-81"`, `data: {earliest_start_date: "YYYY-MM-DD"}`
> (preview → confirm). A person with no Candidate role has nowhere to store it.
> The public bucket's fix-hint for this key currently falls back to
> `manage-model update Contact 0-105: earliest_start_date` — that field does not exist on
> Contact and the call fails. Use the `additional_fields` hint (Candidate `0-81`) instead;
> the wrong fallback is tracked in alluvo#2654.

> **CV buckets (Sprachen, Ausbildung, Berufserfahrung) — the fix-hint's payload is
> wrong; the model type is right.** These hints read
> `manage-model create (source_type: "0-105", source_id: contact_id)`, but
> `manage-model` has no `source_type`/`source_id` parameters at all — it takes
> `model_type`, `action`, `id`, `data`, `confirmed`. Take the model type from the
> hint and put the Contact reference **inside `data`** as `contact_id`:
>
> - Sprachen → `model_type: "0-185"` (ContactLanguage),
>   `data: {contact_id: <Contact id>, language: "<ISO 639-1 code>", proficiency: …}`
> - Ausbildung → `model_type: "0-183"` (ContactEducation), `data: {contact_id: …, …}`
> - Berufserfahrung → `model_type: "0-184"` (ContactWorkExperience), `data: {contact_id: …, …}`
>   — always set `start_date`, plus `end_date` (or leave it null for an ongoing station).
>   A dateless entry satisfies `work_experience` but is skipped by the coverage check above.
>
> Pass the **Contact** id (`0-105`), not the Employee/Candidate id — CV data is rooted
> on the Contact. `get-profile` `resource: "completeness"` returns the linked Contact's id.
>
> `language` is enum-constrained to lowercase ISO 639-1 codes — **not** free text.
> Currently accepted: `de`, `en`, `ar`, `bg`, `da`, `es`, `fi`, `fr`, `hi`, `hr`, `hu`,
> `it`, `ja`, `ku`, `la`, `nl`, `pl`, `pt`, `ro`, `ru`, `so`, `sq`, `sr`, `tl`, `tr`,
> `zh`, plus `sgn` for Gebärdensprache (sign language has no 639-1 code). Send the code,
> never a label like `"Türkisch"`, or the preview returns a validation error. `proficiency` is optional and one of
> `native` / `fluent` / `advanced` / `intermediate` / `basic`; leave it out when the
> person did not state a level rather than guessing one. If unsure a code exists, call
> `get-model-schema` for `0-185` in `create` context and read the enum options.

> **Order and per-entry visibility are writable now — `position` used to be dropped
> silently.** `position` (integer, `min:0`, ascending) sets the CV display order and is
> accepted on all three CV types (`0-183`, `0-184`, `0-185`). Until 2026-08 the field had
> no validation rule, so it was stripped before the write and the call still answered
> "Record Updated Successfully" — an ordering that "did not stick" earlier is that gap, not
> an operator mistake. Re-send it if an old sort order never landed.
>
> `0-184` additionally takes **`profile_visibility`** — `auto` (default) / `always` /
> `never` — the only way to take a duplicate or outdated station off the profile, since
> `delete-model` refuses `0-184` (no soft-delete). `never` hides the station on the
> published profile, the client-portal profile and the profile PDF; `always` keeps it even
> when the tenant's rolling window would drop it. Nothing is deleted either way, and a
> hidden station **still counts** for `work_history_coverage` above — so hiding never
> repairs a gap, and it never creates one. Full recipe: `→ triage-data-quality` step 3g.
>
> **`0-183`, `0-185` and Lizenz (`0-186`) take `hidden_on` — the same idea, per output
> surface.** It is a list of the surfaces the entry is **not** shown on, so `null` / `[]`
> means visible everywhere and every row that existed before this field behaves exactly as
> it did. Two values:
>
> | Value | Suppresses the entry on |
> |---|---|
> | `profile` | the published profile, the client-portal profile, the profile PDF |
> | `contract` | the AÜV and the Einzel-AÜV |
>
> `data: {hidden_on: ["contract"]}` on a `manage-model` `update` (preview → confirm as
> always); `[]` brings it back. When a parsed CV hands you a qualification that is real but
> does not belong in front of a client — or one you are not sure of — **hide it, don't drop
> it**: the row keeps its dates and evidence on the Personalakte either way. Deleting is for
> a row that is simply wrong. Full recipe incl. the two entries an operator cannot hide:
> `→ triage-data-quality` step 3g.

### 2a. Send the digitaler Personalfragebogen — and apply what comes back (preview → confirm)
Two record actions, both through `manage-record-action`: one asks the person for their
master data, one takes the answers over. Prefer this over dictating field by field —
step 2b stays the manual path for a paper form or a single correction. For a single
follow-up question rather than the whole set, step 7 messages the employee in their app.

**Ask — `request-employee-master-data`**, available on Employee (`0-2`), Candidate
(`0-81`) and Contact (`0-105`), whichever record the operator is on:

1. `operation: "list"` with the `record_id`. The action only appears when the person has
   a **linked Candidate profile**; without an email on that candidate it is listed but
   disabled with "Add an email address to the linked candidate before sending the
   master-data questionnaire". The mail always goes to the **Candidate's** address, not
   to one held on the Employee.
2. `operation: "execute"`, `action: "request-employee-master-data"`, `confirmed: false`
   → operator approval → `confirmed: true`. It **sends mail** — never confirm without an
   explicit yes.

> **Read the preview's confirmation message out: it says which of two very different
> things will happen.** While an unfinished link is open, the call re-sends that *same*
> link. Once the person has completed a questionnaire and no link is open, the identical
> call starts a **brand-new, empty** questionnaire under a new link — it does not revive
> the old one. Their previous answers stay untouched either way. To correct one value,
> write that field on the record instead of sending a new questionnaire.

> **The preview shows the mail body as markdown, not as the sent HTML.** Under the
> `sends_mail` effect the preview prints `subject`, `to` and a `body (markdown)` block —
> a readable rendering of the notification, cut off at 1.200 characters with an explicit
> `… truncated, N more characters of mail body._` marker. Recipient and subject are the
> complete, literal values; the body is a rendering. So confirm the **recipient** off the
> preview, quote the **subject** verbatim, and do not tell the operator the mail says
> nothing further when the truncation marker is there. The layout, styling and footer the
> person actually receives are not in the preview at all — never describe them from it.

The person confirms an emailed one-time code before seeing or entering anything, and
signs a declaration of accuracy at the end. The form asks for: Person (Name, Geburtsname,
Geburtsdatum und -ort, Geburtsland, Staatsangehörigkeit, Familienstand, Telefon/Mobil,
E-Mail) · **Anschrift** (an address search fills Straße, Hausnummer, PLZ, Ort **plus the
required Bundesland and Land**; if the lookup is down the fields stay hand-fillable) ·
Bank (IBAN, BIC, Kontoinhaber) · Steuer (Steuer-ID, BEA-Widerspruch, Steuerklasse,
Kirchensteuer, Kindergeld, Haupt-/Nebenarbeitgeber, weitere Beschäftigung) · Versicherung
(SV-Nummer, Art der Krankenversicherung, Krankenkasse) · Notfallkontakte (a **list** —
several contacts, each Vor- und Nachname, Mobil, Telefon — **no** `relationship`) ·
Qualifikation (höchster Schul- und Berufsabschluss).

> **Schwerbehinderung and Grad der Behinderung are asked only of someone who already IS
> an Employee — never on the pre-hire questionnaire a Candidate fills in.** § 164 Abs. 1
> SGB IX legitimises the question inside an employment relationship; before one exists it
> is the discrimination-risk question the AGG exists to prevent. Do not tell an operator
> to expect those answers from a candidate, and do not report their absence as a gap.

> **Submitting is a hard server-side gate.** The signature step refuses an incomplete
> questionnaire: every statutory field must be filled — Vor- und Nachname, Geburtsdatum,
> Geburtsort, Geburtsland, Staatsangehörigkeit, Geschlecht, the full home address
> (Straße, Hausnummer, PLZ, Ort, Bundesland, Land), IBAN, Steuer-ID and SV-Nummer.
> Step-saves stay permissive — skipping a section and clicking "Weiter" still works;
> only the final submit enforces. Exactly **two** fields carry a structured "Liegt mir
> nicht vor" escape: `social_security_number` and `tax_id`, each with a reason
> (`not_to_hand` / `first_job` / `other`). That is what to tell a blocked
> Berufsanfänger — a first job means no SV-Nummer exists yet (the employer requests one
> from the Krankenkasse); without the escape they cannot submit at all. Every other
> field rejects an escape outright — name, address and IBAN are always knowable. An
> escaped field is recorded on the submission with its reason but does not count as
> answered, so it is absent from `filled_keys`.

**Track it — `EmployeeMasterDataSubmission` (`0-429`), read-only.** Find it with
`search-model` / `query-model` on `0-429` (filter by `contact_id`) or `get-model`. It is
on the MCP allowlist but deliberately **not** manageable: `manage-model` can neither
create nor edit one, and the apply action is the only thing that ever changes it.

> **The answers themselves never come over MCP — do not offer to read them back.** The
> `data` column is encrypted and hidden on the model, so `get-model` / `search-model` /
> `query-model` never return a Steuer-ID, IBAN, Konfession or Schwerbehinderung. What you
> get is progress and provenance: `status` (`draft` / `submitted` / `applied` /
> `discarded`), `filled_keys` (**which** field keys were answered — key names only, never
> their values), `filled_keys_count`, `signed_at`, `signed_email`, `owner_name`,
> `applied_at`, `applied_employee_id`, `applied_by_name`. The submitted values live on
> the submission's page in the web app.
>
> `filled_keys` is now in the exposed schema (the alluvo#3382 gap is closed) — build the
> apply call's `accepted_keys` from it instead of sending the operator to the web app for
> the key list. The "Liegt mir nicht vor" reasons are **not** exposed over MCP; but on a
> `submitted` questionnaire a statutory key missing from `filled_keys` can only mean the
> person escaped it, and only `social_security_number` and `tax_id` can be — say that
> ("SV-Nummer als 'liegt nicht vor' erklärt") instead of reporting a blank.

**Take it over — `apply-employee-master-data`** on the submission (`0-429`), again via
`manage-record-action`:

- Available from `submitted` onward. `draft` and `discarded` hide it; an already-`applied`
  submission shows it disabled.
- `data: {"accepted_keys": [...]}` — the field keys to write, as the questionnaire names
  them (`tax_id`, `iban`, `address_zip`, …). The Notfallkontakte are **one key for the
  whole list**: `emergency_contacts` — the per-column keys (`emergency_first_name`,
  `emergency_mobile`, …) are not individually acceptable. **Only the keys you pass
  are written.** The list is the operator's decision — they can see the values, you
  cannot; never invent it.
- Two-stage like every write: `confirmed: false` → approval → `confirmed: true`.

What the write does — state it, do not re-derive it:

- Writes into the real records — Contact, Employee, TaxProfile, BankAccount,
  EmergencyContact and the Contact's **home Address** — and creates the Employee row
  when the linked Contact has none yet.
- A blank answer **never** overwrites a stored value.
- Tax data opens a **new TaxProfile version** (valid from today, the previous one closed
  the day before) instead of overwriting the current one, so the payroll history survives.
- Idempotent: applying a second time is a no-op that returns the same employee.
- Accepting `marital_status` also derives the payroll flag `married` on the tax profile —
  so it counts as tax data and opens a new TaxProfile version too, even on its own.
- Accepting `emergency_contacts` **syncs the whole list, destructively**: the submitted
  rows become the employee's emergency contacts by position — row 1 patches the first
  stored contact, row 2 the second, and any stored contact beyond the submitted list is
  **deleted**. That is safe by design: the questionnaire pre-fills the stored contacts,
  so a shorter list coming back is the person's deliberate removal, not an omission. A
  brand-new row still needs both first and last name (a nameless row is skipped rather
  than failing the handover); an existing contact can be patched by a partial row.
- The signed questionnaire PDF is filed as an `onboarding_questionnaire` EmployeeDocument,
  which closes step 2's always-mandatory Personalfragebogen requirement by itself — do not
  file it again by hand. If the PDF render is still pending, everything else is applied
  and only the filing is skipped.
- The review list the operator ticks off shows only answers that would actually change
  something: a value identical to the stored one is omitted entirely, a currently-empty
  field comes pre-checked, a contradicting answer is shown unchecked, and the e-mail is
  never pre-checked. The Notfallkontakte appear as **one row for the whole list**, and
  that row is pre-checked only when no contacts are stored yet — never when some exist,
  because accepting it is the destructive sync above; ticking it is always the
  operator's explicit decision.

> **Anschrift is not a field on the Contact.** `address_street_name`,
> `address_street_number`, `address_zip`, `address_city` and the now-required
> `address_subdivision_code` (Bundesland) and `address_country` (Land) resolve to the Contact's
> own **home** Address (step 2's `home_location` note). Accepting the questionnaire **corrects
> that current row in place** — it does not open a new one, so a routine data handover never
> shows up as a move in the person's address history. Accepted address values are merged
> **over** what is already stored, so accepting only the postcode still yields a complete
> address rather than a street-less one. The address is skipped entirely only when neither
> the accepted answer nor the stored home Address yields a street name — a Meldeadresse is
> identified by its street, and without one there is only a town.
>
> **This field is the one place the Bundesland is still code-only.** Unlike `manage-address`
> (which resolves a spelled-out name), the questionnaire's `address_subdivision_code` is
> validated against a fixed list of **German ISO codes** (`"DE-NW"`) — a name, a bare `"NW"`,
> or an Austrian/Swiss code is rejected here. It is derived from `address_zip` when the
> answer leaves it empty, so correcting the **postcode** is the reliable fix; reach for the
> code itself only for a German address whose zip is genuinely wrong.

### 2b. Record Bankverbindung and Notfallkontakt by hand (preview → confirm)
The manual path — for a Personalfragebogen that came in on paper, or a single value to
correct. When the person filled the digital questionnaire, apply it via 2a instead; that
writes both records for you.

Both are ordinary `manage-model` types — readable via `get-model` / `search-model` /
`query-model` / `get-model-schema` and writable via `manage-model` (`create` / `update`).
They no longer have to be left to the web app.

**Bankverbindung** — `model_type: "0-21"` (BankAccount):

> **Two model types are called "bank account" — take `0-21` here, never resolve by name.**
> `list-model-types` labels `0-21` **"Employee Bank Account"** (this one: the employee's own
> account, wages and Auslagen are paid OUT to it) and a *different* type, `0-323`, plainly
> **"Bank Account"** — the tenant's own invoicing accounts that clients pay INTO
> (`→ manage-contract-lifecycle`). Resolving "Bankkonto" by label lands on `0-323`, and a
> create there would file the employee's private IBAN in the tenant's payee list. In this
> skill "Bankverbindung" always means `0-21`, and `employee_id` is required — `0-323` has no
> such field, so a mis-typed call fails rather than silently writing the wrong record.

- Required: `employee_id`, `account_holder_name`, `iban`.
- Optional: `bic` (max 11 chars), `bank_name`, `is_active`, `is_primary`.
- `iban` is checksum-validated (mod-97). A placeholder, example or half-transcribed
  IBAN is **rejected** — never invent one to get past the preview. Ask the operator to
  read the digits off the Personalfragebogen, or leave the record uncreated.
- Whitespace and casing are normalized on write, so `DE89 3704 0044 0532 0130 00`
  is fine as typed.
- `is_primary: true` is **server-side exclusive**: the employee's other accounts are
  demoted automatically. Do not issue a second call to clear the previous primary,
  and never try to mark two accounts primary — the second write silently wins.

> **The IBAN comes back masked in every MCP read** — `DE89********3000`: country code,
> check digits and the last 4 characters, everything else `*`. This is one-way and
> unconditional; the full value stays in the database and in the web app, but never
> reaches this session. So: do not read an IBAN back to confirm it, do not compare two
> IBANs, do not copy one from one record to another, and do not report a masked value
> as if it were the account number. To verify a transcription, have the operator check
> it in the app. A BankAccount's label in search results and relation previews is its
> masked IBAN, which identifies nothing for the operator — name the account holder and
> the bank instead.

**Notfallkontakt** — `model_type: "0-16"` (EmergencyContact):

- Required: `employee_id`, `first_name`, `last_name`.
- Optional: `mobile`, `phone`, and `relationship` — one of `father`, `mother`,
  `brother`, `sister`, `other_family`, `life_partner`, `spouse`, `friend`.
- `relationship` is deliberately optional: a Personalfragebogen usually does not state
  it, and a guessed relationship is worse data than a blank field. Leave it out unless
  the form says so.

Both are two-stage like every other write: `confirmed: false` preview → operator
approval → the identical call with `confirmed: true`. Create one record per call; use
`bulk-manage-model` only when writing several at once.

### 2c. Record Schwerpunkt-No-Gos (preview → confirm)
When the person states a Fachbereich they will not work in ("keine Palliativpflege", "keine
Beatmung"), record it as a **No-Go** against the Schwerpunkte catalogue (`FocusArea`,
`0-369`).

- **It hangs on the Contact, never on the Employee.** The Contact (`0-105`) is the identity
  root for a person, so a single No-Go covers them as Employee **and** as Candidate. Read the
  `contact_id` off the Employee (`get-model` `0-2`, or `get-profile` with
  `resource: "completeness"`, which returns the linked Contact's id) and use that as the
  source.
- Resolve the Schwerpunkt with `search-model` (`0-369`) first — `name` is unique tenant-wide,
  so a duplicate "Intensivpflege" is rejected. A genuinely new entry goes in via `manage-model`
  `action: "create"`, `model_type: "0-369"`, `data: {name, code?, description?, is_active?,
  sort_order?}`. Reading the catalogue needs the `focus-areas.view` permission.
- Attach: `manage-association`, `action: "attach"`, `source_type: "0-105"`,
  `source_id: <contact_id>`, `target_type: "0-369"`, `target_id: <focus area id>`,
  `confirmed: false` → approval → `confirmed: true`. Several at once: `"bulk-attach"` with
  `target_ids` (max 50). Withdrawing one: `detach` / `bulk-detach`.
- A call with `source_type: "0-2"` (Employee) is refused with a message naming the linked
  Contact — follow that hint instead of retrying on another source type.

> **What a No-Go does — and what it deliberately does not.** It acts in the **client portal**
> only: for an Abteilung carrying that Schwerpunkt (and only while the Schwerpunkt is
> `is_active`), the customer neither sees the person in the portal nor can book them; the
> booking is refused server-side at add, change and finalisation. Operator matching,
> Dienstplan and AÜV are **untouched by design** — you keep seeing the person and decide
> informed. That divergence is intended; never report it as a bug, and never treat a No-Go as
> a substitute for a Blacklist entry (person ↔ company/sector), which is the hard block.
>
> Never infer a No-Go. It is the person's own statement, or the Disponent's decision — not
> something to derive from a gap in the CV. The Abteilungs-side (which Schwerpunkte a
> department carries): `→ intake-personalbedarf`. Full rules: the MCP prompt
> `manage-focus-areas-prompt`.

### 2d. Complete the Dienstwagen / Fuhrpark data (preview → confirm)
Reach for this when the `vehicle` requirement is open (it is optional, and its `meta`
carries the Kennzeichen when satisfied), or when an assigned task says
"Fahrzeugdaten vervollständigen". The vehicle record and its satellites are writable
over `manage-model` (`confirmed: false` preview → confirm), so the data belongs in
real fields — **never** in a `[fuhrpark-daten]` block inside `vehicles.notes`.

- **Vehicle** (`0-4`) — `license_plate` and `manufacturer_id` are required on create.
  `first_registration_date` is the registration date, distinct from
  `year_of_manufacture`: HU deadlines and the geldwerter Vorteil key off it.
  `ownership_type` is `company_owned` / `lease_agreement` / `rental_contract`.
- **Kilometerstand — always a new reading, never a write on the vehicle.**
  `current_mileage_km` and `current_mileage_recorded_at` on `0-4` are a read-only
  projection of the newest reading; they are not writable fields and an observer
  recomputes them from the readings after every save, edit or delete. Record mileage
  as **VehicleMileageReading** (`0-424`): `vehicle_id`, `mileage_km` and `recorded_at`
  required, plus optional `source`, `employee_id`, `notes`. `recorded_at` is the date
  the odometer was **read**, not the date you type it in. `source` is `operator` /
  `employee` / `import` and defaults to `operator` — set it when the figure came from
  the driver or an import. A correction or a backdated figure is another reading; the
  projection resolves itself.
- **The Tacho-Foto is the Beleg — and it cannot be attached over MCP.** `0-424` carries
  one odometer photo (`odometer_photo`, single file, jpeg/png/heic/heif, max 12 MB), web
  form or Mitarbeiter-App only — exactly like the Schadensfotos on `0-67`. Nothing you pass
  to `manage-model` sets it; say so and have the driver add it there.
- **Whether the photo is mandatory is a tenant setting — check it before you promise it.**
  `fleet.require_mileage_photo` (bool, **default `false`**, see the settings block below)
  decides one thing only: whether a driver answering a `request_mileage` in the
  Mitarbeiter-App can submit **without** a photo. Off — the default — the app still **offers**
  the upload and stores a voluntarily attached photo; it simply does not block sending. On,
  the submission is refused without one. It **never** touches the operator path: recording a
  reading yourself (form or `manage-model` on `0-424`) is photo-optional in both states.
  So "der Fahrer muss den Tacho fotografieren" is only true where the tenant switched it on
  — read the setting before telling a driver that, and if the operator wants it to be true,
  that is a `manage-settings` update, not a rule you can assert.
  The provenance follows: with the setting **on**, a reading with `source: employee` always
  has a photo; with it **off**, it has one only if the driver chose to attach it, and a
  reading you enter as `operator` normally has none either way. Whenever the Kilometerstand
  has to hold up against Leasing — an Überschreitung der contracted mileage, a
  Rückgabe-Abrechnung — name which of the two you are quoting, and when the figure needs a
  Beleg, ask the driver via `request_mileage` instead of typing it in yourself. Whether a
  reading is actually backed reads off `0-424` as `has_odometer_photo` — read that flag
  rather than inferring it from `source`.
- **Don't know the Kilometerstand? Ask for it — via the action, never via `manage-model`.**
  `request_mileage` is a record action on the **Vehicle** (`0-4`), run through
  `manage-record-action`: `operation: "list"` to see whether it is available, then
  `operation: "execute"`, `action: "request_mileage"`, `confirmed: false` preview →
  approval → `confirmed: true`. Optional `data: {"due_in_days": <n>}`; left out, it falls
  back to the tenant's `fleet.mileage_request_due_days` (default 3 — see the settings block
  below). `due_in_days: 0` creates a request with **no** deadline, which never goes overdue
  and therefore never pushes; only pass it when that is what you mean. Creating a
  **VehicleMileageRequest**
  (`0-425`) directly with `manage-model` is technically allowed but **wrong** — only the
  action resolves the recipient and enforces the rules below, so a hand-made request can
  land on nobody.
- **The action is deliberately blockable — pass the reason on, don't route around it.**
  `list` returns it as unavailable with the reason: the assigned driver has **no app
  login** (invite them to the employee app first — see step 5), the vehicle has **neither
  a driver nor a responsible person** (nobody to ask), or the vehicle **already has an
  open request** (one at a time, by design). With no driver assigned but a responsible
  person set it is *not* blocked — the request goes to that person to find the number out.
  The preview names the recipient before you confirm; read it out.
- **Answering closes the request — there is no separate "close" call.** Any new reading
  (`0-424`) for that vehicle marks every open request of that vehicle as `fulfilled`,
  whoever entered it, including the operator entering it herself. What the driver has to
  do in the app is **type the number**, plus attach a photo of the Tacho where the tenant
  requires it (`fleet.require_mileage_photo`; off by default the upload is offered but
  optional). The app also rejects a figure **below** the last known
  reading. So a driver who cannot submit is usually looking at a typo or at the wrong
  vehicle; sort that out before re-asking rather than recording the figure yourself, which
  would close the request without a Beleg. The reading the app writes is always
  `source: employee`. Never set
  `fulfilled_by_reading_id` or `fulfilled_at` by hand. To **withdraw** a request that no
  longer applies (vehicle left the fleet, the figure arrived via the Tankkarten-Abrechnung),
  update `0-425` `status` to `cancelled` — requests never expire on their own. The driver
  is **not** pushed when the request is created: it appears as a card in the employee app,
  and the push follows only once the deadline has passed, so don't promise an instant ping.
  Open requests are readable with `search-model` on `0-425` (`status`, `due_on`,
  `vehicle_id`).
- **One ownership record per vehicle** (to-one — check for an existing one before
  creating): **VehicleAsset** `0-64` (Kauf), **VehicleLease** `0-65` (Leasing, incl.
  `contracted_mileage_km` — the contracted annual/total mileage), **VehicleRental**
  `0-66` (Miete). Each needs `vehicle_id`.
- **FuelCard** (`0-56`) — `card_identifier` and `supplier_id` required, `vehicle_id`
  links the card to the vehicle. **Prüfungen und Werkstatt-Services** live on
  **VehicleInspection** (`0-69`) — see the block right below, they are no longer just
  "HU/UVV dates".
- **Key** (`0-52`, `name` + `key_category_id` required) and **Insurance** (`0-63`,
  `name` required) hang off the vehicle through a **list**, not a `vehicle_id`: pass
  `vehicles: [<vehicle_id>]` on create **and** on update. The list is the full set —
  an update replaces the current links rather than adding to them. The insurance
  pivot's own terms (`valid_from` / `valid_until`, `premium_amount`,
  `coverage_amount`) are deliberately not exposed over MCP; they stay on the vehicle's
  Versicherungen tab.

- **Prüfungen und Services — VehicleInspection (`0-69`), two families of `type`.**
  One record is one event of one type; `vehicle_id` and `type` are required. The type
  decides which deadline the record even has, so pick it before you fill anything else.
  There is **no plain `inspection` value any more** — "Inspektion" split in two.
  - **Statutory, date-only** — `hu` (HU/Hauptuntersuchung), `au` (Abgasuntersuchung),
    `sp_uvv` (Sicherheitsprüfung/UVV). These hand out a badge, so `certificate_number`
    belongs on them, and a mileage deadline must never be invented for one: an HU does
    not fall due earlier because the van drove a lot.
  - **Workshop services, no certificate** — `inspection_small` (Kleine Inspektion),
    `inspection_large` (Große Inspektion), `oil_change` (Ölwechsel-Service),
    `air_conditioning` (Klimaservice). The first three are due by date **or** by
    odometer, whichever comes first; `air_conditioning` is date-driven like the
    statutory ones despite being a workshop service.
  - **Fields:** `performed_on`, `due_on`, `result` (`passed` / `passed_with_defects` /
    `failed`), `defects`, `certificate_number`, `provider`, `mileage_at_inspection`,
    `next_due_mileage`, `notes`, plus `contact_id` (Werkstatt-Kontakt) and
    `appointment_at` (Werkstatttermin).
  - **Findings go in `defects`, not in `notes`.** It is a real field now — the free-text
    workaround is obsolete. It is the field the HU §29 report and the UVV protocol list,
    so fill it whenever `result` is `passed_with_defects` or `failed`.
  - **`next_due_mileage` is the odometer deadline** (an absolute reading, not a budget)
    and only means anything on `inspection_small`, `inspection_large`, `oil_change`.
    Don't set it on a date-only type. The web form additionally offers the relative entry
    a workshop printout uses ("in 15.900 km oder 648 Tagen"); over MCP you always write
    the **absolute** values `due_on` / `next_due_mileage`.
  - **Both deadlines are auto-filled when left blank** — `due_on` from `performed_on` +
    the type's interval (24 months for `hu`, `au`, `inspection_large`,
    `air_conditioning`; 12 for `inspection_small`, `oil_change`, `sp_uvv`),
    `next_due_mileage` from `mileage_at_inspection` + the type's km interval (15 000 for
    `inspection_small` / `oil_change`, 30 000 for `inspection_large`). A value you send
    always wins; these only fill a hole. Both are **suggestions** — the car's own service
    computer or the workshop printout beats them, so enter the stated figure where you
    have it instead of leaning on the default.
  - **`due_on` is always stored as the last day of its month.** Deadlines here are
    month-granular (HU badge, UVV "gültig bis"), so a 14.03. you send reads back as
    31.03. That is not a bug — don't "correct" it.
  - **A `mileage_at_inspection` on a record with `performed_on` also writes a
    VehicleMileageReading (`0-424`)** with `source: operator`, dated `performed_on`. So do
    **not** create that reading by hand as well; it would only be skipped as a duplicate
    (same vehicle + date + value) or double up the history. It moves the vehicle's current
    odometer and closes any open Kilometerstand-Anfrage, exactly like the driver's own
    submission.
  - **A completed inspection schedules its successor — expect two rows per type.** On
    create, a record with `performed_on` set and `due_on` still in the future spawns a
    second, open `0-69` record of the same type carrying `vehicle_id`, `type`, `due_on`
    and `next_due_mileage`, unless an open one already exists. So don't create the next
    Frist yourself after recording a completed one, and don't read the extra row as a
    duplicate. Backfilled history (`due_on` already past) schedules nothing.
  - **"What does this vehicle owe" is the LATEST record per type**, ordered by
    `performed_on ?? due_on` — every older row of that type is superseded and must not be
    reported as an open deadline.
  - **Due status is the WORSE of the date and the mileage verdict, never the date alone.**
    `overdue` (deadline passed, or the odometer is at/past `next_due_mileage`) ▸ `due_soon`
    (within 1 month, or within 1 000 km) ▸ `upcoming` (within 2 months, or within 2 500 km)
    ▸ `ok`. A missing deadline on one axis never improves the verdict from the other. So a
    high-mileage vehicle can be **overdue on a service whose date is still months away** —
    when you report Fristen, read `next_due_mileage` against the vehicle's current
    Kilometerstand, not just `due_on`.
  - Data-quality Issues (`0-190`) for overdue/expiring inspections are raised **only** on
    the latest record per type and notify the **vehicle's** owner; the currently assigned
    driver is reminded separately. Fixing them is `triage-data-quality`'s ordinary path —
    record the renewed inspection, the Issue resolves itself.

- **Assigning the vehicle to an employee — a record on `0-432`, never an association.**
  The Fahrzeugzuweisung behind the `vehicle` requirement is **EmployeeVehicle** (`0-432`),
  a first-class model type on `manage-model`. It is a **history**, not a link: every row
  has its own id and a `valid_from` / `valid_until` window, and the same person may drive
  the same car in two separate periods.
  - **Hand a car over** → create `0-432` with `employee_id`, `vehicle_id` and `valid_from`
    (all three required). Optional: `valid_until` (must not precede `valid_from`),
    `max_annual_mileage_km`, `notes`.
  - **End an assignment** → **update** that row's `valid_until`. Never delete the row and
    never reach for `manage-association` `detach` — the row *is* the answer to "who drove
    B-XX-1234 in 2026", and deleting it takes that answer with it.
  - `is_current` is **not** writable: it is recomputed from the dates on every save. Don't
    send it; read it back.
  - **Reading the periods:** `manage-association` still lists them under *Vehicle
    Assignments (Fahrzeugzuweisungen)* on the Employee, with the Assignment ID you need as
    the `manage-model` record id — but it is **read-only** there and refuses writes with a
    pointer back to `0-432`. `search-model` on `0-432` works too (`employee_id`,
    `vehicle_id`).
  - **Side effect worth naming:** a currently-valid assignment puts the employee into the
    Führerschein-Kontrolle cycle, and that flag is **one-way** — ending the assignment does
    not clear it.

**The three tenant-wide Fuhrpark settings live on `manage-settings`, group `fleet`.**
All are read with `action: "get"` and written with `action: "update"`, and all are
tenant-wide — reach for them when the operator is fixing a policy, not a single vehicle.
All three are also editable in the web app under *Einstellungen → Apps → Fuhrpark*, so
someone may have changed them since your last read — `get` before you write.

- `mileage_request_due_days` (int, 1–90, default 3) — the default deadline every
  `request_mileage` gets when the call carries no `due_in_days`. Changing it does not touch
  requests that already exist.
- `require_mileage_photo` (bool, default `false`) — whether a driver answering a
  Kilometerstand-Anfrage **in the Mitarbeiter-App** must attach a Tacho-Foto. Off, the app
  still offers the upload and keeps a voluntary photo; it just does not block submitting.
  It never gates an operator recording a reading (form or `manage-model` on `0-424`) — that
  path stays photo-optional either way. Turning it **on** is the only way to make "Foto beim
  Kilometerstand ist Pflicht" true, and turning it **off** does not remove the upload from
  the app, only the obligation. Say which of the two the operator actually wants before you
  preview the write.
- `usage_notes` (array of strings, max 20, each ≤255 chars) — the "Wichtige Hinweise für
  die Fahrzeugnutzung" every employee sees verbatim on *Mein Fahrzeug*. The update
  **replaces the whole list**, so `get` first and send the full array back with your line
  added, or you silently delete the other hints.

```
manage-settings(group: "fleet", action: "get")
manage-settings(group: "fleet", action: "update", fields: { "mileage_request_due_days": 7 })
manage-settings(group: "fleet", action: "update", fields: { "require_mileage_photo": true })
```

Confirm the exact writable fields with `get-model-schema` (context `create` / `update`)
before the preview — fields outside the update schema are silently dropped.

### 2e. Schadensmeldung — report a damage, then run the claim out
A damage reported by phone belongs in the same record the driver's own app submission
produces. Use the **action**, not a generic create.

- **`report_damage` is a record action on the Vehicle (`0-4`)**, run through
  `manage-record-action`: `operation: "list"` first, then `operation: "execute"`,
  `action: "report_damage"`, `confirmed: false` preview → approval → `confirmed: true`.
  It produces the report with status **`submitted`**, which notifies the vehicle's
  responsible owner. Creating a **VehicleDamageReport** (`0-67`) by hand is the wrong door:
  the generic create lands a `draft`, and nobody is notified about a draft.
- **Required in `data`:** `incident_type` (`accident` / `damage` / `theft`), `occurred_at`,
  `description`, and a driver — `employee_id` defaults to the vehicle's **current** driver,
  so pass it explicitly whenever the car has since moved on. With no `employee_id` and no
  current driver the call fails rather than guessing.
- **Optional:** `incident_location`, `fault` (`yes` / `no` / `partial`), `police_involved`,
  `police_station`, `police_reference_number`, `has_witnesses`, `witness_details`,
  `has_injuries`, `has_property_damage`, `own_vehicle_damage_description`, and `parties`
  (max 5; each `name`, `phone`, `vehicle_plate`, `insurance_company`,
  `insurance_policy_number`).
- **Company policy says the police attend every damage — that rule is addressed to the
  driver, and this call does not enforce it.** Record the damage even when no police
  attended; a block here would not enforce the rule, it would only lose the report. Note
  the gap in `description` instead of refusing.
- **Photos cannot be attached over MCP** — only from the web form or the employee app. Say
  so and ask the driver to add them there.
- **Finishing the claim — two actions on `0-67`, in this order.** `0-67` is readable over
  MCP (`search-model` / `get`) but **not** `manage-model`-writable, and `status` is never
  a field you write:
  `draft` | `submitted` | `under_review` --`send_to_insurer`--> `sent_to_insurer`
  --`close`--> `closed`.
  - **`send_to_insurer`** is the **only** thing that generates the filled insurer claim
    form, it cannot be repeated, and the PDF only materialises when the report's linked
    insurance has a form filler on file — so **set `insurance_id` before sending**, or the
    status moves and no PDF ever appears. It also **freezes** the record (no edits, no
    delete) and it **emails nobody**; delivery to the insurer stays a manual step.
  - **`close`** is the only move left on a sent report, and it is terminal — no edit, no
    reopen, no delete. It notifies nobody and tells the insurer nothing; it records *our*
    side as finished. Refused from `draft` / `submitted` / `under_review`.
  - A claim left unclosed sits open forever, so name the next action when you report one.

### 2f. Record the Qualifikationen / Berufsbilder (preview → confirm)
Which Einsatzrollen the person can be placed in — the `StaffingRole` catalogue (`0-100`).
This is the block a client reads first in the Profilvertrieb, and the input the default
hourly rate and every match score are resolved from, so it belongs in the onboarding pass,
not "later".

- **The qualification hangs on the Contact, not on the employment.** The rows live on the
  Contact (`0-105`); Employee (`0-2`) and Candidate (`0-81`) read and write the *same* rows
  through it. So you can record roles for a **Kandidat before the Einstellung** and they are
  already there once the Employee record exists — nothing to re-enter, nothing lost.
- Resolve the role first — `resolve-staffing-role` with the person's own wording, or
  `search-model` on `0-100`. Never invent a `staffing_role_id`.
- Attach: `manage-association`, `action: "attach"`, `source_type: "0-105"` (Contact) —
  or `"0-2"` with the Employee id, which addresses the identical rows —
  `target_type: "0-100"`, `target_id: <role id>`, plus a `pivot` map:
  `is_primary`, `years_experience`, `certified_since` (`YYYY-MM-DD`). `confirmed: false`
  preview → approval → `confirmed: true`. Removing one: `detach` / `bulk-detach`.
  **`source_type: "0-81"` (Candidate) is not a declared pair** and comes back with "No
  association relationship defined" — take the candidate's `contact_id` and use `0-105`.
- Several roles at once: `"bulk-attach"`, max 50 targets, in one of two forms:
  - `targets: [{id, pivot}]` — a pivot **per target**. Use this whenever the values
    differ per role, which for Berufsbilder is the normal case:
    `targets: [{"id": 12, "pivot": {"is_primary": true, "years_experience": 8}},
    {"id": 34, "pivot": {"years_experience": 2, "certified_since": "2021-03-01"}}]`.
    A per-target `pivot` is merged **over** the call-level `pivot`, so shared values
    (e.g. one `certified_since`) can still be passed once at call level.
  - `target_ids: [...]` — the flat form, where the single call-level `pivot` map is
    applied to *every* target. Correct only when the roles genuinely share their values.
  The whole set of roles now goes in **one** call either way; do not fall back to one
  `attach` per role to vary a pivot value.
  **`is_primary: true` still belongs to exactly one target** — see below. Passing it in
  the call-level `pivot` of a `target_ids` bulk claims it for *every* role; the
  one-primary rule is then enforced row by row, so each one demotes the one before it and
  whichever happens to be written last silently ends up primary — no error, and not
  necessarily the role you meant. Put it on a single entry of `targets` instead.
  The preview reports the pivot per target (`per target:` with one line per id) whenever
  the values differ, and a single line when they don't — read it back before confirming,
  so a mis-assigned `is_primary` or a wrong `years_experience` is caught in the preview.
- **Exactly one primary role per person.** Setting `is_primary: true` demotes the person's
  other roles automatically — server-side, scoped to the Contact, so it holds across their
  Employee *and* Candidate records. Never issue a second call to clear the previous primary.
  A person with no primary role raises the data-quality issue **Missing Primary Staffing
  Role** and gets **no default rate and no card price** (`→ triage-data-quality`); the fix
  there is the `set-primary-staffing-role` action on the Employee, which writes the same row.
- Read the current roles back with `action: "list"` before attaching more — the list shows
  ID, Label, Primary, Years exp. and Certified since per row.

### 2g. Record the bAV-Versorgungsträger — Ziffer 9.11 of the Arbeitsvertrag (tenant-wide, confirm before writing)
Name and address of every occupational-pension provider (Versorgungsträger der
betrieblichen Altersvorsorge) the tenant has promised its employees — the Pflichtangabe
§ 2 Abs. 1 Satz 2 Nr. 13 NachwG requires **on the Arbeitsvertrag itself**.

This is a **tenant-wide** list, not a per-employee field: you record it once, and every
Arbeitsvertrag generated afterwards carries it. It does not belong to an individual
onboarding — do it the first time it is missing, then never again.

- **MCP is the only way in.** There is no settings *page* for this list, so never send an
  operator to the web app for it. `manage-settings`, group `contract`, field
  `pension_providers` — `action: "get"` reads the current list, `action: "update"` writes it,
  and `action: "describe"` returns the `contract` group's field docs (the field list is **not**
  in the tool description — call `describe` rather than guessing a neighbouring field name).
  Needs the settings-manage permission; without it the call comes back as a permission error.
  `describe` is the exception: it serves static documentation and needs no permission.
- **Empty is the default and often the correct state.** Every tenant starts with an empty
  list, and while it is empty the Arbeitsvertrag omits Ziffer 9.11 **entirely** — no heading,
  no placeholder. That is the right rendering for a tenant that promises no bAV, not a gap to
  paper over. Only fill it in when the operator confirms an occupational pension is actually
  promised; naming a Versorgungsträger nobody agreed to would put a false statement into a
  signed employment contract.
- **Shape per entry:** `name` (required, ≤255) plus the optional `address_line` (≤255),
  `postal_code` (≤32), `city` (≤255), `country` (≤255). An entry without a `name` makes the
  **whole call fail** — an address with nobody's name on it identifies no Versorgungsträger.
  Empty parts are simply left out when the clause prints (name · address_line · "PLZ Stadt" ·
  country, one block per provider, several providers one after another).
- **The update replaces the whole list.** There is no append: `get` first and send the full
  array back with your addition, or you silently drop the providers already recorded.
  Sending `pension_providers: []` clears the list — and with it Ziffer 9.11.
- **`confirmed` does nothing on this group.** `manage-settings` declares a `confirmed`
  parameter, but it gates the `candidate_flow_prompts` group only — on `contract` it is
  ignored and, like the go-live date in step 6, `update` writes immediately. Read the exact
  list you are about to send back to the operator and get an explicit yes *before* the call;
  there is no preview stage to catch it in.

```
manage-settings(group: "contract", action: "get")
manage-settings(group: "contract", action: "update", fields: {
  "pension_providers": [
    { "name": "…", "address_line": "…", "postal_code": "…", "city": "…", "country": "…" }
  ]
})
```

### 3. Check nearby placement opportunities
Use `get-profile` (`resource: "profile"`, `model_type: "0-2"`) again — it provides home location and position.
Call `find-matches-prompt` to find matching clients / open Personalbedarfe
nearby. Output up to 5 top opportunities with Name, ID, and distance.

### 4. Create prospecting tasks (preview → confirm)
One follow-up task per relevant opportunity (e.g. "Send profile to client X", due in
3 days) — write them all in **one** `bulk-manage-model` call with `model_type: "0-5"`
(Task), one `operations` entry each, rather than looping single creates.

Attach each task to both records it concerns via
`attachments: [{"type_id": "0-2", "id": <employee>}, {"type_id": "0-3", "id": <company>}]`
— `attachments` accepts any number of entries of different types. `owner_id` defaults to
the authenticated user. `due_at` needs an explicit timezone offset here
(`2026-07-30T09:00:00+02:00` or `...Z`), unlike `manage-task`'s tenant-local
`Y-m-d H:i`.

Preview with `confirmed: false`, then repeat the identical call with `confirmed: true`
after operator approval.

### 5. Send invitation — or resend the login link (optional)
The invitation runs as the `invite-user` **record action** on the Employee
(`model_type: "0-2"`), via `manage-record-action` — no separate status tool.

> `invite-user` is **idempotent invite-or-resend**: without an account it provisions
> the user, and once one exists (a linked user, or a non-cancelled invitation for the
> email) the *same* action resends the login link instead. Running it twice never
> creates a second account. In resend mode the label reads "Einladung erneut senden"
> and the wizard has no user-type step — `user_type_slug` is ignored there.

1. `manage-record-action` `operation: "list"`, `model_type: "0-2"`,
   `record_id: <employee id>`. Look up the `invite-user` entry: if it is
   unavailable, its `unavailable_reason` states exactly why — no email address, no
   employment relationship attached, or no active Salary record (proxy for a signed
   Arbeitsvertrag). Those three gate the **first invite only**; they never block a
   resend. Separately, if the employee self-service app (`EmployeeAppModule`) is not
   live for the tenant, the action is still listed but **disabled** with that reason
   — the link would land on the "coming soon" page. Report the reason to the operator
   and stop; fix the named precondition first (`manage-model` /
   `manage-association`), or have the module enabled.
   "Already has a linked user account" and "an invitation is already pending" are
   **no longer** blockers — both simply mean the action resends.
2. If available and the operator wants to proceed: `operation: "execute"`,
   `action: "invite-user"`, `confirmed: false` — show the email address and say
   plainly whether this is a first invite (plus the resulting user type) or a resend.
   On a first invite `data.user_type_slug` defaults to `external` (employee
   self-service panel); only set another slug on explicit request.
3. Only after explicit approval: same call with `confirmed: true`. A resend also
   extends the invitation's expiry when it has expired or has under two days left.

> **A connected inbox mailbox can never be invited — and you only find out on commit.**
> If the address on the Employee is the mailbox behind a connected inbox channel
> (`anfrage@`, `verwaltung@`, `hallo@` … — the Gmail/Outlook account wired up under
> Einstellungen → Inbox), the **first invite** is refused with a 422 naming the inbox:
> *"Diese Adresse ist das Postfach des Posteingangs „X". Ein geteiltes Postfach kann kein
> persönliches Benutzerkonto werden — bitte laden Sie die Person mit ihrer eigenen Adresse
> ein."* A shared mailbox belongs to the team, and its login codes would land back in the
> very inbox alluvo syncs, readable by every member.
>
> Three things to know before you hit it:
> - **Nothing warns you first.** This check is not part of the gate statuses, so
>   `operation: "list"` shows `invite-user` as available with no `unavailable_reason`, and
>   `confirmed: false` previews cleanly. The refusal arrives only on `confirmed: true`.
> - **It is not transient — never retry it.** Report the refusal to the operator and ask for
>   the person's own address. The fix is to correct the Employee's `email` via `manage-model`
>   (`model_type: "0-2"`) and invite again — with `confirmed: false` first, as always. Do not
>   route around it, and do not suggest the Einstellungen → Benutzer flow instead: the same
>   guard applies there.
> - **Resends are unaffected**, and so are forwarding targets. The guard runs on the
>   first-invite path only, so an employee who already has a linked user or a pending
>   invitation still gets their login link resent. And it matches only a channel's own
>   mailbox — an inbox **Weiterleitungsziel** (`→ clean-inbox`) is routinely a real person's
>   address and is deliberately left invitable.

> **"Der Mitarbeiter hat nie einen Code bekommen."** Login is **OTP by default for every
> account**. There is no per-user switch that can turn the code off any more, and no
> "which login method applies" lookup — an account with a working address gets a code,
> full stop. So this symptom is no longer an account problem you can repair by inviting;
> the remaining causes are ordinary ones:
>
> - **There is no linked user account yet** — `invite-user` is in *first-invite* mode. That
>   is the one case an invite fixes, and it is the case to check first (step 1 above tells
>   you which mode you are in).
> - **The address on the record is wrong or stale** — the code went to an old mailbox. Fix
>   `email` on the Employee (`manage-model`, `model_type: "0-2"`), then invite/resend.
> - **Plain mail delivery** — spam folder, full mailbox, blocked domain. Nothing on the
>   alluvo side to fix; say so rather than resending a fourth time.
>
> **The "Code gesendet" screen proves nothing.** The login endpoint answers with the same
> "if an account exists, a code has been sent" message whether or not the address is known —
> deliberately, so it leaks no account list. Never read that screen as evidence a code
> actually went out.
>
> **Never write to a User's password or authentication fields** — that is not operator data,
> and there is no MCP path to it.

> **A password is the employee's own business — you cannot set one, and you do not need to.**
> An account signs in by code by default; a password is an optional extra the *employee*
> sets themselves, always gated behind a fresh code mailed to their address. Two entry
> points, both self-service:
>
> - **From the branded employee login** — *"Noch kein Passwort? Melde dich per Code an — oder
>   setze hier eins."* → **Passwort setzen**. This is also the "Passwort vergessen" path:
>   setting one overwrites whatever was there.
> - **Inside the Mitarbeiter-App** — *Einstellungen → Passwort*, same code step even though
>   they are already signed in.
>
> Once set, the code-entry step offers *"Stattdessen mit Passwort anmelden"*. Route every
> "Passwort vergessen / zurücksetzen" request straight back to the employee — do not promise
> an operator-side reset, and never tell an employee they "cannot have a password". You also
> cannot tell whether someone *has* one: nothing exposes that, by design.
>
> **Where to find who is stuck:** *Auswertungen → Mitarbeiter-App*. The funnel is three
> nesting stages — `employed` → `has_account` → `app_enabled` — plus three non-nesting
> signals (`life_sign`, `pwa_installed`, `push_enabled`). Below it are exactly three
> work lists, and each person sits in exactly one: **`no_life_sign`** (app is on, never
> used it → resend), **`invitable`** (no account, the gates pass → invite), and
> **`not_invitable`** (no account, grouped by the blocking gate — fix the named
> precondition first). There is **no** fourth "Login unmöglich" list any more; if an
> operator asks for it, say that bucket was retired because the situation it named
> cannot occur.

There is **no** `resend-invitation` action on Employee — it was removed; never call it.
The former `get-employee-invitation-status` and `invite-employee-user` tools are **gone**
too — they no longer exist on the MCP server, so there is no fallback: `manage-record-action`
is the only path. Read the invitation state from `operation: "list"` on `0-2` (the
`invite-user` entry's availability and `unavailable_reason`), and invite or resend with
`action: "invite-user"`.

### 6. Set the go-live date if the tenant is migrating in waves (confirm before writing)
Relevant only for a tenant that came from previous software and is onboarding its
workforce wave by wave — skip it for an ordinary new hire, where the tenant default
already fits.

The go-live date is when this employee starts working in alluvo. **Before it, they are
asked neither to release hours (Stundenfreigabe), to confirm Einsatzmitteilungen, nor to
hand in AU-Bescheinigungen whose deadline predates it** — that period ran in the previous
system, so the requests would be noise they cannot act on. It resolves per-employee override → tenant-wide `employee_app.go_live_date` → none.

`manage-record-settings` handles it (the tool covers Employee `0-2` as well as Company
`0-3`):

1. `action: "describe"`, `model_type: "0-2"`, `model_id: <employee id>` — shows the
   resolved value, the tenant default, and whether an override is stored. **Describe
   first**; keys are model-scoped and Employee currently carries only this one.
2. `action: "set"`, `key: "employee_app.go_live_date"`, `value: "YYYY-MM-DD"`. There is no
   preview stage on this tool — name the employee and the date to the operator and wait for
   a yes before calling it. Needs `update` permission on the Employee.
3. `action: "clear"` removes the override and reverts to the tenant default.

> **It settles nothing; it only decides what the employee is asked.** No `Timesheet` is marked
> approved, no Einsatzmitteilung acknowledgement is stamped, no AU is marked received — nothing
> is signed on anyone's behalf. Never tell an operator this "closes off" or "approves" the past:
> a released Abrechnungszeitraum carries a real client signature, and one behind the cutoff has
> none.
>
> Two consequences worth naming before you set it:
>
> - **Pre-go-live Abrechnungszeiträume stop existing, they are not just hidden.** No period ending
>   before the date is materialised any more, so it also drops out of your own `Timesheet`
>   (`0-426`) counts. Nothing is lost — a Zeitraum is derived from the Schichten and time entries
>   and is rebuilt if you clear or move the date back — and a period the client or employee
>   already confirmed, released or invoiced is **never** removed, whichever side of the cutoff it
>   sits on.
> - **Einsatzmitteilungen and AU-Bescheinigungen are hidden, not removed** — those operator-side
>   MCP counts still include the pre-go-live period. Details `→ approve-stundenfreigabe`.

The same value can be set in the app on the employee's **Einstellungen** tab.

### 7. Ask the employee directly — a conversation in their app (preview → confirm)
When a gap is left after all of the above — a missing Notfallkontakt, an IBAN nobody
supplied, an unclear Qualifikation — you can reach the employee **inside the
Mitarbeiter-App** instead of waiting for them to write:
`manage-ticket` `action: "create"`, `mode: "employee_app"`, with `employee_id`, `subject`
and `body` (`priority` optional, default `medium`). Call it once without `confirm` to get a
preview, show that to the operator, then repeat with `confirm: true`.

- **No email is sent.** The message appears under „Nachrichten" in the employee's
  self-service app together with an in-app notification and a web push.
- **It needs an app account.** Without one the call fails with "has no self-service app
  account yet" — run step 5 first.
- **It opens a real support ticket** in the tenant's Mitarbeiter-Support inbox, owned by
  you, status `waiting_on_user`; the employee's answer lands back in that same ticket and is
  then triaged like any other Vorgang (`→ clean-inbox`).
- **Not a replacement for the Personalfragebogen.** For the whole set of Stammdaten, step 2a
  is still the right instrument — it writes the answers back into the record. A conversation
  returns prose you have to enter yourself, so use it for one or two specific questions, or
  to explain a request the questionnaire cannot.
- **Never send unasked.** Show the operator the recipient, the subject and the body and get
  a yes; the confirmed call sends and notifies in one step.

## Output
- Profile completeness in percent + traffic-light status per section
- List of open required fields (blocking), recommended fields, and document
  to-dos (non-blocking Personalakte gaps)
- Personalfragebogen status (questionnaire sent — new link or re-send · submission
  status · how many fields were answered · applied yes/no with the accepted keys; never
  the submitted values, which do not reach this session)
- Bankverbindung and Notfallkontakt records created (account holder · bank ·
  primary yes/no — never the IBAN, which only ever arrives masked; contact name ·
  relationship if stated)
- Schwerpunkt-No-Gos recorded (Schwerpunkt · on the person's Contact · portal-only effect)
- bAV-Versorgungsträger, when the list was touched (tenant-wide · provider names · that
  Ziffer 9.11 now renders / stays omitted)
- Top placement opportunities (Client · ID · distance · match rationale)
- Created prospecting tasks (title · due date · assignee)
- Invitation result (first invite sent / login link resent / blocked, with the reason)
- Go-live date, when one was set or already applies (value · per-employee override vs
  tenant default)
- Conversation opened in the Mitarbeiter-App, when one was sent (employee · subject ·
  ticket reference)

## Related skills
- `→ bench-check` — the new employee appears on the bench until placed.
- `→ match-bench-to-clients` — actively match the employee to clients with a Rahmenvertrag.
- `→ profilvertrieb` — pitch the profile to nearby target companies.
- `→ approve-stundenfreigabe` — what the go-live date does to the employee's approvable
  Abrechnungszeiträume.
- `→ clean-inbox` — the inbox side of a conversation opened in step 7: where the employee's
  answer arrives and how it gets triaged and closed.
