---
name: head-of-disposition
description: Disposition leadership overview and Disponent coordination — verleihfreie Mitarbeiter, expiring assignments, open Personalbedarfe, Dienstplan-Lücken, Stundenfreigabe backlog, and task delegation to Disponenten. Use this skill when the operator asks "how is utilisation looking", "Dispo-Übersicht", "who is verleihfrei", "auslaufende Einsätze", "offene Bedarfe", "Dienstplan-Lücken", "head of disposition", "disposition overview", "coordinate Disponenten", "unbestätigte Einsatzmitteilungen", "offene Lesebestätigungen". Defaults to the logged-in user; can be broken down per Disponent on request.
---

# Head of Disposition — Disposition Overview & Disponent Coordination

## Purpose

Leadership skill for the Dispositionsleitung: delivers a consolidated situation report
of the entire Disposition operation and coordinates Disponenten. This skill does
**no individual placement** — it reports, prioritises, and delegates to job-skills
(`bench-check`, `match-bench-to-clients`, `build-dienstplan`, etc.).

> **The reporting section (Steps 1–2) is READ-ONLY** — no data is modified.
> The **coordination section (Step 3)** is write: tasks are shown first as a preview
> (`confirmed: false`) and only actually created after explicit confirmation from the
> operator (`confirmed: true`). Only `mcp__alluvo__*` tools — no shell, no file I/O,
> no web.

## Prerequisites

- alluvo MCP server connected (`mcp__alluvo__*`).
- The operator is acting within their tenant.
- By default, the logged-in user is assumed to be the primary Disponent.
  If the report should be broken down per Disponent, the operator must confirm this
  explicitly.

## Steps

### 1. Build situation report (read-only)

Query all five signals in parallel — when uncertain about parameters, call
`get-model-schema` or `list-model-types` first, never guess.

#### 1a. Verleihfreie employees (now and upcoming)

`manage-employee-availability` with `action: unassigned` for the **current month**,
then again for the **following month**. Returns employees without full coverage,
their position, and home location. Cross-reference with expiring contracts (see below).

> **Workforce structure is a grouped `query-model` call, not a page-and-tally.** For a
> headcount cut over the whole workforce — per position, per home location, per `owner_id` —
> call `query-model` on Employee (`0-2`) or Candidate (`0-81`) with
> `aggregate: {function: "count"}` and a top-level `group_by`. This works on both types.
> **It does not answer "wer ist verleihfrei"**: a grouped count sees every employee on
> record and knows nothing about coverage. Use it for the denominator (how the workforce is
> distributed) and keep `manage-employee-availability` as the only source for who is actually
> unassigned.

#### 1b. Expiring assignments (next 30 days)

`query-model` on `AssignmentContract` (model type `0-31`):
- Filter: `status: active`, `valid_until` between today and +30 days.
- Fields: employee ID, company ID, `valid_until`.
- For a breakdown per Disponent, make a **second** call with
  `aggregate: {function: "count"}` and a top-level `group_by: "owner_id"` — an aggregate
  call returns counts per group *instead of* the rows, so it does not replace the row
  query above.

#### 1c. Open Personalbedarfe

`search-model` on `StaffingDemand` (model type `0-415`) — **all** current demand lives here,
however it arrived (operator intake, inbound mail the agent triages, client-portal bookings,
guest profile-page requests, stazzle sync). Open = `status` in `signal` / `qualified` /
`active` (exclude `covered` / `lost` / `cancelled`).

A Disponent moves a demand forward with `manage-record-action` on `0-415` (`qualify`, then
`activate`) and on its matches (`0-416`: `mark_offered`, `accept`, `decline`). `qualify` is
rejected unless `valid_from`, `staffing_role_id` and `client_site_id` (the Einsatzort) are
all set — a demand missing `client_site_id` is the gap to flag, never guess a site among
several. `0-415` is writable via `manage-model` (two-stage: `confirmed: false` preview →
`confirmed: true`), so those gaps can be filled from here; see `intake-personalbedarf`.
`accept` on a match creates a **DRAFT** `AssignmentContract` (`0-31`) only; sending,
approving and signing stay with `manage-contract-lifecycle`.

> **Count Bedarfe, not rows — demands are grouped.** A `0-415` row is one *line*, and several
> lines routinely describe one Bedarf (the same Anfrage re-sent, a Stazzle re-post, or a
> strategic bundle like "10 Pflegekräfte für die neue Station" split per role). Lines are tied
> together by `demand_group_id`, a self-FK: the **anchor** line has it **null** and lists the
> rest under its `children` relation; a child always points straight at an anchor, never at
> another child. A freshly created line folds into an open anchor automatically when it matches
> on company + Abteilung (linked, else the reported text) + Rolle (linked, else the reported
> title) + a period that overlaps or sits within a day of the anchor's. Only **open** demands can
> be anchors, so nothing ever attaches to a covered/lost/cancelled line.
>
> So a raw row count overstates the backlog badly — in production ~334 lines corresponded to ~97
> actual Bedarfe. Report **Bedarfe (anchors)** with the line count beside it. Confirm with
> `get-model-schema` (`context: list`) whether `demand_group_id` and the `children` / parent
> relation are filterable and includable on `0-415` before building the query on them; where they
> are not, read `demand_group_id` off the rows you already fetched and group them yourself rather
> than reporting the row count as the Bedarfszahl.
>
> The proposal drafter dedupes the same way — one auto-draft per group, plus a 7-day safety net
> over the same Kontakt + Rolle + Einsatzort — so a customer no longer gets one mail per
> duplicated line. **A group with several lines and one proposal is correct, not a missed
> demand.**

`StaffingRequirement` (`0-102`) is the **legacy predecessor** — read it only for historical
records and existing outreach/proposal business, and do not add it to the open-demand count.
Reading it via `search-model` / `get-model` / `query-model` is unchanged. `0-415` stays the
only target for **new** demand, but that is now a routing rule rather than a server-side
block: `manage-model` create/update on `0-102` used to be rejected and today **succeeds**, so
a misrouted create quietly produces a legacy record that no `0-415` count or report ever sees.
Updating an existing `0-102` to correct a historical record is fine (two-stage as usual) —
creating new demand there is not.

Matches are queryable **directly**, not only through a demand's `matches` include: run
`search-model` / `query-model` / `get-model` on `0-416` without a parent demand id to answer
cross-demand questions ("every offered match with `score` > 80", "is this employee already
proposed anywhere"). Filterable: `employee_id`, `score`, `outcome`
(`offered` / `accepted` / `declined`), plus the `employee` and `staffingDemand` relationship
filters — confirm with `get-model-schema` (`context: list`) before calling. Readable fields
include `employee_id`, `employee_name`, `staffing_demand_id`, `rank`, `score`, `outcome`,
`matched_at`, `offered_at` and `warning_summary`. It is **read-only**: `manage-model` writes
are rejected, and offer/accept/decline stay on `manage-record-action`. Needs the
`staffing_demand_matches.view` permission — an operator without it sees nothing here.

> **Abteilung on a `0-415` demand: read the relation *and* the text.** Besides
> `company_department_id` (relation to `CompanyDepartment` `0-107`), a demand carries
> `company_department_text` — the Abteilung as the inbound source reported it ("Gemeldete
> Abteilung"). Inbound integrations no longer create Abteilungs-Stammdaten, so a
> machine-channel demand commonly has **no** linked department while the name lives in the
> text field. Summarise it as `company_department_id` → fallback `company_department_text`,
> and do not count an unlinked Abteilung as a data gap or a blocker — unlike a missing
> `client_site_id`, it blocks neither `qualify` nor matching (the matcher applies the same
> fallback).
>
> **Automatic matching is off — do not manage against a shortlist that is not produced.**
> The autonomous pipeline sits behind the Pennant flag `AutomaticDemandMatching`, **off by
> default per tenant** (it proposed candidates who had reported themselves unavailable and
> missed the fachlich right person by ignoring higher, neighbouring roles). While it is off, a
> demand generates **no** `0-416` match rows, **no** "Personalbedarf prüfen" task, **no**
> "Anschlusseinsatz prüfen" task, **no** auto-drafted proposal email and no Slack shortlist
> reply — and nothing flips a demand to `NotCoverable`, so demand sitting at `Qualified` is
> un-worked, not un-coverable.
>
> Two consequences for how you read the team's work:
> - **Never count "Personalbedarf prüfen" tasks as the demand backlog.** The backlog is open
>   `0-415` demand itself — query that. A Disponent with no such tasks is not idle.
> - **"No matches" is not a coverage verdict.** Judge a demand by whether someone *searched*,
>   via `→ match-bench-to-clients` / `→ bench-check`, `0-126`
>   (EmployeeStaffingOpportunity — **not** gated), or the operator-driven matching workspace
>   (`/staffing/matching`, `/staffing/company-matching`, also not gated: same scoring engine,
>   run on a human's request). Ask for the search, not for the shortlist.
>
> The rest of this section describes match rows that **do** exist — demands worked before the
> shutdown, or a tenant with the flag switched back on. Read the record, don't assume either way.
>
> **How a `StaffingDemandMatch` (`0-416`) got there — read `score` correctly.** Every
> candidate is gated and scored by the shared matching engine *before* the AI ranker sees
> anyone: employment window → **Freistellung** → role/qualification → availability →
> eligibility, blacklist, **Sektor**, role-fit floor and travel radius. `score` is that
> **deterministic fit score, 0–100** (role 0.35 · experience 0.25 · sector 0.20 ·
> distance 0.15 · compensation 0.05 · **availability 0.05**) — **not** the AI's confidence.
> The AI only contributes `rank` and the `note` reasoning; `warnings` carries the
> AÜG/Verlängerungs-Hinweise. So a proposal on the list has already passed the hard gates —
> do not re-argue radius, blacklist, Sektor or role level; judge fit and availability.
>
> Three things shape how *many* matches you see, in this order — a short or empty list is a
> verdict, not just a cap:
> - **Hard Sektor gate.** Where the employee **and** the client both state a Sektor and share
>   none, the pair is rejected outright rather than losing the 0.20 sector weight. Fails open
>   when either side's Sektor is unknown — so a surprising cross-Sektor absence is usually a
>   Sektor-Stammdaten gap on the employee, not a matching bug.
> - **Minimum score 25.** Candidates who cleared every gate but scored below 25 are dropped
>   and reported in the reason breakdown as *below_min_score*. A demand whose only eligible
>   person is a weak fit now produces **no** proposal instead of proposing them alone. Read
>   "keine Vorschläge" accordingly: the pool was not necessarily empty.
> - **Shortlist cap, default 10**, applied *after* the floor — so a strong candidate is never
>   dropped in favour of a weak one.
>
> Two scoring details worth knowing when a Disponent questions a ranking:
> - **Fachweiterbildung counts on this path.** A demand's required role carries its
>   `specialty` (Intensiv, Anästhesie, Notfall, …) into the score, so a same-Gruppe,
>   same-Level candidate with the *wrong* specialty scores **0.4** on the role feature rather
>   than 1.0, and a covering specialty bridges across Gruppen at 0.5. It is a downgrade, never
>   an exclusion — a 0.4 candidate is still worth a look, just not a silent "exakter Treffer".
>   (A demand naming several roles of one Gruppe with different specialties imposes no
>   specialty constraint for that Gruppe.)
> - **Gemeldete Verfügbarkeit is a bonus, not a filter.** An employee who reported still-free
>   availability overlapping the demand window gains the 0.05 availability weight; **not**
>   reporting anything leaves the feature inactive and never costs points. Never read a low
>   score as "hat keine Verfügbarkeit gemeldet".
>
> **Freistellung excludes.** An employee whose current EmploymentPeriod has
> `duties_suspended_at` on or before today is out of automated matching entirely — the same
> rule the client portal applies. They appear in no shortlist by design.
>
> Matches showing `offered_at` + `proposal_email_id` were not necessarily offered by a
> Disponent: where a matching run happened, about 15 minutes after it the system auto-drafts
> one candidate-proposal email for the shortlist (skipped if an operator offered first) and
> parks it as an
> approval-gated run for the demand's contact owner — it is never sent without approval.
> A demand missing its contact or Einsatzort gets a blocker task instead of a draft. When
> reviewing a Disponent's open demand, "proposal drafted, awaiting approval" is therefore a
> normal in-flight state, not a stalled case — the pending approval is the action item.
>
> Where a matching run produced **no** proposal, its "Personalbedarf prüfen" task (and the Slack
> thread) names the reason breakdown against the employed-in-the-window base:
> *ohne passende Qualifikation* / *im Zeitraum nicht verfügbar* / *außerhalb des
> Einsatzradius oder ohne erreichbaren Einsatzort/Adresse* / *below_min_score* (cleared every
> gate, scored under 25 — see above). A high radius count is an Einsatzort/Adress-Datenproblem
> (missing geocoded client site or Contact home location), not a "no staff" problem — flag it
> as such; a high *below_min_score* count is the opposite signal, "people are reachable but
> nobody fits well". A demand with no Einsatzrolle gets a different message ("keine
> Einsatzrolle zugeordnet") — that is a data gap to fix, not a matching result.
>
> **"Anschlusseinsatz prüfen" is a second, separate task — treat it as a priority signal.**
> Alongside "Personalbedarf prüfen", a matching run files a Task (`0-5`) titled
> *"Anschlusseinsatz prüfen: <Bedarf>"* whenever a matched employee is currently verleihfrei or
> their running Einsatz ends within ~14 days. It is attached to the demand (`0-415`) **and** the
> client Company (`0-3`), owned by the demand's creator, priority high, due on the demand's
> `valid_from`. Its body names per employee the situation (verleihfrei / Einsatz bei X endet in
> N Tagen) plus the **Zusatzstunden** and **Zusatzumsatz** a booking would secure, with a
> confidence marker — revenue is omitted where hours or rate are unknown, so an entry without a
> € figure is an honest gap, not a zero. The two tasks answer different questions ("is this the
> right person?" vs. "does booking them close a Bench-Lücke?") and are deliberately closed
> independently; do not treat one as a duplicate of the other. Its **absence** carries no
> signal while automatic matching is off — no run, no task. It overlaps by design with **1a**
> (verleihfrei) and **1b** (auslaufende Einsätze) — where the same employee shows up there *and* on such a task,
> that is the strongest case to work first (`→ match-bench-to-clients`), because one booking
> answers the Bedarf and the Auslastungslücke at once.

For a per-Disponent breakdown use **`query-model`** with `aggregate: {function: "count"}` and
a top-level `group_by` — **not `count-model`**, which accepts only `model_type`,
`filter_groups` and `search` and returns one total. On `0-415` the responsible user is
`creator_id`, not `owner_id`; confirm the groupable fields with `get-model-schema`
(`context: list`) before calling. FK group columns resolve a human label automatically, and
the result is capped at the top 200 groups.

#### 1d. Dienstplan gaps

`query-model` on Schicht entries (Shift — resolve the exact `model_type` via
`list-model-types`; there is no separate "ShiftPlan" model): next 14 days, status
`draft` or `unassigned`. Fields: date, Schicht, missing coverage.

A gap is no longer necessarily a planning omission: employees can cancel (or retime) single
Schichten on their own running Einsatz from the employee app, without an approval round-trip
(`→ build-dienstplan`, step 6b). Before delegating a "close the gap" task, check whether the
Schicht was *cancelled* rather than never planned — a cancelled row means the roster change
was already communicated on site, and the job is coverage, not re-entry.

Since 2026-09-02 that can happen on a day already **underway or past**, not only on future days:
from the Zeiterfassung the employee corrects or cancels the Schicht for as long as the day is
open — no Tagesabschluss of theirs, no Kundenfreigabe. So a change appearing on yesterday is
routine, not a data incident, and it is **backward-looking**: nobody can be sent to cover a day
that has passed. Treat it as a Stundenfreigabe fact (the day's Soll moved,
`→ approve-stundenfreigabe`) rather than a coverage task, and note that your Disponenten cannot
mirror it — `update-shift` still refuses a started or past Schicht for them.

**A month left in Entwurf is a second, quieter gap.** `query-model` on SchedulePeriod (`0-110`)
for `status: draft` on running Einsätze shows the Dienstpläne nobody released. It matters at
your level for one reason: a `draft` Schicht is **not** counted as a conflict when a new Schicht
is planned, so the double-booking and §5-rest guards stay silent — an employee in an unpublished
month can be planned into a second Einsatz without either Disponent being warned. The customer
also sees nothing of that month in the portal. Delegate the release (`→ build-dienstplan`,
step 7); publishing notifies nobody, so it is safe even on a month already worked.

The release can also come back **refused**: an Einsatz may carry only **one live Dienstplan per
date range**, and alluvo will not silently demote the other one to make room. That is a data
question — which of the two plans is the real one — not a task the Disponent closes by retrying,
so expect it back on your desk rather than as a completed release. Filter `0-110` for
`status: superseded` to see plans that were legitimately *replaced* (a client re-submission, a
signed contract's wizard plan going live); those are inert by design and are not a backlog.

#### 1e. Stundenfreigabe backlog

**Count the backlog in Abrechnungszeiträume, not in Kalenderwochen.** Hours are released per
period per Einsatz, and the period is a contract setting — the default `month_segments` cuts a
month into day 1–7, 8–14, 15–21 and 22–end, so no period ever crosses a month boundary and a
period regularly spans parts of two ISO weeks. "KW 32" is not a unit of this backlog: a
Disponent asking about a calendar week may be asking about two periods, or about one segment
that covers only part of it. Periods read as `01.08.–07.08.2026 (KW 31/32)` — quote the date
range, not a week number (`→ approve-stundenfreigabe`).

The month-alignment is the reason this backlog is a leadership number at all: **invoicing and
payroll for a month can run as soon as that month's last segment is approved**, so an
outstanding segment from the 22nd onwards blocks the month's billing, while an outstanding one
from the 8th–14th does not. Rank the backlog by which month it holds up, not by age alone.

> **Count the backlog off the periods themselves — they are queryable now.** `Timesheet` (`0-426`)
> is on the MCP allowlist (read-only), so a backlog figure comes straight from the record rather
> than being rebuilt out of raw time entries: `query-model` on `0-426`, filtered by `status`
> (`open`, `pending_employee`, `mediation`, `approved`, `invoiced` — five values, see below) plus
> `has_deviation`, `date_from` / `date_until`, `deadline_at`, employee or Einsatz — and
> `aggregate: {function: "count"}` + `group_by` for a per-Disponent split in one call. `0-427`
> (Tag) and `0-435` (Freigabe) read the same way; nothing here is writable through `manage-model`
> (`→ approve-stundenfreigabe`). The same list is in the web app under HR & Payroll →
> **Stundennachweise**, with a saved view per status — quote it to a Dispositionsleitung as where
> to look. It **lands on "Alle"**; there is no "Aktiv" tab to explain away.
> If someone cannot see the menu entry, they lack the `timesheets.view` permission.
>
> **`TimesheetStatus` has exactly five values** — `open` (Offen), `pending_employee` (Wartet auf
> Mitarbeiter), `mediation` (In Klärung), `approved` (Freigegeben), `invoiced` (Abgerechnet).
> `closed` ("Ohne Einsatz") was retired one release after it shipped, and
> `upcoming`, `pending_client`, `disputed`, `escalated`, `mediating` and `draft` are **not**
> `TimesheetStatus` values either: a `query-model` filtered on one returns an empty set and a backlog
> figure built that way silently reads zero, with no error to warn you. (Unrelated: the
> Dienstplan-Periode `0-110` still has a real `draft` status — do not "correct" that one.)
>
> **A period with nothing to release is not in your figures at all — no exclusion needed.** Once not
> one of its days can be released by anybody — every Schicht gone, or **every** planned day covered
> by a declared Krankmeldung — the period is either never created or **soft-deleted**, so it is
> absent from the list, the board, the queues, the deadlines and the client portal for free. Do not
> build "exclude the finished ones" logic into a backlog query; there is nothing to exclude. What
> this *does* change is how you read a **shrinking** backlog: periods disappearing from a month is
> a **planning** signal — shifts being cancelled or absence eating the month — not approval
> progress. Take it to an Einsatz review, not to the Stundenfreigabe backlog. Never diagnose it from
> Soll = 0: an all-sick period keeps its Soll (23,10 h Soll against 0,00 h Ist is exactly this
> case). The periods are still there under `search-model` on `0-426` with `trashed: "only"` if you
> need to count them, and they return by themselves when a Schicht is planned back in or the
> Krankmeldung is rejected (`→ approve-stundenfreigabe`).
>
> **`open` is not one bucket but two, and a backlog figure has to choose.** It covers both "the
> period exists, nothing has gone to the client yet" and "submitted, the Frist is running" — the
> distinction lives in the **`submitted_to_client_at`** stamp, not in the status. Filtering on
> `status: open` alone therefore counts running weeks nobody owes anything on together with weeks
> genuinely sitting at a client. Add `submitted_to_client_at` (set / null) to the filter and say
> which of the two you are reporting.
>
> **Three derived reads sit beside it.** The materialised **`lifecycle_phase`** column
> (`upcoming` ▸ `in_approval` ▸ `approved` ▸ `invoiced`, labels Anstehend / In Freigabe /
> Freigegeben / Abgerechnet) is the left-to-right rail — four stations, and note that `upcoming` is
> a valid *phase* and never a status.
> The **awaited party** (`client`, `time_tracking`, `employee`, `mediation`,
> `nobody` — `approved` and `invoiced` yield `nobody`) and the
> **release progress** (`none` / `partial` / `complete`) are derived per request
> and **not stored**, so neither can be filtered or grouped in a `query-model` call — read them off
> the record surface, never promise a report built on them.
>
> **"Wie oft mussten Leute länger bleiben?" is a query now, not a reading exercise.** Since the
> Abweichungsgrund became a category beside the free text, `TimesheetDay` (`0-427`) carries a
> filterable `deviation_reason_code`. `query-model` on `0-427` with
> `aggregate: {function: "count"}` and `group_by: "deviation_reason_code"` gives the whole
> distribution in one call — which is a leadership number, not a curiosity: a rising
> `understaffed` share is a client-side staffing problem, a rising `handover_delayed` share is a
> process one. Five caveats before you report it:
>
> - **The categories are a tenant catalogue, not a fixed list.** They are rows of
>   `ShiftDeviationReason` — this tenant may have added its own and deactivated some of the eight
>   platform defaults (`stayed_longer`, `handover_delayed`, `understaffed`, `left_early`,
>   `sent_home_early`, `started_late`, `break_differs`, `other`). Read the catalogue before you
>   name buckets or label a chart, and resolve the type through `list-model-types` rather than
>   hardcoding its id (`→ approve-stundenfreigabe`). A code your distribution returns that is not
>   in the catalogue is a deactivated or renamed row, not dirty data.
> - **Only days closed since the category shipped carry a code**, so older periods undercount.
>   Bound the range and say so rather than comparing a full quarter against a partial one.
> - **The values are direction-scoped** — `stayed_longer` and `left_early` can never appear on the
>   same day, so they never double-count (`→ approve-stundenfreigabe`).
> - **One whole class of deviating day carries no code at all.** Where the day's *gross* attendance
>   matched the plan and the net delta is nothing but a missing break, the § 4 ArbZG dialog asks
>   the why and the deviation question is suppressed — the day closes with a `no_break_reason` and
>   an empty `deviation_reason_code` despite a non-zero `deviation_minutes`. So the distribution is
>   a distribution of *explained* deviations, not of all of them, and the gap is systematically
>   the "Pause nicht eingetragen" cases. Those reasons live on the closure (`0-422`), which is not
>   on the MCP allowlist — so they cannot be counted here at all. Say the distribution covers coded
>   deviations only; never present the uncoded remainder as unexplained (`→ approve-stundenfreigabe`).
> - **A day carries no Einsatz or company of its own**, only `timesheet_id`. "Welcher
>   Einsatzbetrieb schickt Leute am häufigsten früher nach Hause" is therefore not one call —
>   scope the periods first (`0-426` by Einsatz), then count their days.
>
> **Do not count a partially released period as done, and do not count it as untouched either.**
> A client can sign part of a period (Teilfreigabe), so `client_confirmed_at` on the period is set
> only once **every** day is released. An `open` period sitting with the client may already be
> three-quarters signed — read `Freigegebene Diensttage` against `Diensttage gesamt` before
> reporting it as outstanding work (`→ approve-stundenfreigabe`).

For the hours *underneath* a period — how much was actually tracked — `search-model` on the
time-entry type (`TimeEntry`, resolve via `list-model-types`):
- Filterable: `employee_id`, `assignment_id`, `type` (`work` | `break`), `start` (period).
  There is **no `status` field** on a time entry — approval state lives on a
  `TimeEntryApproval` record with no MCP model type, so `status: submitted` matches nothing.
  Scope by period and read approved-vs-open in the web app.
- Count `type: work` only, and remember that one worked day is several rows (work → break →
  work) — an entry count is not a day count. Group by employee and date for a figure you can
  put in front of a Disponent.
- To quantify the backlog per responsible person, prefer one grouped `query-model` call
  (`aggregate: {function: "count"}` + `group_by`) over a `count-model` loop — `count-model`
  cannot group and would need one call per Disponent.
- **The period the employee is still working is `open` by design — it is not backlog.** A
  `Timesheet` is materialised for the *current*, still-running period too **as soon as it holds a
  releasable day — an effective Schicht nobody is signed off sick for, or a closed time entry**, so
  it sits in any `open` count you take — with
  `submitted_to_client_at` still null, which is exactly how you exclude it. (A
  running period with neither has no row at all yet — see the empty-period bullet below.) The
  employee's own app now says so plainly ("Läuft noch — noch nichts zu
  tun", releasable the day after the period ends), and chasing them for it is chasing them for
  something they cannot do (`→ approve-stundenfreigabe`). Check the period's end date against
  today before it enters a backlog figure — under `month_segments` a segment ending on the 21st
  is only actionable from the 22nd. The *next* period the app previews below it ("Danach: …",
  "Kommt als Nächstes") is only a projection — no `Timesheet`, no Frist, invisible to every
  query you run — so it can never inflate an `open` count, and an employee quoting it is not
  reporting a period you have lost (`→ approve-stundenfreigabe`).
- **A period stuck `open` with nothing signed is often one unclosed day, not a lazy employee.**
  Releasing hours
  now requires the employee to have closed every day being released ("Tag abschließen"); the
  attempt fails naming the open dates (`→ approve-stundenfreigabe`). That is a 30-second fix in
  their app — chase the Tagesabschluss before delegating a full Stundenfreigabe chase. When the
  employee genuinely cannot (gone, unreachable, no device), a Disponent with
  `timesheet_days.close_tracked_day` can close the day for them
  (`close_tracked_day_for_employee` on `0-427`, `→ approve-stundenfreigabe`) — under the same § 4
  and Abweichungs-Prüfungen, and recorded as the agency's declaration rather than the employee's.
  Delegate that as the exception it is, not as the default answer to a slow employee. The
  employee loses the day only once **the client has signed that day**; a period sitting in
  with the client, with the day still open, is still theirs to withdraw and re-close, so do not
  route it to Disposition on the period's status alone (`→ approve-stundenfreigabe`).
  A second, self-inflicted variant blocks the same release: a Disponent edited a *closed*,
  compliant day and pushed its breaks below the § 4 minimum, so the employee is now refused with
  "Pausenzeit nachträglich geändert" and has to withdraw and re-close with a reason. If a
  released-looking period bounces right after someone corrected it, check that first — the fix
  is a conversation with the employee, not another chase.
- **Periods with nothing to release are not a backlog item, and they no longer exist as rows.** A
  period with no releasable day — no effective Schicht, no closed time entry, or every planned day
  covered by a declared Krankmeldung — is never created, and neither is one
  outside its Einsatz's start/end; one that *becomes* so is soft-deleted. So it has no live `0-426`
  record, no Frist, and cannot turn up in
  a count you take (`→ approve-stundenfreigabe`). **A gap in an employee's weeks is therefore an
  answer, not a hole to investigate:** it means nothing was planned, nothing was tracked, or the
  whole period was sick. This
  is what stopped a dead Einsatz — a cancelled contract, a draft never won, an `end_date` that
  outlived its Storno — from announcing weeks at a client the employee never worked at. Don't
  delegate a chase for a period nobody can act on, and don't report the gap as data loss: a
  `Timesheet` is derived, so it reappears — the very same row, id and days intact — the moment a
  Schicht or an entry lands in that period or the Krankmeldung is rejected.
- **Nothing before an employee's alluvo go-live exists either — and unlike before, your count
  now agrees.** A per-employee go-live date (`employee_app.go_live_date`) stops every path from
  materialising a period ending before it, and the unconfirmed pre-cutoff rows already on disk
  were removed in a one-off cleanup, so a `0-426` figure no longer overstates the Zeiträume the
  employee is asked about. **The raw hours underneath are a different story** — a `TimeEntry`
  search still counts pre-go-live time, so an entry-level backlog figure can still overstate it.
  Before delegating a chase against a migrated employee, read their go-live with
  `manage-record-settings` `action: "describe"`, `model_type: "0-2"`
  (`→ approve-stundenfreigabe`). Reporting on hours from before the cutoff: say that alluvo holds
  the Zeiträume from the go-live onwards and the period before it ran in the tenant's previous
  system (zvoove/Landwehr) — that is the bound on the answer, not a gap. The cutoff approves
  nothing and touches no signed, released or invoiced Zeitraum, so never report those periods as
  settled either.

#### 1f. Unbestätigte Einsatzmitteilungen

Einsätze whose §11 Abs. 2 Satz 4 AÜG Einsatzmitteilung the employee has not confirmed.
`search-model` on Assignment (`0-401`), filter
`assignment_notification_acknowledgement_state: pending`. Prioritise by `start_date` — the
deadline is the Einsatzbeginn, so an Einsatz starting tomorrow outranks one four weeks out.

> **Filter the state, never the empty timestamp.** `assignment_notification_acknowledged_at IS
> NULL` is true for `not_requested` just as much as for `pending`, and `not_requested` means
> nobody was ever asked (a send from before the feature, a backfilled snapshot, or the
> requirement switched off for the tenant). A null-filter would hand the Dispositionsleitung the
> whole historical backlog labelled as overdue.

Three things to keep straight before delegating from this list:

- **It is a proof of receipt, not an approval.** Nothing is blocked by a missing confirmation —
  not Schichten, not Zeiterfassung, not the Dienstplan. Report it as a follow-up duty, never as
  a Freigabe-Gate holding up an Einsatz.
- **The system already chases it.** Employees are reminded automatically inside the configured
  window before Einsatzbeginn, and at the escalation threshold a high-priority task is created
  for the **Einsatzvertrag owner** automatically. So this list is mostly a leading indicator —
  only delegate on top of it where no task exists yet, or where the same employee keeps
  recurring (usually no employee-app access or a stale email address, which is a data fix,
  not a nudge). Details → `manage-contract-lifecycle`, step 5a.
- **A migrated employee's old Einsatzmitteilungen are no longer asked about.** Where the
  employee has an alluvo go-live date, an Einsatz whose notification was *sent* before it is
  dropped from their app — but `assignment_notification_acknowledgement_state` still reads
  `pending` in your search, because the cutoff filters the surface, not the data. Check the
  employee's go-live (`→ approve-stundenfreigabe`) before delegating a nudge for a pre-go-live
  Einsatz; the employee has no way to confirm it. Equally, don't record it as confirmed — the
  cutoff stamps no acknowledgement.

If every row reads `not_requested`, the tenant does not have the acknowledgement feature switched
on — say so rather than reporting "no outstanding confirmations".

Responsibility sits on the **Einsatzvertrag**, not the Einsatz, so a per-Disponent breakdown has
to attribute via the contract's owner. Confirm with `get-model-schema` (`context: list`) that the
field is groupable on `0-401` before relying on a grouped `query-model`; otherwise read the rows
and attribute them from the contract.

---

### 2. Disponent matrix (read-only)

Load all Disponenten for the tenant:

`search-model` on `User` (model type `0-1`) with filter `is_active: true`.

Map the metrics from Step 1 to each active Disponent:

| Disponent | Verleihfrei now | Ends ≤ 14 d | Open Bedarfe | Plan gaps | Hours pending | Einsatzmitteilung offen |
|-----------|----------------:|------------:|-------------:|----------:|--------------:|------------------------:|
| ...       | ...             | ...         | ...          | ...       | ...           | ...                     |

Sort descending by urgency (most critical cases first).

---

### 3. Coordination and task assignment (write — preview first)

> Before every write action: show preview with `confirmed: false` and wait for the
> operator's confirmation. Only then execute with `confirmed: true`.
> Never assign tasks to multiple Disponenten simultaneously without the operator
> approving the full plan.
>
> This two-stage gate covers **every** task mutation, whichever tool you reach for —
> `bulk-manage-model` (`confirmed: false` preview → identical call with `confirmed: true`),
> `manage-task`'s `create` / `update`, and the `mark-as-completed` record action via
> `manage-record-action`. None execute on the first call.
> Don't assume an update or bulk edit runs immediately.

A coordination round assigns several tasks at once, so write them in **one**
`bulk-manage-model` call with `model_type: "0-5"` (Task) and one `operations` entry per
task (max 50) — never a loop of single creates. Per `data`: `title`, `body`,
`owner_id: <disponent_id>`, `due_at`, and `attachments: [{type_id, id}, …]`, which takes
several entries of different types so a task points at every record it concerns
(`0-2` Employee, `0-3` Company, `0-110` SchedulePeriod, `0-31` AssignmentContract,
`0-190` Issue). `owner_id` defaults to the authenticated user — set it explicitly only
when delegating.

`due_at` / `reminded_at` / `wait_until` on this path require an ISO datetime **with an
explicit offset** (`2026-07-22T09:00:00+02:00` or `...Z`); `manage-task`'s tenant-local
`Y-m-d H:i` is rejected here. Keep `manage-task` for what the bulk path can't do:
tasks that genuinely repeat (see below) and `ticket_id`.

`manage-task` was trimmed to `create` and `update` only. Its former `bulk-update` is gone —
changing many tasks at once is `bulk-manage-model` on `0-5`, which needs one `operations`
entry per task id rather than the old one-change-set-to-many-`task_ids` shape, so expand the
change set per id. Its former `complete` is gone too: mark a task done with
`manage-record-action` `operation: "execute"`, `model_type: "0-5"`, `record_id: <task_id>`,
`action: "mark-as-completed"` (`operation: "execute_bulk"` with `record_ids` for a batch, max
100). Note attachments are **additive on update** — listing them adds links and
never removes one you left out; there is no MCP path today to detach a task's attachment.

> **The repeat fields now persist on the bulk path — but they do not make a task repeat.**
> `repeat_interval`, `repeat_frequency` and `repeat_until` gained validation rules on `0-5`, so
> `bulk-manage-model` / `manage-model` writes them instead of silently dropping them
> (`repeat_interval` is one of `daily`, `weekday`, `weekly`, `monthly`, `yearly`;
> `repeat_until` needs the same explicit offset as `due_at`). What the generic path still
> cannot set is **`is_repeating`** — it has no rule, so sending it returns it in the write's
> ⚠️ IGNORED FIELDS block — and that flag is what the scheduler filters on when it spawns the
> next instance. A schedule written this way is documentation, not a recurrence. For a
> follow-up that must actually recur, use `manage-task` `action: "create"` with
> `repeat_interval`: it sets `is_repeating` itself and defaults `repeat_frequency` to 1. There
> is **no** MCP path that turns an existing task into a repeating one — `manage-task` `update`
> ignores the repeat fields entirely, and `manage-model` writes the interval without the flag
> (alluvo#4519). Say so rather than reporting a recurring delegation you did not create.

For each Disponent with prioritised cases, formulate an action proposal:

1. **Bench-to-client matching** — `owner_id: <disponent_id>`, title e.g. "Bench-Check +
   Matching: 3 critical employees this week", attached to the affected Employees, and
   reference to skill `match-bench-to-clients`.
2. **Close Dienstplan gaps** — title e.g. "Dienstplan KW XX: 2 gaps early shift",
   attached to the SchedulePeriod, and reference to skill `build-dienstplan`.
3. **Clear Stundenfreigabe backlog** — title e.g. "Stundenfreigabe: 5 pending sheets to
   approve" and reference to skill `approve-stundenfreigabe`.

> **Two period-level actions exist now — delegate them, do not run them off a backlog figure.**
> A period the client will not sign can be released by the agency (`approve_by_operator` on
> `0-426`), and one approved in error can be taken back (`revoke_approval`, only while `Approved`)
> — both operator-only, both `manage-record-action`, both on their own permissions
> (`timesheets.approve_by_operator` / `timesheets.revoke_approval`), granted to no role by default
> (`→ approve-stundenfreigabe`). Neither is a backlog tool: an operator release puts hours on an
> invoice the customer never agreed to and prints a Tätigkeitsnachweis stating that no Entleiher
> confirmation exists, so it belongs to the Disponent who actually agreed the hours with the
> client, case by case. A backlog that shrinks because someone released it without the client is
> not a backlog that was worked. Two facts to hold a report to: `approve_by_operator` demands
> every day be closed first (chase the Tagesabschluss, above), it runs only while the period is
> `open`, and it lands on `pending_employee`
> rather than `Approved` wherever the agreed hours deviate from the tracked ones — so a count of
> "freigegeben" taken from the action having succeeded will be wrong on exactly the deviating
> periods.

**Default behaviour:** actions are proposed for the logged-in user.
Creating tasks for other Disponenten requires explicit confirmation from the operator —
no automatic delegation without instruction.

**No impersonation:** the MCP has no true impersonation — tasks are *attributed* to a
Disponent via `owner_id`, but **permissions remain the authenticated operator's own**.
Show the planned attribution clearly in every preview before writing.

---

### 4. Output

Summary of the situation in three blocks:

**Block A — Immediate actions (today):**
- Critically verleihfrei employees (🔴) with name, ID, and free time window.
- Assignments ending in ≤ 7 days with no follow-on placement.

**Block B — This week:**
- Assignments with `valid_until` in 8–30 days without a successor.
- Open Personalbedarfe with highest priority.
- Dienstplan gaps in the next 14 days.

**Block C — Backlogs:**
- Stundenfreigabe backlog per Disponent (number outstanding).
- Recommendation: use skill `approve-stundenfreigabe` to work through it.

Each block ends with a **concrete follow-on skill call** (see below).

## AÜG / ArbZG

This skill **never** proposes measures that loosen the true hard limits, but not every
ArbZG rule below is a hard block — `manage-shift-schedule` splits them explicitly
(`ArbZgWarning::isHardLimit()`), and reporting should match:

- **Überlassungshöchstdauer** (AÜG § 1 Abs. 1b): 18 months per employee at the
  same Entleiher. Warn when an assignment will reach this limit within the next
  90 days. The clock counts alluvo assignments **and** recorded Vorüberlassungen
  (**PriorPlacement `0-406`** — out-of-system time at the same Entleiher, e.g. via another
  Verleiher), merged per Entleiher, with an interruption of more than 3 months resetting it.
  Vorüberlassungen are now recordable over MCP (`manage-model` on `0-406`), so a
  "no warning" reading only means "no warning *for what is on file*" — if an employee
  plausibly worked at that client before, hand off to `→ manage-contract-lifecycle`
  (Vorüberlassung section) to get it on record rather than reporting the employee as clear.
- **Hard, never overridable — exactly one:** more than 10h worked on one day (§3).
  `manage-shift-schedule` has no bypass for it — the Schicht itself must change.
- **It is measured per EMPLOYEE, across all their Einsätze — not per Einsatz.** The check
  folds in the employee's shifts under every other AÜV (any client) in the surrounding week,
  and the §3 ceiling sums a calendar day's Schichten rather than judging each alone. So an
  employee split over two clients can hit a hard block that is invisible in either Dienstplan
  on its own; the warning names the other client. Report such a conflict as a **coordination
  item between the two Einsatzvertrag owners**, never as a planning error on one side — and
  never resolve it by cancelling the other Einsatz's Schichten.
- **Every write path is checked, the monthly bulk `create` included.** An imported month runs
  the same batch check as `add-shift`/`update-shift` (`→ build-dienstplan`, step 3) and is
  refused **as a whole** if any of its days breaches §3. So a month that exists is a
  month that passed — it may be reported as ArbZG-checked in a Lagebild, provided the report
  says *which* limit was enforced rather than implying a clean bill on every paragraph.
- **Non-blocking (warnings/hints):** rest under 11h in **either** band — the 10–11h deviation
  band *and* below the absolute floor (§5 / §5 Abs. 2) — over 48h/week (§7, tariff-deviable),
  and **Sunday work** (§§9/10). Every alluvo tenant is a care-sector staffing agency, and care
  work is expressly exempt from the Sunday ban — a Sunday Schicht is the **normal case**, not a
  violation to flag as alarming. Surface these as hints alongside the plan, not as blockers
  requiring operator sign-off before proceeding.
- **A rest warning is not a refused write.** §5 findings are computed over an Einsatz's whole
  plan, so they routinely name days far from the one being written and turn up on writes they
  have nothing to do with. In a Lagebild, count them as *roster quality to review* — never as
  "planning is blocked at client X". The same holds for eligibility checks (`Umbesetzung`,
  `add_replacement`, bench matching): a §5 gap arrives as a **hint**, not a blocker, so a
  candidate carrying one is still placeable and should not be filtered out of a shortlist.
- **Availability warning (separate mechanism, not ArbZG):** a shift proposed outside the
  employee's reported availability is blocked until a human types a release reason
  (`availability_override_reason`) — never generated by the assistant. When reporting a
  Dienstplan gap, distinguish "blocked pending an availability release" from a plain
  scheduling gap; the former needs an operator decision (e.g. call the employee), not just a
  planning pass.

If the data suggests a genuine hard-limit violation, highlight it immediately in the situation
report (⚠️) and do not propose further planning steps until the operator has
confirmed the situation.

## Related skills

- `→ bench-check` — detailed individual report on verleihfrei employees
- `→ match-bench-to-clients` — actively place Bench employees with clients
- `→ onboard-new-employee` — create a new employee if capacity is missing
- `→ build-dienstplan` — fill Dienstplan gaps and plan Schichten
- `→ approve-stundenfreigabe` — review and approve submitted Stundenzettel
