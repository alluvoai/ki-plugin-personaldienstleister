---
name: record-absence
description: Record a Krankmeldung, Urlaub, unpaid Abwesenheit, or AU-Bescheinigung for an employee, and check the remaining Urlaub balance before booking vacation. Use when the operator says "Krankmeldung eintragen", "Urlaub buchen", "AU-Bescheinigung hochladen", "AU in die Personalakte legen", "Abwesenheit erfassen", "wie viel Resturlaub hat", "Urlaubsanspruch prüfen", "record sick leave", "log absence", "employee is off sick", "how many vacation days are left", or wants to create or update an absence period.
---

# Record-Absence (Record Abwesenheit & Krankmeldung)

## Purpose

Create or update an Abwesenheit (AbsencePeriod) for an employee — Krankmeldung (AU), Urlaub, Sonderurlaub, or unpaid absence. Includes AU-Bescheinigung fields (required / received, submission deadline). When the certificate itself arrived as a ticket or email attachment, it can be filed into the employee's personnel record in the same run (step 7). The absence may affect the employee's Dienstplan and availability.

> **MUTATING.** Creates/updates an AbsencePeriod (and, in step 7, an EmployeeDocument);
> always two-stage — preview (`confirmed: false`) → operator approval → `confirmed: true`.

## Prerequisites

- Employee ID (`0-2`) known or resolvable via `search-model`.
- Period (start–end) and absence type provided by the operator.
- Exclusively via `mcp__alluvo__*`.

## Steps

### 1. Resolve the AbsencePeriod Model Type + Absence Type

Call `list-model-types` and determine the `model_type` value for `AbsencePeriod` (do not guess — read the value from the API). Then inspect the schema with `get-model-schema` to know all available fields and enum options.

The absence kind is a foreign key, `absence_type_id`, not a free enum — resolve it first via
`search-model`/`list-model-types` on `AbsenceType` (`0-14`, read-only) to find the right id for
Krankmeldung / Urlaub / Sonderurlaub / unpaid, rather than guessing a value.

The row also carries `requires_immediate_call` — whether recording this type asks the employee to
phone the absence in (see *The employee is asked to phone a Krankmeldung in*, below). Read it here
when it matters; `0-14` is read-only, so you can never set it.

**The catalogue tells you which row to pick — read it.** Every `0-14` row carries two text
columns written for exactly this decision:

- `description` — what the type means, for humans. Show it to the operator when you name the type
  you picked, and when you ask them to choose between two similar rows.
- `ai_instructions` — guidance addressed to *you*: when to pick this row and when not to. Where a
  row has it, **follow it** — it outranks your own reading of the label.

`search-model` on `0-14` returns both columns automatically as long as you do **not** pass a
`fields` list. If you do pass `fields`, name `description` and `ai_instructions` in it explicitly,
or you will choose blind. `get-model-schema` on AbsencePeriod (`0-13`, `context: "create"` /
`"update"`) flags `absence_type_id` with the same pointer.

This matters because **several rows share a `key`, so the label alone does not disambiguate**.
Seeded examples where the wrong pick is a compliance error:

- *Beschäftigungsverbot (generell)* — employer- or authority-imposed ban (§§ 11/12 MuSchG,
  § 31 IfSG), **no** Attest required — versus *Beschäftigungsverbot (individuell)* — a doctor's
  individual ban (§ 16 MuSchG), Attest **required**. If the operator mentions an Attest, it is the
  individual variant; if they mention neither, ask before picking the individual one.
- *Krank bei Eintritt (Wartezeit, § 3 Abs. 3 EFZG)* — sickness inside the first four weeks of
  employment, where the employer owes no Entgeltfortzahlung yet. After that waiting period, use
  the regular Krankmeldung type.

A row may legitimately have neither column filled — then decide from `label`, `key`,
`medical_certificate_requirement` and the operator's wording, and say what you based it on. Both
columns are read-only over MCP (`0-14` is not manageable); operators edit them in the UI under
*Einstellungen → Abwesenheitsarten* ("Description" / "AI Instructions"), the same screen as
"Requires an immediate phone call".

### 2. Identify the Employee

If not already provided: use `search-model` with `model_type: "0-2"` by name or personnel number. Confirm the employee with name + ID.

### 3. Check Existing Absences

Use `query-model` for AbsencePeriod with filter `employee_id` + period → check whether a new absence overlaps with existing entries. Report any overlaps to the operator.

### 4. Check the Urlaub balance (vacation only)

Before booking **Urlaub**, read the employee's remaining entitlement — never book vacation
blind. Call `manage-employee-availability` with `action: "vacation-balance"`, `employee_id`
(required for this action), and `year` (optional — defaults to the current year in the tenant
timezone; pass it explicitly when the absence falls into next year).

Returns, for that year:

| Field | Meaning |
|---|---|
| `entitlement` | Days entitled — the agreed value on the Salary, or the Tarifwerk floor (incl. GVP seniority tiers) when none is agreed |
| `tariff_entitlement` | The Tarifwerk figure alone, so an agreed value above it reads as "+N above tariff" |
| `approved` | Days already approved |
| `pending` | Days submitted but not yet approved |
| `remaining` | `entitlement` − `approved` |

Rules for reading it:

- **`remaining` does not subtract `pending`.** When `pending > 0`, say so — approving those
  days reduces the balance further.
- **`null` means unknown, never 0.** `entitlement` / `remaining` come back `null` when they
  genuinely cannot be resolved (no Salary record for that year, no Tarifwerk coverage). Do not
  treat that as a zero balance or a deficit — report it as unknown and let the operator decide.
- **Days are working days minus public holidays**, not the calendar span — a two-week holiday
  costs 10 days, not 14. Size the request the same way before comparing it against `remaining`.
  **Which holidays count follows the employee's Einsatzort, resolved per day** (the `site`
  Address of the Einsatzbetrieb they are placed at that day — never their home address). So two
  employees taking the identical dates can legitimately consume a different number of days, and
  an employee who moved between Einsätze mid-year can have holidays from two Bundesländer in one
  year. Where the Einsatzort has no resolvable Bundesland only the nine nationwide holidays are
  deducted, which understates the count — that address shows up as an `Unresolvable Federal
  State` issue (`→ triage-data-quality`), fixable with `manage-address` `action: "correct"` on
  the ClientSite (`model_type: "0-341"`). Never explain a surprising figure by recomputing it
  yourself; report what the tool returned.
- The figure comes from the same service the employee's own PWA shows, so never recompute a
  balance from raw AbsencePeriod rows — the two would drift.

If the requested Urlaub exceeds `remaining`, do **not** book it silently: show the balance and
the overrun and ask the operator to confirm or shorten the request.

Skip this step for Krankmeldung, AU, and unpaid absence — they do not consume vacation days.

### 5. Create Absence — Preview

Use `manage-model` with the AbsencePeriod `model_type` and `confirmed: false`. Populate the relevant fields (taken from `get-model-schema`):

- `absence_type_id` (resolved in step 1 — Krankmeldung / Urlaub / Sonderurlaub / Unbezahlt or similar)
- `starts_at` / `ends_at`
- **AU-Bescheinigung fields** (only for Krankmeldung):
  - `medical_certificate_required` — is a certificate required for this absence?
  - `medical_certificate_received` / `medical_certificate_received_at` — has it arrived, and when
  - `medical_certificate_due_at` — submission deadline

  The read-only `medical_certificate_status` derives from these: `not_required` /
  `outstanding` / `overdue` / `received`.

Show the preview to the operator. Name the absence type by its `label` **and** its `description`
(step 1) — the operator confirms the type, not an id, and two rows can share a `key`.

### 6. Confirm

Use `manage-model` with `confirmed: true`. Output the newly created AbsencePeriod with its ID.

#### Approving or rejecting a submitted Abwesenheit

An absence an employee submitted themselves is decided with record actions on the AbsencePeriod
(`0-13`) via `manage-record-action`, not by writing `status` directly:

| Action | Notes |
|---|---|
| `approve` | Allowed from `draft`, `submitted` and `pending`. Returns `affected_shifts` — see *Approving is not the last step* below. |
| `reject` | Allowed from `submitted` and `pending`; takes an **optional** `reason`, stored as `review_note` and shown to the employee. |
| `request-revision` | Sends it back for correction; the reason is **required** — the employee is notified and can resubmit. |

`approve` and `reject` are the only two actions in alluvo that can also be clicked from **Slack**:
a workflow's `send_slack_message` action with `record_actions` posts the request with real
Approve/Reject buttons (`→ build-automation-agent`, *Slack delivery*). Two things to say when an
operator asks for that: the click runs as the *clicking* Slack user under their own permissions
(an unmapped or unauthorized clicker is refused and nothing is written), and a Slack `reject`
carries **no** reason — `review_note` stays empty, so the employee gets no explanation. When the
rejection reason matters, or when the right answer is `request-revision`, decide it here rather
than on a button.

#### Automating around an Abwesenheit — trigger on the action, branch on the surface

Two things a `→ build-automation-agent` workflow can do on AbsencePeriod (`0-13`) that it cannot
do on other models:

- **Trigger on the action itself (`trigger_event: "action_performed"`).** All six actions —
  `submit`, `approve`, `reject`, `request-revision`, `cancel`, `reset-to-draft` — are legal
  trigger keys, e.g. `trigger_config: {"actions": ["approve", "reject"]}`. AbsencePeriod is
  currently the **only** model where this trigger works at all, so this is the one place to
  prefer it over `field_changed` on `status`: a Slack post then carries
  `Aktion „Genehmigen" ausgeführt von <Name>` in its footer and `{{trigger.action}}` in its text,
  which is the only way a reader tells an approval from a rejection — both reach a status-based
  workflow identically.
- **Branch on where the absence came from.** An absence the employee filed in the
  **Mitarbeiter-App** carries `record_source = external_panel`. Every other path still writes
  `manual` — an operator entering it in the backend, this skill over MCP, or the web
  Mitarbeiter-Portal. So use a condition `record_source equals external_panel` for "nur
  Selbstmeldungen aus der App", and don't treat an app-filed absence as `manual`; it is not.

#### Approving is not the last step — it hands you a list of uncovered Schichten

Approving an Abwesenheit moves every Schicht it covers to the status **`replacement_needed`**: the
Schicht still exists, still occupies the client's slot and still shows in their Dienstplan — only
the assigned employee cannot work it. Approval is **never blocked** by them; a Krankmeldung is a
fact, not a request the roster gets to veto. But the approval is the moment the gap becomes known,
so do not stop at "genehmigt".

- **The `approve` response carries `affected_shifts`** — one row per Schicht with `shift_id`,
  `assignment_id`, `company_name`, `date`, `start`, `end`. Relay the list to the operator, grouped
  by client, and then for each distinct `assignment_id` offer the Umbesetzung (`reassign_shifts` on
  that Assignment — step 9 and `→ build-dienstplan`, step 6c). Cancel a Schicht only when no
  replacement can be found: cancelling notifies the client that the slot is simply gone, while an
  Umbesetzung sends a § 12 AÜG Konkretisierung naming who comes instead.
- **The `confirmed: false` preview returns it too.** The preview invokes the action's own
  write-free preview machinery, so the same `affected_shifts` list renders under
  **`## Action Preview`** — nothing is approved yet. "Preview first to see which Schichten
  are affected" is a real option: use it when the operator wants to see the gaps before
  deciding on the approval itself.
- **`execute_bulk` throws the list away.** The bulk path prints only executed / previewed / skipped
  / failed per record — no response data at all. So a bulk approval of imported zvoove Urlaube silently discards
  every `affected_shifts`. Where the shifts matter, approve those absences **one at a time**; after
  a bulk run, recover the gaps from the Issues below. The response list is also capped at **20**
  rows with an "N more" note, so a long absence needs the same fallback.
- **Schichten that were actually worked are left alone.** What decides is tracked time, not the
  calendar: a Schicht with a matched `TimeEntry` stays `planned` even when the absence covers its
  day. That is what stops an AU handed in on Friday from retroactively unmaking Monday's hours. A
  past Schicht with no tracked time *was* a no-show and does get marked.
- **A marked Schicht that already lies in the past is a dead end — say so instead of offering a
  fix.** A backdated Krankmeldung routinely marks days that have already passed, and those
  Schichten can be neither umbesetzt (the Umbesetzung blocks them as `shift_already_started`) nor
  cancelled (`remove-shift` refuses a started or past Schicht — a hard block no flag releases,
  `→ build-dienstplan`, step 6). They therefore stay `replacement_needed` permanently and keep the
  Einsatz's Issue open. That is the correct record of a shift nobody worked, not something to
  repair: **dismiss** the Issue where the operator accepts the gap (`→ triage-data-quality`), and
  offer the Umbesetzung only for the days still ahead. **The dead end is yours, not the
  employee's, though:** on a day that is still open (no Tagesabschluss, no Kundenfreigabe) they can
  cancel the Schicht themselves from the Zeiterfassung („Dienst entfällt“) — where they are
  reachable, that is the cleaner record, so ask before you dismiss.
- **Already-reassigned or already-cancelled Schichten are never rewritten.** Those two states are
  terminal — a client-facing document has gone out on them. Cancelling the Krankmeldung afterwards
  does not restore them.
- **The gap is tracked as an Issue on the Einsatz.** Every Assignment left with uncovered Schichten
  raises `App\Issues\Staffing\Assignment\UncoveredShiftsDuringAbsence` (category `staffing`,
  severity `high`) — **one per Einsatz, not per Schicht**. It closes itself once the last uncovered
  Schicht is reassigned or cancelled; nobody ticks it off — though not instantly: the re-check runs
  on the nightly sweep, so an Issue still open right after an Umbesetzung is expected. That Issue is
  the reliable way to find gaps you did not see in an `approve` response
  (`→ triage-data-quality`).

#### A declared Krankmeldung becomes a Bemerkung on the client's signed document

A Krankmeldung reaches the Stundennachweis **as soon as it is submitted — approval is not the
gate**. Every day covered by a declared absence (`submitted`, `pending`, `needs_revision` or
`approved`; not a never-submitted `draft`, not `rejected`, not `cancelled`) in one of the three
incapacity categories — `SICK_LEAVE`, `SICK_LEAVE_WITHOUT_PAY`, `CHILD_CARE` — prints the
Bemerkung **"Krank"** on the Tätigkeitsnachweis, the § 17c AÜG sheet the Entleiher signs
(`→ approve-stundenfreigabe`) — **wherever the sheet prints absence days at all**, see the first
bullet. Six things to hold on to:

- **By default the client never sees the day.** `taetigkeitsnachweis_show_absence_days` is a
  tenant setting (per client company overridable) and it is **off** out of the box: a day the
  employee was absent on with nothing tracked is dropped from the document entirely, "Krank"
  label and all. The Entleiher confirms the hours worked at their site, and an absence row
  discloses a health fact they have no business knowing. So the rest of this section describes
  the row *when a tenant or client has switched that on* (`→ approve-stundenfreigabe` for the
  key and the wording to use before switching it on for someone). A day that still carries
  tracked hours is never dropped either way.

- **Attendance now, pay later — keep the two apart.** On submission the day stops counting as a
  deviation (no week pushed into `mediation` over an unapproved Krankmeldung), owes no Tagesabschluss, and
  prints "Krank"; whether the day is **paid** is still decided by the absence's own approval flow
  and payroll. So "die Krankmeldung ist noch nicht genehmigt" is never the explanation for a gap
  on the Nachweis any more — but it is still the correct answer to a pay question.
- **All three collapse to that one word on purpose.** The sheet documents attendance, not the wage
  type, and "Kind krank" does not belong on a document the client reads. It is not a labelling bug
  and there is nothing to correct.
- **The excusal only covers days with nothing tracked.** Where the employee worked, a real Über-/
  Unterschreitung stands, and a late Krankmeldung does not zero it.
- **A manual day note is appended, not replaced** ("Krank · AU liegt vor ab 03.08."), so an
  operator note on that day still reaches the client.
- **The label is derived when the PDF is generated**, from the absences overlapping the period — it
  is not stored on the timesheet day, so it cannot be edited there. Where the document is already
  issued and signed, the correction path is the Stundenklärung
  (`→ approve-stundenfreigabe`), not the absence record.

**Every absence transition rebuilds the affected weeks automatically.** Creating, approving,
rejecting or deleting an AbsencePeriod re-derives the overlapping Stundennachweis-Wochen still
`open` — **including the ones already in the trash**, which is how a rejection brings a whole-period
Krankmeldung's week back — whether or not they have gone to the client, in both directions: a
submitted Krankmeldung
clears a deviation already stored on the week, a **rejection or cancellation makes it reappear**.
Weeks that have moved on (`pending_employee`, `mediation`, `approved`, `invoiced`) are
deliberately never rewritten, so a week already in `mediation` when the Krankmeldung was recorded is
**not** repaired by approving it now — that one is settled in the Stundenklärung
(`→ approve-stundenfreigabe`), and offering anything else overpromises.

> **A Krankmeldung covering the whole period REMOVES it — and a rejection brings the same record
> back.** When **every** planned day of a Stundennachweis-Zeitraum is covered by a declared absence,
> nothing in it can be released by anybody, so the period is **soft-deleted** — it goes to the
> trash, it is not parked in a status. Say it that way: *der Zeitraum ist nicht geschlossen, er ist
> weg — und er kommt von selbst zurück.* It is automatic — there is no MCP write and no action for
> it — and rejecting or cancelling that Krankmeldung **restores the very same row**, same id, same
> days, same history, with its deviation back. Three things to say
> correctly when an operator asks: the period **keeps its Soll** (an all-sick week shows its planned
> hours against 0,00 h Ist — never read Soll 0 as the marker); it is gone from the list, the board,
> the queues, the deadlines and the client portal all at once, findable with `search-model` on
> `0-426` and `trashed: "only"`; and never offer a manual restore (`delete-model` with
> `action: "restore"`) as the fix — reject the Krankmeldung or plan a Schicht back in and alluvo
> does it. Full rule in
> `→ approve-stundenfreigabe`. A period that already carries a confirmation, a Freigabe or an open
> Korrektur is never removed, however completely the absence covers it. **A day the employee
> actually tracked always keeps its period alive**, even under a Krankmeldung — hours worked despite
> an absence record still have to be released and billed.

**Within a week that does get rebuilt, days a human already decided are frozen** — a day the
client signed, and equally a day someone edited (an accepted Korrektur, a portal edit of the agreed
times). The client can
now release a period day by day (Teilfreigabe), so an `open` week already with the client may hold
both, and the
rebuild touches only its still-open days. A Krankmeldung landing after the client signed that day
therefore changes nothing on it; reopening it needs an operator to revoke that day's release
(`→ approve-stundenfreigabe`).

### The employee is asked to phone a Krankmeldung in

An absence whose AbsenceType carries `requires_immediate_call` makes the employee's app show an
extra step after the record exists: *also phone this in*. Two independent blocks — the agency's
office number, and the on-site contact of the shift the absence covers. Either can be missing; if
both are, no step is shown at all.

**It fires for absences you record, too.** The prompt is not limited to the employee's own
submission — their absence list rebuilds it for every flagged absence that has not yet ended
(`ends_at` today or later), whoever created it. So a Krankmeldung you enter on Monday for a period
running to Friday still asks that employee to call. Say so when the operator is recording it
*because* the employee already phoned in: the app will ask again, and that is expected.

**The duty is per record, not per key.** The flag was backfilled to `true` for every type keyed
`SICK_LEAVE` or `SICK_LEAVE_WITHOUT_PAY`. On a tenant whose "Kind krank" row is keyed
`SICK_LEAVE_WITHOUT_PAY`, that row is now flagged too — usually not wanted, since the call duty is
about the employee's own incapacity. **You cannot change it from here:** `0-14` is read-only
reference data, so `manage-model` create/update is rejected. Toggling it is a UI job —
*Einstellungen → Abwesenheitsarten*, "Requires an immediate phone call".

**The office number is a waterfall, not a single field.** It resolves in the order configured in
`employee_app.employee_phone_priority` — by default `branch` (the employee's Niederlassung phone) →
`employee_hotline` (`general.company_employee_phone`) → `company` (`general.company_phone`); the
first source carrying a number wins, unknown entries are skipped.

The two hotline numbers and the order are readable and writable over `manage-settings`: the numbers
on the `general` group, the order on the `employee_app` group (added for this — alluvo#3349). The
**first** source is not a setting at all — `branch` reads the `phone` of the employee's own
Niederlassung record, which is now reachable over `manage-model` (`model_type: "0-73"`): read it
with `get-model` / `search-model`, fill it with an `update` (two-stage, `confirmed: false` first).
Reading first is worth it, because the usual reason nothing resolves is simply that every source is
empty:

```
manage-settings(group: "employee_app", action: "get")
manage-settings(group: "general", action: "update", fields: { "company_employee_phone": "+49 202 1234567" })
get-model(model_type: "0-73", id: <branch id>)   # the branch phone, first in the waterfall
```

Setting the order alone changes nothing until at least one number is filled in. *Einstellungen →
Employee-App* additionally lists every source with its current value, which makes an empty waterfall
obvious at a glance. The priority is tenant-wide — unlike `go_live_date` it has no per-employee
override.

**The on-site block goes missing more often than you would expect.** It resolves the Einsatz's own
Ansprechpartner → the AssignmentContract's "Fachlicher Ansprechpartner" → the contract's first
contact, and is then **dropped entirely unless that contact has a `phone` or `mobile`** — a name
without a number is useless on a screen whose only job is to get a call placed. So an Einsatz with
no contact, or one whose contact was never given a number, silently produces no on-site tile. When
an operator asks why a sick employee was not told whom to call on site, check the Einsatz's contact
and its phone number first — that is a data gap to close, not a defect
(`→ enrich-contacts-from-activities`). The shift named on the tile is the first one anywhere in the
absence period, not necessarily its first day; where the roster does not reach that far, the
running Einsatz is used and no shift line is shown.

### 7. File the AU-Bescheinigung itself (when the file is already in alluvo)

The `certificate_*` fields above are **metadata** — they record that a certificate exists,
not the document. When the AU-Bescheinigung actually arrived as a file (an employee
photographing it into a shared inbox is the normal case), file it into the employee's
personnel record as well:

- `manage-employee-document` `action: "list-types"` (optionally
  `applicable_to_employee_id: <employee>`, or `category`) → pick the `type_code`. Codes are
  tenant-specific; read them, don't guess.
- `action: "create"` with `employee_id`, `type_code`, `from_attachment_id` — the numeric
  attachment id from the 📎 line in `manage-ticket` `action: "get"` — and
  `from_attachment_source: "ticket"` (use `"email"` for an attachment on a personal-inbox
  Email). Add `valid_from` / `valid_until` from the certified period. The bytes are copied
  server-side; you never move them through the conversation.
- Two-stage as everywhere else: omit `confirmed` for the preview (it names the attachment it
  will copy), show it to the operator, then repeat with `confirmed: true`.

`from_attachment_id`, `file_url` and `file_base64` are **mutually exclusive** — pass exactly
one. Prefer `from_attachment_id` whenever the file is already in alluvo: a ticket attachment
has no fetchable URL for `file_url`, and `get-attachment` returns an image for viewing
rather than as base64 you could pass to `file_base64`, so for a photographed certificate it
is the only path that works. You can only file an attachment you are allowed to read —
access is checked against the parent ticket's inbox membership (or the Email view
permission), exactly as `get-attachment` does.

**When the certificate is a file on the operator's own machine** (handed over on paper and
scanned, or mailed to a private address) there is no `attachment_id` to copy — route it
through a temporary vault rather than reaching for `file_base64`, which is impractical for a
real scan (a 4 MB PDF is ~5.5 MB of base64 through the conversation): `manage-temp-vault`
`action: "create"` (plain vault, no `slots`) → hand the operator the returned **browser
upload link** so they upload it themselves → `action: "get"` with the `token` to read the
file's public URL → pass it verbatim as `file_url` on `manage-employee-document`
`action: "create"` → `action: "delete"` on the vault once the document shows the copied file.
The vault takes JPEG/PNG/WebP **and PDF** up to 30 MB; its URL comes from the app's public
disk (S3 in production), so read it back from the tool instead of constructing it. Delete
promptly — a vault is transit, and an AU-Bescheinigung on a world-readable URL must not be
left to idle out its TTL. Details: `→ clean-inbox`.

Only file what the operator has actually seen. A blurred or partial photo is a follow-up
with the employee, not a document in the personnel file — and it never justifies flipping
`medical_certificate_received` to true.

### Pre-go-live AUs — you see them, the employee does not

Where the employee has an alluvo go-live date (`→ approve-stundenfreigabe`, *the go-live
cutoff*), an AU whose submission deadline fell before it is suppressed in the employee's app
entirely: no overdue badge, no deadline line, no upload button, and no automatic reminder
mail. Your view is deliberately unfiltered — the AU-überfällig list in the app and any
`query-model` / `search-model` on AbsencePeriod keep showing `medical_certificate_status:
overdue`. So "the employee says their app shows nothing to upload" is expected for a
migrated absence, not a bug. Nothing is written by the cutoff; moving the go-live back
restores the request. If the certificate genuinely still matters, collect it directly
(step 7) — the employee will not be prompted for it.

### 8. Note Impact on Dienstplan

Inform the operator: an absence in this period may affect existing Schichten in the Dienstplan. If Schichten exist → recommendation: call `build-dienstplan` or review Schichten manually. The employee's availability changes automatically in the system.

Two things to state plainly when Schichten in the absence window are affected:

- **A Schicht that has already started cannot be removed any more — by you.** Editing,
  cancelling or deleting a Schicht is hard-blocked on the operator path from the moment its
  start time passes (and for any day before today) — a Krankmeldung recorded mid-shift does not
  retro-clear that day from the plan. (The employee's own Zeiterfassung is the exception: on a
  day still open they can cancel it themselves, `→ build-dienstplan`, step 6.) Only the
  Schichten still ahead can be cancelled by you; the hours already underway are
  corrected in time tracking (`→ approve-stundenfreigabe`), never in the Dienstplan — and only
  while the day is not yet released or approved. A released/approved `TimeEntry` is locked for
  everyone; a closed day is corrected via the day-correction flow
  (`→ approve-stundenfreigabe`, *released or approved hours are locked*).
- **Cancelling on an approved Dienstplan reaches the employee automatically.** If the
  Dienstplan-Periode is already `published`, `locked` or `pending_approval`, cancelling,
  deleting or re-timing Schichten sends the employee a change digest ~15 minutes later
  (AÜG § 11 Abs. 2 Satz 4). That is usually wanted after a Krankmeldung — but announce it,
  and do all the cancellations in one call so the employee gets one notification instead of
  a series. On a `draft` Periode nothing is sent.

### 9. Covering the shifts — Vertretung or Umbesetzung

There are two distinct ways to get the absent employee's Schichten covered, and they are not
interchangeable. Offer the operator the choice; never cancel-and-recreate the Schichten by
hand, which produces neither contract documents nor notifications.

| Situation | Path |
|---|---|
| The employee stays on the Einsatz and someone covers a window (classic Krankheitsvertretung) | `add_replacement` on the AssignmentContract (`0-31`) — adds the cover as a **second** Einsatz and transfers the shifts in that window. Sends no notification by itself; follow up with `send_konkretisierung` (`→ manage-contract-lifecycle`). |
| The shifts move to another employee for good (Umbesetzung) | `reassign_shifts` on the Assignment (`0-401`), two-stage — see `→ build-dienstplan`, step 6c. Derives its own contract handling and sends the employee and client notifications itself. |
| Nobody can take them — the Schichten fall away (ersatzloser Ausfall) | `manage-shift-schedule` `remove-shift` with `cancel: true`. The **last resort**, only after the operator has confirmed no replacement is available: the client loses the slot and gets no Konkretisierung naming a substitute. |

For a short Krankmeldung with a known return date the Vertretung is normally right; for an
open-ended absence, or when the employee will not return to that placement at all, the
Umbesetzung is. Both preview before writing, and both are blocked for any Schicht that has
already started — so only the days still ahead can be covered either way.

Reassigning and cancelling are now **distinguishable after the fact** — the Schicht carries
`reassigned` or `cancelled` rather than both looking like the same stornierte row. Either one
closes the uncovered-shift Issue on the Einsatz; only the Umbesetzung actually keeps the client
staffed.

**No Rahmenvereinbarung is required for either.** A standalone AÜV's own § 11.3 Austauschrecht
covers the Vertretung, and a signed standalone AÜV is umbesetzbar as a Konkretisierung
(`→ build-dienstplan`, step 6c). Never offer "Vertrag stornieren und neu anlegen" as the way to
get a cover onto a contract without a Rahmenvertrag.

**Both run the same Eignungsprüfung.** `add_replacement` no longer skips the checks: role fit
(`#NachUntenGehtImmer` — a higher-qualified role in the same Rollengruppe passes, a lower one
never), Blacklist, active employment and a hard ArbZG limit (>10h/day §3 — the only one) are
**blockers**; a §5 rest gap under 11h comes back as a non-blocking **hint**, so a cover with one
is still eligible. The
Überlassungshöchstdauer (§ 1 Abs. 1b AÜG) and a reported absence / missing availability on the
cover's side are **warnings** that name the flag to set.

Calling `add_replacement`:

```
manage-assignment-contract
  action: "add_replacement"
  assignment_contract_id: <the running AÜV>
  employee_id: <the cover, Z>
  window_start: "YYYY-MM-DD"
  window_end: "YYYY-MM-DD"      (omit for an open-ended cover)
  replacement_reason: "sick" | "vacation" | "other"
  confirmed: false
```

- The contract must be **active** (commissioned/performing/performed) and the tenant needs the
  `sick_replacement` feature — otherwise the call returns the reason and there is nothing to
  retry.
- **The preview is the plan.** `confirmed: false` returns `blockers`, `warnings`,
  `required_acknowledgements`, `effects` and `shift_ids` (the Schichten that would transfer) —
  the same shape the Umbesetzung previews. Read it to the operator verbatim, then repeat with
  `confirmed: true`. A blocker is final: report it and stop.
- **There is no `shifts` parameter.** The cover inherits the replaced employee's Schichten in
  the window **verbatim** — different times for the Vertretung cannot be requested here. If the
  cover needs other hours, create the Vertretung first and then adjust its Schichten via
  `→ build-dienstplan`.
- Only ever set `acknowledge_absence_conflict` / `acknowledge_duration_override` after the
  operator has explicitly agreed — never on your own initiative.
- An **open-ended** cover (no `window_end`) is fine — the Höchstdauer is then checked against
  the shifts actually planned, not projected forward. Set `window_end` as soon as the return
  date is known so the check reflects the real duration.
- The original employee is **never** removed. Follow up with `send_konkretisierung`
  (`assignment_id` = the new Vertretungs-Einsatz) for the client and
  `send_assignment_notification` (same `assignment_id`) for the cover —
  `→ manage-contract-lifecycle`.
- **The cover's §11 Einsatzmitteilung has the same gate as the Vertretung itself.**
  `send_assignment_notification` needs `stage: won` and a contract that has not fallen through
  (`cancelled`/`rejected`) — `performed` passes, and an Einsatz that has already ended can be
  notified as a late notice (Nachtrag). Say the notice is late in that case; do not skip it.

## Output

- Created AbsencePeriod: type · start–end · employee (name + ID)
- For Urlaub: the balance before and after — entitlement · approved · pending · remaining
  (or "unknown" when entitlement could not be resolved)
- AU-Bescheinigung status (`not_required` / `outstanding` / `overdue` / `received`), plus the
  filed document (id + type) when a file was supplied
- Note on affected Schichten in the period (if any) — after an `approve`, the `affected_shifts`
  rows grouped by client, and per Einsatz the offered next step (Umbesetzung / Vertretung /
  ersatzloser Ausfall)
- For a type flagged `requires_immediate_call`: that the employee will still be asked to phone the
  absence in, and — where the Einsatz has no contact with a number — that no on-site number can be
  shown to them
- Recommended follow-up action (adjust Dienstplan, find cover)

## Related skills
- `→ build-dienstplan` — adjust or cancel Schichten affected by the absence, or move them to
  another employee (Umbesetzung, step 6c).
- `→ bench-check` — find available employees to cover the absent employee's shifts.
- `→ approve-stundenfreigabe` — review submitted hours around the absence window.
- `→ clean-inbox` — where a Krankmeldung mail with its certificate attachment usually
  surfaces; it resolves the ticket's Contact to the Employee and can file the attachment.
- `→ build-automation-agent` — build the workflow that posts a submitted Abwesenheit into Slack
  with Approve/Reject buttons, or reminds someone that one is still pending.
- `→ enrich-contacts-from-activities` — fill in the missing phone number on an Einsatz contact so a
  sick employee actually gets an on-site number to call.
- `→ triage-data-quality` — find the `staffing` Issues (`UncoveredShiftsDuringAbsence`) an approval
  raised, when the `affected_shifts` list was never seen (bulk approval, or an absence approved
  elsewhere).
