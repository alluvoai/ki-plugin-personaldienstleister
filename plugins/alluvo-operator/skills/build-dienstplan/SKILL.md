---
name: build-dienstplan
description: Create, adjust or publish a Dienstplan for a month — with ArbZG compliance checks, creating, editing, cancelling, and reassigning Schichten to another employee (Umbesetzung). Use when the operator says "Dienstplan erstellen", "Schichten anlegen", "plan the schedule", "create shifts for next month", "Schicht stornieren", "Schicht umbesetzen", "Einsatz auf jemand anderen umbesetzen", "someone else has to take the shift", "Dienstplan veröffentlichen", "publish the schedule", "Dienstplan ist noch im Entwurf", "Änderung übernehmen", "Dienstplan-Vorschlag des Mitarbeiters prüfen", "der Mitarbeiter hat den Dienstplan geändert", "approve the employee's shift change", or wants to build, adjust or release a monthly shift plan for one or more employees. Also covers the Soll/Plan comparison the employee sees at the end of the Dienstplan-Wizard ("die App zeigt mir X h unter Soll", "Mitarbeiter sieht Überstunden in der App", "Verplant im Monat gesamt", "Soll-Vergleich im Dienstplan-Wizard", "warum sieht der Mitarbeiter keinen Soll-Vergleich", "muss der Mitarbeiter die Unterschreitung bestätigen"), and the Begründungspflicht on employee changes to a released plan ("die App verlangt eine Begründung", "warum muss der Mitarbeiter das begründen", "wo sehe ich die Begründung zur Dienstplanänderung", "why does the employee have to give a reason").
---

# Build-Dienstplan (Monthly Shift Plan with ArbZG Compliance Check)

## Purpose

Create, adjust, or cancel Schichten for an Assignment over a month — including automatic ArbZG compliance checks (rest period §5, maximum working hours §§3+6, Sunday work §§9+10). All write operations are two-step: preview first, then explicit confirmation.

> Thin wrapper around `manage-assignment-shifts-prompt`. Complex Dienstplan logic lives in the prompt — this skill guides the operator through the workflow.

## Prerequisites

- Employee ID (`0-2`) and Assignment ID (`0-401`) known or resolvable via `search-model`.
- Month and shift times (start–end) known or provided by the operator.
- Exclusively via `mcp__alluvo__*`. No shell access.
- `manage-shift-schedule` belongs to the **Disposition & Verträge** module. Without it
  the tool is missing from the tool list and calling it answers `MODULE_LOCKED` — pass
  that German message on to the operator as it is (it names the required Tarif and the
  Testphase link) instead of planning shifts by hand elsewhere.

## Steps

### 1. Identify the Assignment

If not already provided: use `search-model` with `model_type: "0-401"` to search by employee or assignment number. State the assignment with name + ID.

**One Einsatzvertrag can carry several Einsätze** (different Abteilung, different period —
each with its own Zeitraum and Stundenregelung). Schichten always belong to *one* Einsatz, so
never assume the contract has only one. List them with `manage-assignment-contract`
`action: "manage_einsatz"`, `sub_action: "list"` (`assignment_contract_id`) and have the
operator pick by Abteilung + Zeitraum before planning. For shifts on a contract that is not
yet signed, `manage-assignment-contract` `action: "plan_provisional_shifts"` takes the same
`assignment_id`. The Periode it creates is `provisional`, and **the employee does not see it** —
"Meine Dienstpläne" hides a provisional plan the employee did not author themselves (step 6b).
It reaches them when the plan is published (step 7), not before.

**`add-shift` and `create` never pick the Einsatz for you.** `assignment_id` is always yours to
supply and there is no automatic tie-break. Write to the **existing** Einsatz whose
Einsatzzeitraum covers the Schicht's date (a date outside it is a hard block — step 3), and
**never create a new Einsatz just to park a Schicht**. If two or more of the employee's Einsätze
cover the same date — Einsatz periods of one AÜV may overlap — **ask the operator which one is
meant**, naming Company/Abteilung and Zeitraum for each, and do not guess: a Schicht written to
the wrong Einsatz lands on the wrong customer's Dienstplan document and the wrong invoice. (A
second Schicht overlapping in *time* on the same day is refused as a double-booking whichever
Einsatz it is written to — step 3.)

**A terminated Einsatzvertrag has no Dienstplan any more — check the stage before planning.**
When a contract reaches `lost` or `cancelled`, the AÜV termination cascade removes or cancels
its plan automatically: a never-signed contract has its Dienstplan-Perioden and Schichten
**soft-deleted**; a signed one has its Schichten stamped `cancelled_at` and its Perioden set to
status `cancelled` ("Storniert"), except **Locked** Perioden (approved/invoiced Stundenzettel),
which stay untouched. Either way those Schichten stop being *effective* — they disappear from
the calendar, the employee app, timesheets and the client portal, the employee's availability is
released, and the employee gets an automatic "Einsatz beendet" mail. Consequences here:

- Missing Schichten on a `lost`/`cancelled` contract are expected, not a data problem — don't
  try to recreate them to "repair" the plan.
- Never plan into a terminated contract. If the placement is back on, the contract must first
  return to a live stage and the Dienstplan has to be rebuilt from scratch — reverting the stage
  restores nothing (`→ manage-contract-lifecycle`, step 6).
- `cancelled` is a Dienstplan-Perioden status you may *read*, never one an operator sets; the
  cascade owns it.

**A still-`won` contract can also have a dated end.** `end_contract` ("Vertrag beenden") and
`end_assignment` ("Einsatz beenden") end a contract or a single Einsatz on a chosen date without
it ever becoming `lost`/`cancelled` (`→ manage-contract-lifecycle`, step 6). The same cascade
runs, narrowed to the cutoff: Schichten strictly **after** the date are stamped `cancelled_at`,
the cutoff day's own Schicht is kept, and the Dienstplan-Perioden are left untouched — so a
still-live contract can legitimately show cancelled Schichten past a date plus an inert Periode
around them. Do not recreate those Schichten, and check the contract's `valid_until` before
planning past it: an Einsatz may never run beyond the contract that authorises it (§1 AÜG). To
extend the plan again, the contract's end date has to move first.

**The Schichten you plan here become a customer-facing document.** The AÜV bundle carries one
branded "Dienstplan" PDF per Einsatzvertrag, with a section per Einsatz — the numbered contract
clauses no longer contain the per-day shift list. Two consequences for planning:

- The PDF is a **snapshot taken when the contract documents are generated** (send for signoff,
  re-render, signing), not a live view. Finish the plan before the AÜV goes out for signature;
  if shifts change afterwards, the customer's copy only updates on a re-send.
- Whether an Einsatz appears in it is the per-Einsatz flag `attach_shift_plan_document`
  (default `true`). An Einsatz set to `false` is left out entirely — its Schichten then reach
  the customer through no document at all. Change it via `manage-assignment-contract`
  `action: "manage_einsatz"`, `sub_action: "update"` (→ `manage-contract-lifecycle`), not from
  this skill; never flip it just to make a document look tidier.

### 2. Call the Dienstplan Prompt

Call the prompt `manage-assignment-shifts-prompt` with the desired month and assignment. The prompt returns:

- existing Schichten in the month (overview)
- template for new Schichten (bulk creation or single shift)

> **There is no `ignore_warnings` parameter on `manage-shift-schedule`** — passing it is silently
> dropped. Never send it and never tell the operator a warning can be waved through with it.
> The prompt agrees: it takes six arguments (`assignment_id`, `assignment_contract_id`,
> `employee_id`, `month`, `send_notification`, `dry_run`) and names `ignore_warnings` only to
> say it does not exist. The full flag set is `confirmed`, `past_date_acknowledged` (+ the
> optional `past_date_acknowledgement_reason`) and `availability_override_reason` — nothing
> else releases anything, and the §3 hard limit is releasable by nothing at all.

### 3. Create / Adjust Schichten (Preview)

Use `manage-shift-schedule` or the prompt to set up new Schichten — initially with `confirmed: false`.

For a whole month at once use `action: "create"` with `assignment_id`, `month` (`YYYY-MM`) and
`shifts[]`. **Every entry in `shifts[]` must carry a `shift_type`** — it is required, never
optional. It is the code for that day: free-day codes (`frei`, `dienstfrei`, `free`, `off`,
`urlaub`, `krank`, `nicht vermittelt`, `o`, `-`, `x`, `ab`, `k`, `u` — case-insensitive) are
dropped automatically, any other value is a working code (`f`, `s`, `n`, …) and should have a
matching `legend[]` entry (`code` + `start` + `end`) so the times resolve. A `shifts[]` entry
without `shift_type` fails validation for the whole call.

The preview shows:

- date, start–end, duration per Schicht
- **ArbZG warnings** — on **every** write path, the monthly bulk `action: "create"` included
  (see the box below). They come in two classes — never suppress either:
  - **Hard limit — exactly ONE, never overridable, no `confirmed`/reason bypasses it:** more
    than 10h worked on a single day (§3). There is no `ignore_warnings` parameter — it does
    not exist. The only way past it is to change the Schicht (different time, different day).
    The §3 ceiling is measured on the **calendar day's total net working time**, not on the
    single Schicht: two Teildienste of a geteilter Dienst add up, so 2×6h on one day breaks
    §3 even though neither half does.
  - **Non-blocking warnings — everything else, rest periods included:** rest under 11h in
    **either** band (§5 / §5 Abs. 2 — the 10–11h deviation band *and* a gap below the
    absolute floor), over 48h/week (§7, tariflich abweichbar), Sunday work (§§9/10 — care
    work is expressly exempt, and every alluvo tenant is a care-sector staffing agency, so a
    Sunday shift is the normal case, not a violation to talk the operator out of). These
    proceed with `confirmed: true` like any other preview; show them, don't gate on them.
    A sub-floor rest gap is still reported at `critical` severity so its seriousness stays
    visible — but severity is **not** blocking, and it does not stop the write. §5 is the
    paragraph ArbZG itself makes deviable for exactly this sector (§5 Abs. 2, Krankenhäuser
    und Pflege, with compensating rest alluvo cannot verify); §3 has no such carve-out.
    The §5 rest check measures between **calendar-day envelopes** (each day's earliest start
    to its latest end), not between consecutive Schichten, so the gap between the two
    Teildienste of a geteilter Dienst is not a rest period and raises no §5 warning at all.
    Only the gap from one day's last end to the next day's first start counts.
  - **The §§9/10 check on this write path fires on Sundays only — never on a Feiertag.** Do
    not tell the operator a public holiday was checked. Feiertagsruhe is enforced on the
    timesheet/portal side instead, and there it is scoped to the **Bundesland of the
    Einsatzort** (the Einsatzbetrieb's own `site` Address), not to the employee's home address
    and not to one national list. Two consequences worth naming when the operator asks: the same
    calendar date can be a Feiertag for one Einsatz and an ordinary working day for another
    (Fronleichnam counts in NW, not in HH), and one employee's month can legitimately carry
    holidays from two Bundesländer when they were placed in two states. When that address
    has no resolvable Bundesland, only the nine nationwide holidays are applied —
    the honest fallback, not the full picture; the address is flagged as an
    `Unresolvable Federal State` data-quality issue (`→ triage-data-quality`), correctable with
    `manage-address` `action: "correct"` on the ClientSite (`model_type: "0-341"`). The billing
    run still calculates such an Einsatz, but **invoice generation is refused** for the whole
    run, naming the affected Einsatzbetriebe — so it does hold up invoicing until fixed.
- **Availability warning (separate from ArbZG)** — if a Schicht falls on a day the employee
  has not reported as available, the call is **blocked** ("Availability Warning — Action
  blocked") until re-called with `confirmed: true` **and** a non-empty
  `availability_override_reason`. **Never author this reason yourself** — it must be a
  real operator decision (e.g. after phoning the employee), typed by the operator. Pass it
  through verbatim; do not prefill or invent wording, and never "fix" a blocked availability
  warning by widening the employee's reported availability instead of getting a reason.
- **One Einsatz per day (separate from ArbZG)** — Einsatz *periods* of one AÜV may now
  overlap (e.g. an employee alternating week by week between two deployments), so a Schicht
  can land on a day another Einsatz already covers. That is a **hard block**, same class as
  the ArbZG hard limits: a Schicht is refused on a day the employee already works a Schicht
  under a *different* Einsatz — even if the clock times don't collide. A second,
  non-overlapping Schicht within the *same* Einsatz (geteilter Dienst) stays legal. Resolve it
  by picking the correct `assignment_id` for that day, not by overriding.
  This check runs on **every** write path, the monthly bulk `action: "create"` included — a
  month import that collides on a single day is refused as a whole, not partially applied.
  Drop or re-target the colliding day and re-run.
- **Contract window (`contract_window`, hard)** — a Schicht outside the signed AÜV's own
  `valid_from`/`valid_until` is refused, again with no override. This holds for **`with_plan`
  Einsätze too**: only the *Einsatz* window is plan-derived there (the shifts define it), the
  *contract's* window is not — it is signed and fixed. So "mit Dienstplan" does not mean
  "plan freely past the contract end". If the placement really runs longer, extend the
  contract first (`→ manage-contract-lifecycle`, Verlängerung), then plan the Schichten. On a
  contract with no `valid_until` (open end) only dates before `valid_from` are blocked.
- **Past-dated Schichten (`past_date_backfill`) — operator-confirmable, not a wall and not an
  ArbZG block.** A Dienstplan is routinely digitised part-way through the month, so entering a
  day that has already passed (nachtragen) is a normal correction, not an error. On `create` and
  `add-shift` the day is released by `past_date_acknowledged: true`, plus an optional free-text
  `past_date_acknowledgement_reason` (e.g. "Dienstplan vom Kunden erst am 03. erhalten"); the
  reason, who confirmed it and when are recorded on the Schicht for audit. The
  `confirmed: false` preview lists the days in their **own** section, `### Backfill — past
  date(s) (soft — confirmable, NOT an ArbZG block)` — separate from the hard ArbZG warnings and
  from the non-blocking hints — and the preview's closing line already names *every* flag the
  confirming call needs, both `past_date_acknowledged: true` and an
  `availability_override_reason` when the write needs both. Send them together; don't discover
  the second one on a third round-trip.

  **A confirming call that carries only `confirmed: true` comes back as
  `## Backfill confirmation required (<action>)`** — its own response, explicitly *not*
  `## Action blocked — hard limit`. It names the releasing flag and says plainly that
  `confirmed: true` alone is not enough: `confirmed` confirms the write,
  `past_date_acknowledged` confirms the backfill. Re-send the **same** payload with both.
  **Never react to it by moving the Schicht to another date, and never report the day as
  impossible to enter** — entering exactly that day is the whole point, and re-sending the
  identical payload with only `confirmed: true` will be refused again, every time.
  Two limits stay hard and no flag releases them:
  - **Before the backfill window** (`past_date_outside_window`) — by default the current
    tenant-local month only: on 03.08. the 01. and 02. can still be entered, July cannot.
  - **Editing, cancelling or deleting an already-persisted past Schicht**, and moving a
    Schicht backwards into the past — see the lock box in step 6. Creating is releasable
    because a day with no Schicht yet cannot be falsified; rewriting one that already exists
    is exactly the falsification the guard prevents. `update-shift` accepts the parameter but
    it releases nothing there — a past date on that path still comes back as
    `## Action blocked — hard limit`, not as a backfill confirmation.

  **Never set `past_date_acknowledged` yourself.** Like the availability release it is a
  deliberate operator decision — ask, then pass it through. Only the sanctioned paths carry
  it: a plain `manage-model` create on a Schicht still gets the old hard block (and is
  blocked outright anyway, see step 6).
- **The month's Periode is closed to new Schichten (hard, and not an ArbZG block).**
  `add-shift` resolves the Dienstplan-Periode by **containment of the Schicht's own date**:
  whichever Periode of that Einsatz already *covers* that day, whatever its boundaries and
  whatever its status (a `published` one included — status is not part of the lookup). If no
  Periode contains the day but one overlaps the month, that Periode is **widened to the whole
  month** and takes the Schicht. Only when neither exists is a new Periode created. So a day
  nachgetragen outside the existing plan's boundaries no longer opens a *second* Periode beside
  it — an Einsatz has one Dienstplan per date range and the resolver keeps it that way.
  (On a legacy Einsatz that still carries two live plans in the same month, the widening can
  itself be refused with the overlap error of step 7 — that is a data problem in the plan, not
  in your write.)

  Four statuses refuse the Schicht outright, as a validation error on the `date` field prefixed
  `No shift can be added to Dienstplan #<id> (<name>): …`:
  - **`locked`** — *"the hours for this month are already approved or invoiced — correct them
    in the Stundenklärung, not in the Dienstplan"* (`→ approve-stundenfreigabe`).
  - **`cancelled`** — *"the assignment contract was terminated, so its Dienstplan is closed"*
    — the AÜV termination cascade owns that status (step 1); planning into it is not a
    correction, the placement has to come back first.
  - **`pending_approval`** — *"this month is currently awaiting approval — withdraw it from
    approval before adding shifts"*: a reviewer is looking at exactly that set of Schichten.
  - **`superseded`** ("Ersetzt") — the Periode was **replaced** by a newer plan covering the same
    range (step 7). It is inert; growing the replaced copy would put the Schicht somewhere
    nobody looks. Write the day into the *replacing* Periode instead.
    **Its message is currently wrong** — it comes back as the `pending_approval` wording
    ("withdraw it from approval before adding shifts"), because `superseded` has no message of
    its own yet (alluvo#3196). There is nothing to withdraw from approval: read the Periode's
    real status back (`get-model`, `0-110`) before acting on that sentence, and never tell the
    operator to withdraw an approval that does not exist.

  `draft`, `provisional`, `published`, `needs_revision` and `rejected` all accept a Schicht.
  There is **no** acknowledgement flag and **no** override reason for these four — the way out
  is the one the message itself names. Never report them as an ArbZG finding, never re-send the
  identical call, and never work around one by writing the day to a different Einsatz.

  The monthly bulk `action: "create"` is **stricter than this**: it replaces the month instead
  of adding to it, so it refuses a `published` Periode as well (step 7). Adding one day to a live
  month is a normal correction; re-importing the whole month is not.

> **§3 and §5 are facts about the EMPLOYEE, not about this one Einsatz.** The rest-period and
> daily-ceiling check reads the employee's other effective, non-cancelled Schichten on **every
> other Einsatz** (any AÜV, any client) as context, windowed to the ISO week(s) being planned
> plus a day on each side. This runs on every write path, the monthly bulk `create` included.
> Consequences for planning:
>
> - A Schicht that is fine within this Einsatz can still be **hard-blocked by a shift at a
>   different client** — 4h at client A plus 7h at client B on the same day is a §3 hard block
>   at 11h. A rest conflict across clients (Spätdienst until 23:00 at client A, then 06:00 the
>   next morning at client B, 7h rest) is reported the same way but **warns rather than
>   blocks** — report it and proceed.
> - The warning line **names the other client**: "… — conflicts with another assignment at
>   *Firma X*." Read that back to the operator verbatim; it is the fastest way to see that the
>   conflict is not in the plan they are looking at.
> - The foreign Schichten are **read-only context here** — only the Einsatz you are planning is
>   ever written or blocked. You cannot resolve a cross-Einsatz conflict from this call: move
>   the Schicht on *this* side, or coordinate with the other Einsatzvertrag's owner and change
>   it under its own `assignment_id`. Never cancel the other Einsatz's Schichten to make room.
> - **A hard §3 violation whose affected days all lie in the past is demoted to a
>   non-blocking hint.** One old breach used to hard-block every further write on the Einsatz
>   indefinitely, long after the days in question were history and could no longer be
>   corrected. It now surfaces as a hint, and planning ahead is possible again. A §3 violation
>   with at least one leg on today or any future day still hard-blocks, unchanged. The
>   demotion applies **only** to the ArbZG check: the contract window, the double-booking
>   guard and the backfill window are derived from the rows being written, not from history,
>   so a past-dated backfill still hard-blocks on a real double-booking or an out-of-window
>   date. (§5 needs no demotion — it never blocks, past or future.)
> - This is a **guard rail, not a suggestion** — it protects the employee, not the plan. Do not
>   look for a way around it.

> **A rest warning is plan-wide context, not a verdict on your write.** The §5 check is computed
> over the Einsatz's **whole plan**, not just the row being written — so a single `add-shift` can
> come back naming dates weeks away from the day you touched (two Spät→Früh transitions mid-month
> surfacing while you backfill the 1st). That is pre-existing information about the roster, not a
> defect in your write, and it does **not** stop you. Report the named dates to the operator and
> proceed with `confirmed: true`.
>
> This matters most when **completing or correcting an imported month**: the monthly bulk `create`
> accepts a plan whose rest gaps warn, so the plan legitimately exists with them in it. If those
> same gaps then refused every later edit, the roster the tool let in could never be finished or
> fixed. Never conclude from a rest warning that a Dienstplan task is impossible and hand it back
> to the operator — check whether the block is actually §3 (over 10h on a day), the contract
> window, a double-booking, the started/past-Schicht lock, or an unacknowledged past date. Those
> block; §5 does not.

> **The monthly bulk `action: "create"` runs the ArbZG check too.** It validates the whole month
> in one batch dry-run — the same one `add-shift`/`update-shift` use — per employee across every
> Einsatz, on top of the contract window, the double-booking guard and the availability release
> described above. A clean bulk `create` is genuinely ArbZG-checked; you may report it as such.
> Four things are specific to this path:
>
> - **A hard §3 violation blocks the whole month atomically.** Not one Schicht is written —
>   there is no half-imported month to clean up, and `confirmed: true` does not push it through.
>   The blocker replaces the preview, so you already see it on the `confirmed: false` call.
>   A rest gap alone never triggers this; the month imports and the gap is reported.
>   **A past-dated day does not behave this way** — it does not replace the preview. The
>   `confirmed: false` call returns the normal preview with the backfill section in it; the
>   `## Backfill confirmation required (create)` response only appears on a `confirmed: true`
>   call that omitted `past_date_acknowledged`. So a month digitised mid-month previews cleanly
>   and is confirmed with both flags in one go.
> - **The rows are checked against each other**, not only against what already exists: two new
>   Schichten in the same import that leave less than the rest floor between them are caught
>   (as a warning), although neither is persisted yet.
> - **Rows without a resolvable time are skipped by the ArbZG check** — a working day the
>   extraction left without start/end (no legend match, unreadable cell) has no interval to
>   validate. It is still subject to the contract-window check. Fill those days in with
>   `add-shift`, which validates them on the way in.
> - Hints (rest under 11h in either band, §7, §9/§10) appear in the preview **and** again in the
>   success response under "ArbZG hints (informational — not blocking)"; they never block.

### 4. Evaluate warnings

Present every warning to the operator. A **hard** ArbZG warning — which now means §3, over 10h
on one day, and nothing else — means the Schicht as proposed cannot be created at all; adjust
it and re-preview. A **hint** (every other ArbZG finding, rest periods included) or an
**availability** block both still require the operator's explicit decision, but only the
availability block needs a typed reason to proceed. A **backfill** section is a third, separate
category — not an ArbZG finding at all: it needs the operator's `past_date_acknowledged: true`
flag, no reason required (a note is optional). Read the section heading to tell them apart rather
than lumping everything the response returns into "ArbZG".

**Never state that "ArbZG can never be overridden" without naming §3.** Said unqualified, that
sentence reads as "this task is impossible" the moment any ArbZG line appears in a response —
and a rest warning is the one that appears most often, on writes it has nothing to do with.
Name the paragraph, then act on it: §3 blocks, everything else is reported and passed.

On a monthly `create` a single hard warning refuses the **entire** import. Name the offending
day(s), correct those rows and re-submit the month — there is nothing half-written to repair,
and dropping the day from the payload is only the right fix when the day itself was wrong.

A warning naming another client ("conflicts with another assignment at …") is the one case the
operator cannot solve alone at their desk: say which Einsatz collides and offer the two real
options — move this Schicht, or take it up with the other Einsatzvertrag's owner
(`get-model` on the AÜV shows the owner). Do not present "plan it anyway" as a third option.

**The Einsatz's `max_hours` ceiling is not checked here.** It caps what the *customer* may
book through the client portal, so planning past it never produces a warning on this path —
do not announce one, and do not treat the ceiling as a planning budget. On a plan-only Einsatz
("Nein, Dienstplan reicht") the reverse holds: each shift write **re-derives** `max_hours`
from the plan itself, so the ceiling follows the Schichten you create. Both figures live on
the Einsatz (→ `manage-contract-lifecycle`).

### 5. Confirm

Create or update the Schichten with `confirmed: true` — **plus every extra flag the preview's
closing line named**: `past_date_acknowledged: true` for a backfilled day and/or the operator's
`availability_override_reason`. Both may be required on the same write, and the closing line lists
both; `confirmed: true` on its own then gets you a `## Backfill confirmation required` or
`## Availability Warning — Action blocked` response, not the write. Output the result: number of
created/changed Schichten, total hours, remaining (non-blocking) warnings.

A confirmed write leaves the Dienstplan-Periode in **`draft`** — the Schichten exist, but the
month has not been released yet (step 7). Say which state the plan is in rather than reporting
"Dienstplan erstellt" and stopping. The `create` response says so itself: it prints
**`Schedule Period ID`** and closes with a DRAFT note naming `publish` as the next step. Carry
that id forward and offer the release in the same breath — `manage-shift-schedule(action:
"publish", schedule_period_id: <that id>)` — instead of leaving the operator with a month the
customer cannot see.

### 6. Edit or cancel single Schichten

Beyond the monthly `create`, `manage-shift-schedule` works shift by shift:

- `list` — the Schichten of an assignment (`assignment_id`, optional `from`/`to`), with date,
  time, hours, break, effective rate and cancelled flag. **This is where shift ids come from.**
- `add-shift` — one Schicht (`assignment_id`, `date`, `start_time`, `end_time`, optional
  `break_minutes`, `billing_rate`, `department_shift_id`, `notes`).
- `update-shift` — edit one Schicht (`shift_id` + any of date / start_time / end_time /
  break_minutes / billing_rate / notes).
- `remove-shift` — `cancel: true` cancels (keeps the row and stamps `cancelled_at`);
  `false`/omitted soft-deletes. Pass `shift_id` for one Schicht or
  `shift_ids: [...]` to cancel/delete **several in one call** — same `cancel` / `confirmed`
  semantics apply to the whole batch. Prefer the bulk form over a loop of single calls.
  Two optional booleans, **both defaulting to `true`**, decide which of the two discretionary
  audiences hears about it: `notify_owner` and `notify_on_site_contact` (step 6a).

> **Once the Dienstplan is out, a Schicht can be cancelled but never deleted.** A hard delete
> (`cancel: false` or omitted) is **refused** when the Schicht's Periode is `published`, `locked`
> or `pending_approval`. The employee holds a § 11 Abs. 2 Satz 4 AÜG Einsatzmitteilung naming
> that day and the client sees it in the portal, so the removal has to leave a cancelled row
> behind — that row *is* the audit trail the change digest, the Tätigkeitsnachweis and the
> Umbesetzung history read. It comes back as a validation error on `shift_id`: "This shift
> belongs to Dienstplan #N (…), which is published — a communicated shift can be cancelled but
> never deleted. Cancel it instead (cancel: true), which keeps the row and its audit trail."
> Nothing overrides it — no `confirmed`, no permission, no reason. On a `draft`, `provisional`,
> `needs_revision` or `rejected` Periode, and on a Schicht with no Periode at all, the delete
> still goes through. Practical rule: **once the plan has left draft, `cancel: true` is the
> correct operation** — never offer a delete there as the tidier variant.

> **Shift ids go stale after a bulk write.** `create` (and other mutations) can renumber or
> replace the underlying rows, so ids from an earlier `list`/`create` response are not durable.
> Always re-`list` the plan immediately before a series of `update-shift`/`remove-shift` calls —
> reusing old ids surfaces as a run of "Shift #N not found" errors and a half-applied change.

`add-shift` and `update-shift` run the **full** step-3 check set — availability, contract
window, the double-booking guard **and** the ArbZG limits (§3 blocking, §5/§7/§9 warning)
across all of the employee's
Einsätze. The monthly bulk `create` runs the same set, so no write path is weaker than another:
a day the import accepted is not going to be refused later merely for being edited, and
re-importing a month is never a way around a block.

> **The § 4 ArbZG break is filled in automatically — don't compute it yourself.** Every write
> path (monthly `create`, `add-shift`, `update-shift`) raises `break_minutes` to the statutory
> minimum for the Schicht, so a Schicht can never persist below it. The minimum is derived from
> the **Arbeitszeit** the break leaves over (§ 2 Abs. 1 defines Arbeitszeit *without* the
> Ruhepausen), not from the raw start–end span:
>
> | Span (`end − start`) | Minimum break |
> |---|---|
> | up to 6h00 | 0 min |
> | over 6h00 up to 9h30 | 30 min |
> | over 9h30 | 45 min |
>
> So a 19:10–04:40 Schicht (9h30 span) carries **30** minutes and exactly 9,0 h Arbeitszeit —
> still inside § 4's "mehr als sechs bis zu neun Stunden" band. Do not "correct" it to 45; that
> would cut 15 minutes of paid time without any statutory basis. A break the operator set
> *higher* than the minimum is only ever raised, never trimmed back. If the times change and the
> break was not edited in the same call, a break that exactly matched the old minimum follows the
> new span in both directions — so shortening a Schicht can legitimately lower the break.
> Net hours reported per Schicht are always span − break.

> **A Schicht that has already started is locked — no edit, no cancel, no delete.**
> `update-shift` and `remove-shift` refuse any Schicht whose start time has already passed,
> and any Schicht dated before today — including moving a Schicht backwards into the past.
> This is a **hard block of the same class as the ArbZG ceilings** — no `confirmed`, no
> permission, no reason, and no `past_date_acknowledged` overrides it. The error reads "This
> shift has already started and can no longer be edited or removed — the Dienstplan is locked
> once a shift is underway", or for a past date "… in the past, and can no longer be edited,
> cancelled or removed — past days are immutable." **The `confirmed: false` preview names the
> lock itself**, alongside the hard ArbZG warnings — a clean preview is no longer something a
> failing write can contradict, so read the preview out before promising a correction.
> A Schicht that is running
> or done is history: correct the actual hours in time tracking (`→ approve-stundenfreigabe`),
> and re-plan only the Schichten still ahead. Note the boundary is the *start time*, not the
> date — a Schicht later today is still editable until it begins. Correcting the hours in time
> tracking is itself only possible while the day is not yet released or approved — a released
> or approved `TimeEntry` is locked for everyone, and a closed day is corrected via the
> day-correction flow (`→ approve-stundenfreigabe`, *released or approved hours are locked*),
> never by editing the entry.
>
> **This lock is yours, not the employee's — the two paths diverged on 2026-09-02.** On their own
> **Zeiterfassung** the employee may change („Dienst ändern“) or cancel („Dienst entfällt“) a Schicht
> that has already started, or that lies on a past day, for as long as that **day is still open**:
> no Tagesabschluss of theirs and no Kundenfreigabe on it (`→ approve-stundenfreigabe`). Moving a
> Schicht to another day needs the **target** day open too, and withdrawing a Tagesabschluss reopens
> the window. `update-shift` and `remove-shift` are unchanged — the calendar lock above is still
> exactly what refuses *you*. So „der Mitarbeiter kann das selbst korrigieren, du nicht“ is a real
> answer and usually the right one: ask them to fix it in the app instead of promising a Dienstplan
> write that will not go through. Nothing else is relaxed there — the § 3/§ 5 hard ceilings, a
> `locked` Periode, ownership and the post-publish reason all still refuse — and the change is
> **loud**: it writes the § 11 change-log row and sends the employee digest like any other (6a).
>
> **Adding a missing past day is a different question, and it is allowed** — with the
> operator's `past_date_acknowledged` confirmation and inside the backfill window (step 3).
> The asymmetry is deliberate: a day with no Schicht yet cannot be falsified, an existing one
> can. A backfilled Schicht becomes immutable the moment it is saved, like any other past
> Schicht — so get the times right on the way in; there is no second attempt.

### 6a. Changing an approved Dienstplan notifies the employee

Once the Dienstplan-Periode has left draft — status `published`, `locked` or
`pending_approval` — a change to a Schicht's **time-relevant fields** (`date`, start, end,
break), a **cancellation**, a **deletion**, or a Schicht **added** to the plan is recorded and
the employee is sent a **digest notification** covering every such change in the following
~15 minutes
(AÜG § 11 Abs. 2 Satz 4 — the Leiharbeitnehmer must be kept informed of their deployment
schedule). Employees with a portal user receive it in-app / push / mail per their
notification preferences; employees without one get a mail to their Kontakt address.

- **The employee's digest is never declinable — the other two audiences are.** Split the answer
  by audience when an operator asks for a "silent" or "quick" fix on an approved plan:
  - **Employee — no.** § 11 Abs. 2 Satz 4 is a statutory duty, not a preference, and no
    parameter reaches it. Announce the notification before the write, not after. The one
    internal scope that does silence it is reserved for data repair and seeding and is
    reachable from no operator or UI path, so never offer it as an option.
  - **Einsatzvertrag owner and on-site Ansprechpartner — yes, on `remove-shift` only.**
    `notify_owner: false` leaves the owner out of the digest; `notify_on_site_contact: false`
    keeps the note away from the customer-side Ansprechpartner. Both default to `true`, so an
    omitting call behaves exactly as before, and both are per call — not a standing setting.
    Set them `false` only when the operator actually said so (the usual case: *"das kläre ich
    mit der Kundin telefonisch"* → `notify_on_site_contact: false`); an internal recipient
    nobody asked you to skip should be told. `add-shift` and `update-shift` carry no such
    flags — every audience is notified there.
- **An ADDED Schicht reaches the employee too** (since 2026-08-12). Until then only the
  Einsatzvertrag owner was told about an addition, so a plan revision that cancelled one day
  and added two reported just the cancellation to the employee — the two new working days
  reached them from nobody. Both halves of a revision now land in the same digest. The added
  Schicht's line lists its values plainly, with no old→new arrow (there is no "before"). Two
  consequences: never present "add the day instead" as the quiet way to fix a plan, and expect
  a swap (`remove-shift` + `add-shift`) to read as two lines, not one move.
- **A digest line can carry the employee's stated reason — and yours never will.** Every change an
  **employee** makes to a plan that has left draft has to state a reason (6b), and it renders on
  that change's own line as *"(Grund: …)"* — per line, not per digest, because one digest bundles
  changes made minutes apart for entirely different reasons. It is stored per change on the
  change-log row (`reason`, plus `reason_by_user_id` for who stated it, which is deliberately not
  the row's creator — a job or an automation can write the row, only a human can explain the
  change), so a Schicht moved three times keeps three reasons. **Your own writes record none:**
  `manage-shift-schedule` has no change-reason parameter at all (`availability_override_reason` and
  `past_date_acknowledgement_reason` are different gates and do not feed this), so an operator edit
  — and any change on a draft plan — produces a reason-less line. Two things follow: never offer to
  attach an explanation to your own correction, and never read a missing *"(Grund: …)"* as the
  employee having withheld one.
- **Batch the corrections.** Every change inside the ~15-minute window collapses into a
  *single* digest; a fix-wait-fix-wait rhythm produces several separate notifications for
  the same employee. Prefer the `shift_ids: [...]` bulk form of `remove-shift`.
- **Drafts stay silent.** On a Periode still in `draft` nothing is sent — do the bulk of the
  planning before the plan is approved. A Periode you create through `manage-shift-schedule` lands
  in `draft` when the AÜV is already signed (`won`) and in `provisional` when it is not, so
  operator planning normally starts out silent.
- **A Dienstplan that came from a client-portal booking is `published` from the first second** —
  it is a committed booking, not a draft an operator might still discard. There is no silent
  phase to work in: the very first change you make to it notifies the employee (step 6a
  applies in full). Check the Periode's status before promising a quiet correction. The one
  exception is the booking's **own** Schichten: they are technically additions to an already
  published plan, but are deliberately not digested — the Einsatzmitteilung for that same
  booking has just gone out. A *later* booking onto the same Einsatz is digested normally.
- **Non-time fields don't reach the employee.** `notes` and `billing_rate` changes notify the
  Einsatzvertrag owner only, never the employee.
- **The Einsatzvertrag owner is digested too — one mail per Dienstplan, not per Schicht.**
  Every post-publish change (created, edited, removed — including the non-time fields above) is
  recorded and collapsed into a **single** owner notification ~15 minutes after the first
  change, on the same cadence as the employee digest. It summarises the shape of the change
  ("7 Schichten entfernt") plus the affected days, and only *hints* that a corrected §11
  Einsatzmitteilung may be owed — it never re-sends it; that stays the operator's explicit call
  (step 8). So when an operator asks what the owner will see after a bulk edit, the answer is
  **one** summarising mail. An operator editing the plan on a contract they own themselves is
  not mailed about their own change — that skips the **owner** mail alone; the Ansprechpartner
  note below still goes out (it used to be swallowed along with it). To leave the owner out
  deliberately, pass `notify_owner: false` on `remove-shift`.
- **The Einsatz's Ansprechpartner is now mailed too — and they are the CUSTOMER.** Since
  2026-08-12 the same digest also notifies the on-site Ansprechpartner (the Einsatz's Kontakt,
  falling back to the AÜV's "Fachlicher Ansprechpartner"), as a plain note: what changed, the
  remaining Dienstplan for context, and the already-worked Schichten collapsed to one
  count-and-hours line. There is no CTA and nothing to confirm — the client owns the roster,
  the employee is transcribing it. Two consequences worth stating to an operator:
  - **A change you make on a published Dienstplan now leaves the building.** It is customer-
    facing mail, not an internal digest. Decline it **for a single `remove-shift` call** with
    `notify_on_site_contact: false` — the right move when the operator is clarifying that one
    change with the client by phone. Switch it off **for the whole tenant** with the setting
    `notify_on_site_contact_on_shift_changes` (`availability` group, **default on**) when a
    tenant handles roster changes by phone as a rule. The setting gates the actual send either
    way, so `notify_on_site_contact: true` cannot force a mail a tenant has turned off.
  - **An AÜV with no owner no longer silences everyone.** The digest used to bail out entirely
    when the contract had no owner — nobody was notified at all. The owner mail is now
    skipped independently, and the Ansprechpartner is told regardless. The same now holds for
    the owner editing their own plan: only their own mail falls away.

> **A client-portal booking is guard-railed before the contract exists.** At checkout the
> booked shift intervals are validated (§5 rest — including against a neighbouring day under a
> *different* client's contract — the §3 daily ceiling, the contract window, overlaps) **before**
> the AÜV and the Schichten are written; the checkout guard aborts on a §3 breach **and** on a
> rest gap below the absolute §5 floor, while the 10–11h rest band and Sunday work stay
> non-blocking hints. So Schichten reaching you from the portal have already passed those
> ceilings — don't re-audit them for compliance.
>
> **The checkout guard is stricter than the operator paths on §5, and deliberately so.** A
> booking is a fresh commitment being made from nothing, so alluvo declines to create one that
> is already sub-floor; an operator write is often a *correction to a roster that exists*, where
> refusing the fix helps nobody. Practical consequence: a client booking rejected for a sub-floor
> rest gap **can** be entered from the operator side, because `add-shift` only warns there. Do
> not offer that as a workaround for a rejected booking — it undoes a deliberate gate, and the
> client's booking has no contract behind it. Take it up with the operator as a planning
> decision instead. §3, the contract window and overlaps block on both sides equally.

> **Never reach for the generic model tools here.** Both Shift (`0-111`) and DepartmentShift
> (`0-182`, the recurring shift-code definitions a Dienstplan is built from, referenced as
> `department_shift_id` above) are blocked on `manage-model` / `bulk-manage-model` /
> `query-model` **and on `manage-record-action`**; the error names `manage-shift-schedule`
> explicitly. That includes the `cancel_shift` record action an operator can see on the
> Schicht inside alluvo — it is not reachable over MCP. Cancel through `remove-shift` with
> `cancel: true` instead: same operation (sets the Schicht's status to `cancelled` and stamps
> `cancelled_at`, keeps the row for the audit trail, drops it out of the Einsatzmitteilung), and it
> runs the started-shift block and the employee digest above. Do not retry the generic path — the
> checks only run inside `manage-shift-schedule`. Worth keeping straight now that the web confirm
> dialog for `cancel_shift` offers **exactly** the two switches `remove-shift` takes
> (`notify_owner`, `notify_on_site_contact`), so the skill and the UI agree on what an operator
> may decline — but only `manage-shift-schedule` is callable from here.
>
> **`0-111` stayed blocked when the Schicht gained a status.** The web resource now filters on it,
> but the model type is still off the MCP allowlist — `search-model` / `query-model` / `get-model`
> refuse it exactly as before. "Which Schichten need a replacement?" is therefore **not** a
> `query-model` question; answer it from the uncovered-shift Issue on the Einsatz (below).

#### The Schicht's own status — `planned` · `replacement_needed` · `reassigned` · `cancelled`

A Schicht carries a lifecycle status of its own, and it — not `cancelled_at` — decides whether the
Schicht still counts. `cancelled_at` survives only as the timestamp of a terminal transition.

| Status | Meaning |
|---|---|
| `planned` | The normal state. |
| `replacement_needed` | **Live.** An approved Abwesenheit covers this day: the Schicht still exists, still occupies the client's slot and still shows in their Dienstplan — only the assigned employee cannot work it (`→ record-absence`). |
| `reassigned` | Terminal. The Schicht moved to someone else via the Umbesetzung (step 6c). |
| `cancelled` | Terminal. Ersatzloser Ausfall — `remove-shift` with `cancel: true`. |

- **`reassigned` and `cancelled` are now different rows.** They used to be the same stamped
  `cancelled_at`, so an Umbesetzung and a Storno were indistinguishable afterwards. When an operator
  asks what became of a Schicht, that distinction is now readable.
- **Terminal is terminal.** Neither state is ever reset — a § 12 AÜG Konkretisierung or a
  cancellation notice may already have reached the client. Withdrawing the underlying Krankmeldung
  does not bring the Schicht back.
- **`manage-shift-schedule` `list` does not print the status.** Its `Cancelled` column is derived from
  `cancelled_at`, so a `replacement_needed` Schicht is listed looking like any other planned one; it
  only counts into the `Live shifts` total (which excludes the two terminal states). Do not read
  "not cancelled" as "somebody will work it".
- **An Einsatz with uncovered Schichten raises an Issue.**
  `App\Issues\Staffing\Assignment\UncoveredShiftsDuringAbsence` (category `staffing`, severity
  `high`) opens on the Assignment — one per Einsatz, not per Schicht — and closes itself once the
  last `replacement_needed` Schicht is reassigned or cancelled. Read it via `query-model` on Issue
  (`0-190`); that is the queryable surface the Schicht itself does not offer
  (`→ triage-data-quality`). **Closing it is not instant** — no shift write re-evaluates the
  Issue, so it clears on the nightly data-quality sweep. An Issue still open right after a
  successful Umbesetzung is expected; check the Schichten, not the Issue, to confirm the move
  landed.

### 6b. Employees maintain single Schichten themselves

Employees can add, retime, or cancel **single Schichten on their own running Einsatz** from
the employee app — with **no approval round-trip** (the client communicates the roster change
on site, the employee records it). The Dienstplan is no longer single-author. That holds for
single-Schicht edits in **every** tenant; only the whole-plan wizard edit can be gated behind an
operator (6b-a below). Consequences:

- An unexpected new, moved, or cancelled Schicht may be a legitimate employee entry, not a
  data problem — ask before "repairing" it. One more reason to re-`list` immediately before
  editing (step 6): the plan may have changed since you last looked.
- **No guard is loosened — and on ArbZG the employee path is *stricter* than yours.** Employee
  writes are refused on a Periode closed to new Schichten (`locked`, `cancelled`,
  `pending_approval`, `superseded` — same guard and same messages as step 3), and a deletion
  cancels (stamps `cancelled_at`) rather than destroys — the same semantics as `remove-shift`
  with `cancel: true`. The ArbZG posture there is **not** the advisory one of steps 3/4 — see
  the box below.
- **Which employee surface it is decides how long the window stays open — since 2026-09-02 they
  differ.** Two rules, not one:
  - **Zeiterfassung, single Schicht („Dienst ändern“ / „Dienst entfällt“).** Changeable and
    cancellable while the **day is open** — no Tagesabschluss of the employee's and no
    Kundenfreigabe on that day. A Schicht that has already started, or one on a past day nobody
    ever closed, is therefore still correctable *by them*; a `locked` Periode (Stunden
    abgerechnet) still refuses. Moving a Schicht to another day is checked against the **target**
    day as well, so hours can never be walked out of an open day onto a finished one. Withdrawing
    a Tagesabschluss reopens the window.
  - **Dienstplan wizard, whole plan.** Unchanged calendar lock — a started or past-dated Schicht
    is refused there exactly as it is on your `update-shift` / `remove-shift` (step 6).
  Say the surface out loud when you answer, because "warum ging das gestern und heute nicht" is
  almost always this distinction and not a permission problem.
- On a `published`/`locked`/`pending_approval` Periode an employee change lands in the same
  change log and digest trail as an operator edit (step 6a); drafts stay silent.
- **On those same Perioden a stated reason is mandatory — and it is asked for last.** Adding,
  retiming and cancelling are refused (422 on the `reason` field, max 500 characters) unless the
  employee gives one, whenever the Dienstplan has left draft (`published`, `locked`,
  `pending_approval`). On a `draft` or `needs_revision` Periode the field is accepted but
  **optional**: no change-log row is written there, so a reason would have nowhere to live. What
  decides is the **target Periode's status**, not which screen the employee used — an added Schicht
  resolves the Periode that would cover that day, an inert `pending_approval` one included. The
  guard runs **after** every other refusal (Periode not editable, the promoted ArbZG set, the
  Einsatz's `max_hours`), so nobody is asked to justify a submit that was never going to be
  accepted. Two consequences worth saying out loud: an employee reporting *"die App verlangt eine
  Begründung"* has already cleared every compliance gate — what is missing is a sentence, not a
  planning fix; and **do not offer to enter the change for them instead**, because your own write
  records no reason at all (6a), so the § 11 digest would then explain nothing to anybody.
- **An operator can be alerted to it automatically.** That change-log row is a workflow
  trigger — model type `0-433`, `trigger_event: "created"`, condition
  `record_source equals external_panel` to catch only the employee's own edits — so
  "sag mir Bescheid, wenn ein Mitarbeiter am freigegebenen Plan dreht" is buildable without
  anyone watching the calendar (`→ build-automation-agent`). Since 2026-08-12 a Schicht the
  employee **adds** writes a row too (`change_type = added`), so additions are alertable
  alongside retimes, cancellations and deletions. One limit to state up front: the workflow
  fires **once per Schicht**, not once per edit session — the ~15-minute bundling of step 6a
  covers the employee's mail only.
- **The past-date backfill of step 3 is an operator release only.** The employee app does not
  offer the acknowledgement, so an employee cannot nachtragen a missed day — **adding** a Schicht
  on a past day still refuses outright there, on every employee surface. Entering it is an
  operator job; expect the request to reach you. Do not confuse it with the open-day rule above:
  correcting a past Schicht that *already exists* is theirs, creating one that never existed is
  yours. The asymmetry is the same one as in step 6 — a day with no Schicht cannot be falsified,
  an existing one can, which is why the correction stays inside the still-open day.

The employee-side Dienstplan wizard also changed: it only offers Einsätze whose contract is
**valid today** (a finished Einsatz can no longer be planned for — its absence from the
employee's picker is expected), offers the department's DepartmentShift codes as one-tap
presets (the same rows `department_shift_id` and the AI extraction resolve against), and
displays the § 4 break and resulting net hours — the number the employee sees is the number
that gets paid. Its review step **previews the compliance findings before submit** (each marked
"is this a statutory ceiling?" and "would it actually refuse this submit?"), and a blocking one
is shown together with the Einsatz's Ansprechpartner and the AÜV owner's phone number. An
employee who reaches you about a refusal has usually already tried the on-site contact.

> **What "Meine Dienstpläne" actually lists, and which plans still carry an "Ändern" button.**
> Both were narrowed on 2026-08-12. Say them out loud before promising an operator that an
> employee will see a plan, or that they can correct one themselves.
>
> - **A `provisional` plan an operator built is INVISIBLE to the employee.** The list drops a
>   `provisional` Periode unless the employee's own user authored it (`creator_id`) — and the
>   pre-signature contract-wizard plan (`plan_provisional_shifts`, step 1) is authored by the
>   *operator*, so in practice every provisional plan is hidden. Filtering is by **authorship,
>   not by status**: every other status stays visible no matter who created it. Until this
>   change a "Vorläufig September, 16 Schichten" card stood in the employee's list as though it
>   were their roster, committed to by nobody. **Never tell an operator "der Mitarbeiter kann ja
>   schon mal reinschauen"** — they cannot, and the "ich sehe nichts" call comes back to that
>   operator. The plan becomes visible when it is published (step 7).
> - **A month that has fully elapsed is no longer editable by the employee.** The period card's
>   "Ändern" button, the wizard's plan chooser and the Dienstplan upload all offer a `published`
>   Periode only while its `end_date` is **today or later** in tenant-local time. That is
>   `end_date >= heute`, **not** "covers today" — next month's plan stays editable, which is the
>   normal case, since a Dienstplan is submitted in advance. The gate is server-side too: a
>   whole-plan sync against an elapsed published Periode is refused with `PERIOD_NOT_EDITABLE`,
>   so it is not merely a hidden button.
> - **`draft` and `needs_revision` carry no date bound** — deliberately. That is the resubmit
>   path an employee answers a "bitte nachbessern" with, on a month that has meanwhile ended
>   (6b-a).
> - **This does not make a finished month yours to repair either.** An already-persisted past
>   Schicht is immutable on the operator side as well (the lock box in step 6), and the backfill
>   window for adding a missing day is the current tenant-local month only (step 3). So the
>   answer to "der Mitarbeiter kann seinen letzten Monat nicht mehr korrigieren" is the
>   Stundenklärung (`→ approve-stundenfreigabe`), not an operator edit of the old plan.

> **On the employee path the deviation-permissible ArbZG findings BLOCK unless an exemption
> positively permits them.** On the surfaces *you* write from — `manage-shift-schedule` and the
> calendar — § 5 rest, > 48h/week and Sunday work are reported and passed (steps 3/4; the
> client-portal checkout has its own, separate § 5 floor, see the box in 6a). The employee app
> is the one path that runs them through a strictness promoter, which turns each
> into a hard refusal unless the Einsatz's exemption context permits the deviation. Nothing is
> ever demoted: a § 3 breach stays hard on both sides.
>
> | Finding | Stays a non-blocking hint when | Otherwise |
> |---|---|---|
> | Sunday work (§§ 9/10) | — **no finding is raised at all** once the Einsatzort's Betrieb carries a Sonntagsarbeit-Ausnahmekategorie (falling back to the employee's Position) | blocks |
> | over 48h/week (§ 7) | the employee's Salary active on that day belongs to a Tarif (`collective_agreement_family_id`) | blocks |
> | rest under 11h (§ 5) | the gap is **10h or more** *and* the category is *Krankenhäuser und Pflege* | blocks |
>
> **Permitted Sunday work is silent, not a hint.** Since 2026-08-12 a Sunday on an
> Einsatzbetrieb with a § 10 category produces **no finding** — not an "erlaubt" note. Every
> tenant is a Pflege-Personaldienstleister, so a permitted Sunday is the normal case, and one
> notice per Sunday buried the § 3/§ 5 findings that actually need acting on. A clean care
> roster therefore shows **zero** findings. The § 11 Abs. 3 Ersatzruhetag duty is stated once
> per plan as a footnote under the review step instead of on every Sunday row. Do not tell an
> operator to look for a Sunday hint as confirmation that the Ausnahme is set — its **absence**
> is the confirmation; its presence means the Betrieb is unmapped.
>
> A rest gap **below 10h blocks regardless of any exemption** — § 5 Abs. 2 permits shortening
> *to* ten hours, never under it — and a finding whose gap cannot be read fails closed, i.e.
> blocks. What an operator needs to take from this:
>
> - **A missing Ausnahme on the Einsatzbetrieb, not a bad plan, is the usual cause.** An
>   employee reporting "die App lässt mich den Sonntag nicht speichern" on an ordinary
>   Pflege-Einsatz is nearly always looking at an Einsatzbetrieb whose Ausnahmekategorie was
>   never maintained. § 10 attaches to the **Einsatzbetrieb**, not to the person — so the fix is
>   on that Betrieb; the employee's Position is only a fallback and can never carry an
>   operator-confirmed Ausnahme.
> - **Do not enter the day for them just because MCP lets you.** `add-shift` accepts it (it only
>   warns), but doing so routes around a gate the employee side applies deliberately. Fix the
>   exemption data, or make it an explicit planning decision with the operator — never a silent
>   workaround for a refusal the employee just hit.
> - **Only findings touching a date the employee is actually writing block them.** A hard
>   finding on an untouched day is returned and displayed, but does not refuse the submit —
>   otherwise a single old violation would lock the employee out of the feature permanently.
>   Those days stay yours to repair.
> - **The Einsatz's `max_hours` ceiling blocks there too** — the exact opposite of the operator
>   path, where it is not checked at all (step 4). The employee can neither see nor raise it, so
>   the refusal names the AÜV owner (or generically "Disposition") to call. Expect that call:
>   raising the ceiling is a contract question (`→ manage-contract-lifecycle`), not something
>   the employee got wrong.
> - **It refuses only a write that makes the overage *worse* (since 2026-09-02).** On a month
>   already past its ceiling — 161,7 h booked against 151,67 h — the employee used to be locked
>   out of their own Dienstplan completely: shifting one Schicht an hour later at both ends, no
>   change in duration at all, came back „überschreitet die gebuchten Stunden", and even
>   *shortening* a Schicht was refused. The finding is still **reported** on every such write,
>   because it is true and worth seeing; it just no longer blocks unless the month ends up
>   higher than it already stood. Two consequences: an over-ceiling month is still yours to fix
>   in the Vertrag and does not fix itself, and „die App hat mir die Korrektur verweigert" on a
>   month that is merely over is no longer the expected answer — ask what the change actually
>   was before treating it as a ceiling problem.

**The wizard's review step opens with a Soll/Plan comparison for the month** — `Soll <Monat>`,
`Verplant im <Monat> gesamt`, the difference as *"X h über/unter Soll"*, and a muted *"davon
bereits gearbeitet"* line. Expect to be asked about it ("die App sagt mir 136 h unter Soll"), and
read the figures the way they are built:

- **The Plan figure covers the whole month across ALL Einsätze**, not the plan on the employee's
  screen. Someone on two Einsätze sees a number larger than the hours in front of them — that is
  correct. Do not go hunting through the Dienstplan being edited for the difference.
- **The Soll comes from the Gehalt (`Salary`, `0-12`)**, resolved `monthly_target_hours` →
  `weekly_working_hours × 52 ÷ 12` → the GVP 35-h week (151,67 h) for a GVP salary. It is a
  **flat** monthly value — the same in every calendar month, never spread over that month's
  working-day count — then **minus approved absences** and **prorated** in a partial Eintritts-
  or Austrittsmonat. Same monthly Soll the Einsatz `max_hours` ceiling derives from
  (`→ manage-contract-lifecycle`) and the same engine as the Arbeitszeitkonto card on the
  employee's start page, so those never disagree.
- **It is not the AÜV's `agreed_hours_per_week`.** Those are the hours agreed with the *client* —
  a different quantity, and not what this panel measures. The old wizard check did use them; it
  is gone.
- **No resolvable Soll → no panel at all.** No Salary for the month, or a non-GVP Salary carrying
  neither hours field, yields 0 and the panel is hidden rather than reading "0,00 h" and framing
  every planned hour as Überstunden. "Ich sehe den Vergleich gar nicht" is a Gehaltsdaten gap
  (`→ triage-data-quality`), not a wizard fault.
- **Schichten outside the anchor month are excluded, and the panel says so** (*"… Schichten
  außerhalb von <Monat> sind hier nicht mitgerechnet"*). A Periode spanning two months is
  anchored on its **start** month.
- **Purely informational — it blocks nothing, and there is nothing to tick.** The old blocking
  checkbox *"Ich habe die Abweichung von der Sollzeit zur Kenntnis genommen…"* is **gone**
  without replacement. Never tell an operator that a short-planned month is actively confirmed
  by the employee, and never read a submitted plan as evidence that they saw a shortfall. What
  blocks the submit is unchanged and listed in the box above — the ArbZG hard findings and the
  Einsatz's `max_hours` ceiling. A Soll shortfall is no longer among them: it used to hold the
  submit until the employee ticked that box, and now it does not gate anything.

### 6b-a. When the tenant requires approval: the employee's change is parked as a Vorschlag

`employee_shift_changes_require_approval` (**default off**) changes what happens when an employee
saves a **whole-plan edit** from the Dienstplan wizard: instead of going live, the proposed plan
is parked on the Dienstplan-Periode and an operator releases or discards it. Read or flip it with
`manage-settings` `group: "shift_planning"` (`action: "get"` / `"update"`) — **not** via the
legacy `availability` group, whose field list does not carry it.

What the switch does and does not cover:

- **Only the whole-plan wizard sync is gated.** The employee's single-Schicht add / retime /
  cancel (6b) still goes live immediately in both modes. Never tell an operator that switching
  the setting on makes every employee edit reviewable.
- **Only a Periode in `published`, `draft` or `needs_revision` accepts the wizard edit at all** —
  `provisional`, `pending_approval`, `rejected`, `locked`, `cancelled` and `superseded` are
  refused outright, approval mode or not. So a Vorschlag can sit on a **draft** plan too; it is
  not a published-only mechanism. A **`published`** Periode carries one more condition since
  2026-08-12: its `end_date` must be today or later (6b). An elapsed month is refused with
  `PERIOD_NOT_EDITABLE` and never reaches the Vorschlag stage — so there is nothing for an
  operator to release. `draft` and `needs_revision` stay free of the date bound, which is what
  keeps the revision cycle workable on a month that has since ended.
- **The live plan is never touched while a Vorschlag is pending, and the Periode keeps its own
  status.** A published month stays `published` — it deliberately does **not** move to
  `pending_approval`, because that status is not effective and the approved Schichten would drop
  out of the calendar, "Mein Tag" and availability booking while somebody was reviewing them.
  Consequences: there is no status that signals a pending Vorschlag, and "the plan looks
  unchanged" is the expected state, not a failed save.
- **A Vorschlag replaces, never stacks.** An employee who spots a mistake re-edits, so there is
  always exactly one thing to act on — never a queue.
- **The submit carries one stated reason for the whole plan.** The wizard sync demands a reason on a
  post-publish Periode exactly as the single-Schicht path does (6b) — one reason per revision, not
  one per Schicht, since a single submit can add, move and cancel several days at once. Where the
  sync writes Schichten straight away that reason is stamped onto **every** change-log row it
  produces (and so onto every line of the employee's digest, 6a). In approval mode no Schicht is
  written yet, so it is parked **with** the Vorschlag on the Periode instead
  (`pending_proposal_reason`): replaced when the employee re-edits, cleared when the Vorschlag is
  applied or rejected. On a `draft` or `needs_revision` plan there is nothing to justify and the
  field stays optional.
- **Everything that would refuse a direct employee write refuses the Vorschlag too, before it is
  ever parked** — the promoted ArbZG set of 6b (§ 3 always; § 5 rest, § 7 and Sunday work unless
  an Ausnahme permits them), the Einsatz's `max_hours` ceiling, and the one-Schicht-per-day rule
  below. So a parked Vorschlag has already passed all of them: the operator releasing it is
  deciding about the roster, not about compliance. Do **not** describe the § 5/§ 7/Sunday hints
  as riding along un-gated here — on this path they gate.
- **A second Schicht on one day is refused while `allow_multiple_shifts_per_day` is off** (same
  `shift_planning` settings group, also default off): a day going from ≤ 1 to ≥ 2 Schichten is
  rejected. A day that *already* carries two is grandfathered — it keeps them and stays
  editable and submittable, so flipping the setting can never make an existing plan
  unsubmittable. Tenants who roster a geteilter Dienst switch it on. This gates the employee
  paths only; your own `add-shift` is unaffected (a non-overlapping second Schicht in the same
  Einsatz stays legal there, step 3). The setting lives in the `availability` settings group,
  reachable on the **Dienstplanung** app page.
- **Two Schichten that overlap inside one submitted plan are a hard finding — on every path,
  yours included.** Until 2026-08-12 the overlap check only compared incoming rows against
  *already saved* Schichten, so two conflicting rows sent **together** (a bulk month, an
  employee entering 06:00–13:51 and 13:09–21:00 on one day) were accepted by everything,
  `manage-shift-schedule action: "create"` included. They are now refused. If a bulk create that
  used to work starts failing, this is the likely reason — the plan being sent overlaps
  itself. Back-to-back Schichten that merely touch (13:00 end / 13:00 start) are fine; only a
  real time overlap is refused.

**Releasing or discarding it — two record actions on the Dienstplan-Periode (`0-110`).** Both are
offered only while that Periode actually carries a pending Vorschlag (`operation: "list"` shows
them or does not), and both need `schedule_periods.edit` plus the `approve` ability — releasing an
employee's change onto the live plan is the same authority as approving the plan itself:

```
get-model(model_type: "0-110", id: <period id>)                                   # read the diff
                                                                                  # + version first
manage-record-action(operation: "list",    model_type: "0-110", record_id: <period id>)
manage-record-action(operation: "execute", model_type: "0-110", record_id: <period id>,
                     action: "apply-employee-shift-proposal", confirmed: false)   # preview
manage-record-action(operation: "execute", model_type: "0-110", record_id: <period id>,
                     action: "apply-employee-shift-proposal", confirmed: true,
                     data: { "proposal_version": <version> })                     # write
```

- `apply-employee-shift-proposal` — applies the Vorschlag to the live plan through the same
  per-Schicht diff an employee's direct edit uses: a retimed Schicht **keeps its id** (and with it
  the § 11 change trail, any terminal status an Umbesetzung left, and any TimeEntry pointing at
  it), a Schicht the Vorschlag dropped is **cancelled, never deleted**, and new days are created.
  It writes the § 11 Abs. 2 Satz 4 AÜG change trail, so on a published Periode the employee gets
  the step 6a digest. The Vorschlag is cleared afterwards and cannot be applied twice. Optional
  `data.proposal_version`: a mismatch is refused (*"Der Vorschlag wurde inzwischen geändert…"*)
  and nothing is written. A Periode with no Einsatz behind it is refused outright.

  **Applying can still fail on the started/past-Schicht lock of step 6, and it fails as a whole** —
  the diff runs in one transaction, so nothing is half-applied. Days the Vorschlag leaves
  *unchanged* are skipped, so an already-worked day sitting in the same month is not itself a
  problem; a Vorschlag that retimes or drops a Schicht which has already started is. Report the
  named Schicht and take it back to the operator — the fix is the employee re-doing the Vorschlag
  without that day (the worked hours belong in time tracking, `→ approve-stundenfreigabe`), never
  a workaround from this side.
- `reject-employee-shift-proposal` — clears the Vorschlag and **touches no Schicht**. Because the
  live plan was never modified while it was pending, a rejection is genuinely a no-op on the
  roster — do not offer to "restore" anything afterwards. Pass `data.reason` so the employee
  learns why. The version counter is deliberately not reset, so a stale approval for an earlier
  Vorschlag can never be replayed against a later one.

> **You CAN read the Vorschlag now — but not the reason behind it.** The Periode used to render
> nothing but the two buttons ("Änderung übernehmen" / "Änderung ablehnen"), so an operator released
> an employee's edit onto a live, client-visible plan blind (alluvo#3660). That is fixed:
> `get-model` on `0-110` returns the parked change, because these three sit on the Periode's
> Infolist —
>
> - **`shift_proposal_diff_table`** — one row per changed day: `change` (the translated kind of
>   change), `date`, and `before` / `after` as the live and proposed times side by side
>   (`08:00 – 16:00 (30 Min. Pause)`, and `—` where that side does not exist — an addition has no
>   before, a cancellation no after). **Material changes only:**
>   the employee submits the whole month, so untouched days ride along in the payload and are
>   deliberately left out. Empty when nothing is parked — that is also how you tell there is nothing
>   to release. **Read it out to the operator verbatim before either action**; it is the only
>   description of the change that comes from the data rather than from memory.
> - **`pending_proposal_updated_at`** — when the employee submitted it.
> - **`pending_proposal_version`** — read it here and pass it back as `data.proposal_version`. You
>   no longer need the operator to supply it, so there is no reason to skip the staleness guard: a
>   mismatch means the employee re-edited while you were reading, and the release is refused rather
>   than applying a plan nobody read.
>
> `get-model` returns all three; on `query-model` they only appear if you name them in `fields`. The
> alluvo web app shows the same three under **"Proposed change"** next to the two buttons.
>
> Two things are still readable nowhere:
>
> - **`pending_shift_proposal`**, the raw payload, is on no schema. The diff table is the read
>   surface — do not go hunting for the array.
> - **`pending_proposal_reason` — the employee's stated reason is stored and surfaced by nothing:**
>   no Infolist entry, no MCP field, no notification (api-side gap alluvo#3925). So the one thing
>   the employee was *required* to type (6b) is the one thing neither you nor the operator can read
>   back. Ask the employee, or the operator who spoke to them — and say plainly that alluvo does not
>   display it. **Never present the Vorschlag as having come with no explanation**, and never invent
>   a motive from the diff.
>
> Also unchanged: neither action has a preview of its own, so `confirmed: false` returns the
> declared effects, not the proposed days — read the diff table first.
>
> `→ approve-stundenfreigabe` is a **different** workflow: that approves hours already worked, this
> releases a change to a live roster. Do not present one as the other.

### 6c. Moving Schichten to a different employee (Umbesetzung)

**Never rebuild an Umbesetzung by hand.** Cancelling the Schichten on employee A and creating
them again under employee B produces *no* contract documents and *no* client or employee
notification — the placement is then legally incomplete. There is one dedicated action:

```
manage-record-action
  operation:  "execute"
  model_type: "0-401"          (Assignment — not the contract, not the Schicht)
  record_id:  <assignment_id>
  action:     "reassign_shifts"
  confirmed:  true             (top-level — must be true or the action never runs)
  data: { "employee_id": <incoming employee>, "shift_ids": [...], "confirmed": false }
```

The guided walkthrough is the prompt `reassign-shifts-prompt` — call it when the operator wants
the full Umbesetzung workflow rather than a single mechanical call.

**Two-stage, and the preview is the point.** The top-level switch decides: the tool fills its
top-level `confirmed` into `data.confirmed` only when you **omit** that key, and an explicitly
present `data.confirmed` is honoured **only on the top-level `confirmed: true` branch**. Top-level
`confirmed: false` (or omitted) is *always* write-free — it forces `data.confirmed` to `false`
whatever you sent — and it does invoke this action's own write-free plan, rendered under
**`## Action Preview`** below the payload echo and the field-validation dry run. Either preview
shape works: plain top-level `confirmed: false`, or top-level `confirmed: true` **plus**
`data.confirmed: false` (same plan — mode, blockers, warnings, effects — returned as Response
Data). Show that plan to the operator verbatim, then move the Schichten with top-level
`confirmed: true` and `data.confirmed: true`. **Omitting `confirmed` from `data` on a top-level
`true` call moves them** — the top-level `true`
fills in. The heading separates the two: a `data.confirmed: false` run comes back headed
`# Action Preview (nothing written): reassign_shifts` and spells out that nothing was written and
nothing was sent, while a run that moved the Schichten is headed `# Action Executed`. In the
**Response Data** a preview carries `plan` with `result: null`, whereas the executed run fills
`result` — the payload-side proof of the same thing. Hard blockers and
unacknowledged warnings refuse the write and name what to resolve; set
`acknowledge_absence_conflict` / `acknowledge_duration_override` only after the operator has
explicitly agreed. Only shifts of
**one** Assignment can move together — for shifts spread over two Einsätze, run two Umbesetzungen.

**Only live Schichten move.** A `shift_ids` list is filtered to `planned` and `replacement_needed`
before anything is written; already `reassigned` or `cancelled` ids are silently dropped rather than
moved twice. The Schichten an approved Abwesenheit left at `replacement_needed` are exactly the
normal input here — the `approve` response hands you the ids and the `assignment_id` to run this on
(`→ record-absence`, *Approving is not the last step*). Umbesetzung is the sanctioned answer to an
uncovered Schicht; cancelling it is the fallback for when no replacement exists.

**What happens to the contract is derived, never chosen.** The response's `mode` tells you which
of three paths the server picked:

| `mode` | When | Effect |
|---|---|---|
| `konkretisierung` | the AÜV is signed (`won`) — **with or without a Rahmenvertrag** | contract and client signature stay untouched; the incoming employee joins as a **second Einsatz** on the same AÜV; the client gets a § 1 Abs. 1 S. 6 / § 12 AÜG Konkretisierung with the new person's Einzel-AÜV attached |
| `split_contract` | the AÜV is still pending and keeps some shifts | the original stays pending with its remaining Schichten; an **additional** AÜV carries the moved ones |
| `replace_contract` | the AÜV is still pending and would be left empty | the old AÜV is **cancelled** (a signature link already sent goes dead) and a new one replaces it (`→ manage-contract-lifecycle`) |

Never pass or guess a mode — there is no such parameter.

> **A standalone AÜV (no Rahmenvertrag) is umbesetzbar.** It used to be blocked outright once
> signed (`standalone_contract_won`), with "storniere den Vertrag und lege ihn neu an" as the
> only way out. That blocker is **gone**: a signed standalone AÜV now takes the ordinary
> `konkretisierung` path — the contract stays in force and the incoming person is concretised
> onto it (§ 1 Abs. 1 S. 6 AÜG together with the AÜV's own Austauschrecht). Never advise a
> Storno-and-recreate for an Umbesetzung again; that would void the client's signature for
> nothing.

**`blockers` are absolute.** If the plan comes back with any, report them and stop. Do **not**
shrink the shift selection until a blocker disappears, and do not retry with different
parameters. They are: the incoming employee lacks the required Rolle (`role_mismatch` — a
**higher**-qualified role in the same Rollengruppe is fine, `#NachUntenGehtImmer`, a lower one
never), **no resolvable role requirement at all** (`role_requirement_unresolvable` — see below),
a **hard** ArbZG limit (`arbzg_*`: >10h/day §3 — the only one, same as step 3; a §5 rest gap
comes back as a warning here too and never blocks the Umbesetzung), a Blacklist entry between
employee and client (`blacklisted`), the incoming
employee not being in active employment for those days (`outside_employment_period`), an already
started or past Schicht (`shift_already_started`), and a `lost`/`cancelled` contract
(`contract_terminal_stage`).

**A Schwerpunkt-No-Go is not among them — nothing on this path warns about one.** A person who
declared the Abteilung's Schwerpunkt (`FocusArea`, `0-369`) a no-go stays fully plannable and
umbesetzbar and is shown to you unflagged: the no-go is enforced in the **client portal** only,
deliberately, so the Disponent decides informed. Do not wait for a warning that never comes — if
the Abteilung's Fachlichkeit matters for this Umbesetzung, check it yourself
(`→ match-bench-to-clients`), and do not treat the missing block as a bug.

**`role_requirement_unresolvable` means "pflege die Rolle", not "versuch es anders".** The
equivalence check needs something to compare against: the Einsatzrolle on the Einsatz, else on
the AÜV, else the outgoing employee's own primary qualification. If none of the three yields a
Rolle, the Umbesetzung is hard-blocked — § 11.3 grants the exchange only for a *fachlich
gleichwertigen* Mitarbeiter, and without a requirement that cannot be established. Tell the
operator to maintain the Rolle on the employee or on the contract, then retry. It is not an
acknowledgeable formality.

**`warnings` + `required_acknowledgements` need the operator, not you.** A flag listed in
`required_acknowledgements` must be set to `true` on the confirming call — but only after the
operator has explicitly agreed. Never set one on your own initiative:

- `acknowledge_absence_conflict` — the incoming employee is absent or has reported no
  availability on one of the days.
- `acknowledge_duration_override` — the Überlassungshöchstdauer (§ 1 Abs. 1b AÜG) at this client
  would be exceeded.

Non-blocking ArbZG hints (rest under 11h in either band, >48h/week, Sunday work) appear as
warnings **without** an acknowledgement, exactly as in step 3/4. On `split_contract` a warning also states
that the additional contract copies the commercial terms and that the **Mindeststunden are not
split** — flag that for review before the new AÜV goes out.

**`effects` is the list to read out.** It names, in plain language, which contract is created or
cancelled and which mails go out. Highlights worth repeating to the operator:

- The outgoing employee gets a dedicated cancellation notice when the *whole* Einsatz leaves
  them; on a partial move the cancelled Schichten simply ride the ~15-minute change digest of
  step 6a.
- The incoming employee gets their § 11 Einsatzmitteilung **immediately only in
  `konkretisierung`**. In `split_contract` / `replace_contract` it follows later, when the new
  contract is commissioned.
- In `split_contract` / `replace_contract` the new AÜV is created as a **draft** — it still has
  to be sent for signature (`→ manage-contract-lifecycle`). Do not tell the operator the client
  has something to sign.
- The client is notified only where the plan says so — a Konkretisierung mail in
  `konkretisierung`, a "your signature link is void, another contract follows" notice when the
  pending contract had already been sent out, and nothing at all when it never was.

Afterwards, read the new Einsatz back (`get-model`, `0-401`) rather than trusting the success
message alone.

> **Umbesetzung is not Krankheitsvertretung.** A Vertretung *adds* a cover employee to a running
> Einsatz for a window while the original employee keeps the Einsatz — that is `add_replacement`
> on the AssignmentContract (`→ record-absence`, `→ manage-contract-lifecycle`). An Umbesetzung
> *moves* the Schichten away for good. Pick by what actually happened; the two are not
> interchangeable.

### 7. Publish the Dienstplan (`draft` → `published`)

A plan built here lands in **`draft`** (or `provisional` while the AÜV is unsigned, step 3) and
stays there until someone publishes it. **Publish it from the same tool you built it with** —
`manage-shift-schedule` has a `publish` action, two-stage like every other write there:

```
manage-shift-schedule(action: "publish", schedule_period_id: <period id>)                   # preview
manage-shift-schedule(action: "publish", schedule_period_id: <period id>, confirmed: true)  # write
```

- **`schedule_period_id` is the preferred target** — the `create` response prints it as
  **Schedule Period ID**, so building and releasing a month is one conversation with no lookup
  in between.
- **`assignment_id` works instead** and resolves the Einsatz's single draft Periode. It is
  *refused*, not guessed, when the Einsatz has more than one draft plan — the error names the
  candidate ids so you can re-send with `schedule_period_id`. If there is no draft at all it
  says so and points you back at `list` / `create`.
- It runs **only while the Periode is `draft`**. On a `provisional`, `published`, `locked` or
  `pending_approval` one you get a readable refusal naming the current status — not a write and
  not a 500.

The same transition is also reachable as a record action
(`manage-record-action`, `model_type: "0-110"`, `action: "publish"`) — it is the identical
action behind both routes, so the guarantees below hold either way. Prefer `manage-shift-schedule`
inside this workflow; reach for the record action only when you are already working the Periode
through `manage-record-action`. `0-110` stays **read-only for `manage-model`** either way —
never try to set `status` as a field.

**What publishing actually flips.** The Periode becomes visible in the client portal and to the
employee, and it joins the set of *committed* plans — from then on its Schichten count as a real
conflict for the double-booking, §5-rest and weekly-ceiling checks on the employee's **other**
Einsätze. A `draft` plan is deliberately outside that set, which is why a month left in Entwurf
can be double-planned in silence (`→ head-of-disposition`). Draft Schichten are effective in
every other respect regardless — they already book the employee's availability and already
deliver Soll-Minuten to the Stundenzettel (`→ approve-stundenfreigabe`).

**Publishing sends nothing.** It stamps `status` and `published_at`, and that is all — no
employee mail, no digest. The employee-facing "Dienstplan veröffentlicht" mail comes only from
the client-portal publish path, and `DienstplanApproved` only from the `approve` action. So
`publish` is the safe tool for a month that has already been worked.

> **`approve` is not a substitute for `publish`.** It is a different transition
> (`pending_approval → published`), it only runs on a Periode the employee submitted for
> approval, and it **does** notify the employee. Never reach for it because `publish` was not
> offered — if `publish` is unavailable the Periode is simply not in `draft`.

> **Publishing can be REFUSED: one live Dienstplan per Einsatz per date range.** Before the
> write, `publish` checks the Einsatz's other Perioden and throws when any **live** one overlaps
> this Periode's `start_date`–`end_date`. "Live" means *effective*: `draft`, `published` and
> `locked`. The error names the conflict by id, status and range:
>
> `Einsatz #<id> already has a Dienstplan covering <range>: #<id> (<status>, <from> – <to>). An
> Einsatz can only have one live Dienstplan per date range — cancel or supersede the existing
> one first, or add the shifts to it instead.`
>
> **It is never resolved by silently demoting the other plan**, deliberately: an operator
> publishing a second plan has not said the first one is obsolete, and guessing that would pull
> its Schichten out of the employee app, the client portal and the Stundenfreigabe with no
> warning. So there is nothing here for you to override and no flag that pushes it through — do
> not re-send the identical call. Read the named Periode back (`get-model`, `0-110`), show the
> operator both plans, and take the decision to them:
>
> - the **other** plan is the real one → add these Schichten to it instead (step 3 — `add-shift`
>   joins it by containment), and drop this draft;
> - **this** plan is the real one → the other one has to go first, which on the operator side
>   means the Einsatz/AÜV it belongs to is terminated (step 1). There is no operator action that
>   sets `superseded`.
>
> Inert Perioden never conflict: a `provisional` wizard plan, a `pending_approval` submission,
> a `cancelled` or a `superseded` one may all sit beside the live plan by design.

> **`approve` carries the same refusal — and it is the path that actually hits it.**
> `pending_approval → published` runs the identical check. A pending plan *is* inert, so it can
> legitimately sit beside a live one for as long as it waits; the conflict only surfaces at the
> moment of approval. Resolve it by cancelling the live plan or by rejecting the submission —
> never by approving twice in the hope that it takes the second time.

> **`superseded` ("Ersetzt") — the status of a plan that was REPLACED.** When a *replanning* path
> publishes a new plan over a range an existing plan already covers, the old one is retired to
> `superseded`. It replaced the previous silent demotion to `draft`, so **anything that says a
> replanned Dienstplan "fällt zurück in Entwurf" is now wrong** — `draft` is effective, and the
> demoted plan went on booking the employee's availability and on delivering Soll-Minuten while
> disappearing from the employee app and the portal. `superseded` is inert everywhere: no Soll on
> the Stundenzettel (`→ approve-stundenfreigabe`), no availability booked, invisible to the
> employee app and the client portal, closed to new Schichten (step 3) and to a bulk import.
> It is also **terminal** — no plan comes back out of it.
>
> Three paths write it, and **no operator action is among them**:
>
> - a **client-portal re-submission** of a plan for a range the Einsatz already has one for — the
>   new plan is created, auto-published and the old one retired in the same transaction;
> - the **`provisional` → WON publish** — the pre-signature contract-wizard plan (step 3) going
>   live when the AÜV is signed, retiring the plan it was built to replace;
> - the batch builder behind those two.
>
> The `publish` and `approve` actions above deliberately do not supersede anything.
>
> **A replacement is refused outright when the plan it would retire carries approved or invoiced
> Stundenzettel.** Nothing changes — the new plan rolls back with the refusal. A client-portal
> re-submission is answered with *"Es existiert bereits ein freigegebener, abgerechneter Zeitraum
> in diesem Bereich."*; on the WON path the wizard plan is quietly left `provisional`, the
> contract still transitions and nobody is notified. So after signing an AÜV whose month was
> already abgerechnet, **check for a Periode stuck in `provisional`** — it is not live, and the
> only signal was a log line.

**Publishing is per Periode, all-or-nothing.** Publication lives on the Periode alone — the
Schicht's own status (step 6, `planned` / `replacement_needed` / `reassigned` / `cancelled`) is a
*lifecycle* state, not a publication state, and carries no "published" value. So there is no way
to publish one day of a month; everything effective in the Periode goes out together.

> **What `draft` actually withholds — and what it does not.** The action's description used to
> claim a draft plan is hidden from the employee app and from Stundenfreigabe and delivers no
> Soll-minutes. It does none of those things, and the description now says so. What the code does:
>
> | Surface | On a `draft` Periode |
> |---|---|
> | Employee app (calendar, day, Zeiterfassung) | **visible** — `draft` counts as effective |
> | Employee's Soll on the Stundenzettel | **counted** — the Soll is built from the Schichten regardless of period status |
> | Employee's availability | **booked** — a draft Schicht already blocks the day |
> | ArbZG §3 daily ceiling | **counted** |
> | Client portal "Dienstpläne/Stundenfreigabe" hub / "Nächste Schichten" | **hidden** — this is what publishing releases |
> | Double-booking, §5 rest, weekly ceiling *against a new Schicht* | **not counted** — only `published`/`locked` Schichten are a conflict another Schicht must yield to |
>
> The last row is the operational reason to publish rather than a cosmetic one: while the month
> sits in `draft`, planning the same employee into a second Einsatz raises **no** double-booking
> or rest-period warning. So an employee left in draft is genuinely at risk of being planned
> twice — and neither operator sees it.

**There is no "publish last" rule.** `add-shift` resolves the Periode by **containment of the
day**, status not part of the lookup (step 3) — so a day nachgetragen *after* the month went out
joins the **existing published Periode** and is effective and client-visible immediately, and a
day just outside that plan's boundaries **widens it to the month** rather than starting a second
one. Publish when the month is ready; correct it afterwards as needed. Two things still follow
from publishing: the change notifies the employee (step 6a, no silent phase left), and once the
month is `locked`, `pending_approval` or `superseded` the write is refused outright (step 3).

> **The monthly bulk `action: "create"` is the exception: it does not join a live month, it
> refuses one.** That path is destructive — it deletes the month's Schichten and rebuilds them
> from the payload — so it is closed to exactly one status more than `add-shift`: **`published`**,
> on top of `locked`, `cancelled`, `pending_approval` and `superseded`. The refusal is a
> validation error on the `month` field, `The Dienstplan for <YYYY-MM> cannot be imported into
> Dienstplan #<id>: …`, carrying the reason and the way out:
>
> - **`published`** — *"it is already published — correct a published month shift by shift, never
>   by re-running the import"*. Do exactly that: `add-shift` / `update-shift` per day, which join
>   the published Periode as described above.
> - **`locked`** — *"its hours are already approved or invoiced — corrections belong in the
>   Stundenklärung"* (`→ approve-stundenfreigabe`).
> - **`cancelled`** — *"the assignment contract was terminated, so its Dienstplan is closed"*
>   (step 1).
> - **`pending_approval`** — *"it is currently awaiting approval — withdraw it from approval
>   first"*.
> - **`superseded`** — the Periode was replaced by a newer plan (step 7); import into the
>   *replacing* one. Like `add-shift`, it has no message of its own yet and comes back with the
>   `pending_approval` wording (alluvo#3196) — check the status before repeating that sentence
>   to the operator.
>
> Nothing is written when it refuses — no half-replaced month to clean up — and there is no
> acknowledgement flag that pushes it through. `draft` and `needs_revision` are still reused in
> place: replacing a draft is the point, and `needs_revision` is the revision-cycle re-upload that
> must overwrite rather than duplicate.
>
> **`provisional` is in neither set.** A bulk `create` against a pre-signature wizard plan
> (step 3) is neither refused nor reused, so it still starts a **second** Periode for that month.
> Don't bulk-import over a provisional plan — sign the AÜV first, or plan it shift by shift.

> **An emailed or ticket-attached Dienstplan for a closed month fails silently.** The inbound
> extraction path declines the same five statuses, but it is background work with no operator
> waiting on it: it logs and stops, with **no error anywhere in the UI**. So when an operator says
> a Dienstplan they forwarded "did nothing", check that month's Periode status before hunting for
> a parsing problem — a `published`, `locked`, `pending_approval`, `cancelled` or `superseded`
> month was declined, not misread. The remedy is the same one: correct that month shift by shift.

### 8. §11 AÜG Notification (optional)

If the Einsatzvertrag has a §11 AÜG notification obligation and Schichten have changed, the prompt asks whether the notification should be re-sent. Offer the operator the option — never send automatically.

**The re-send window does not close when the Einsatz ends.** `send_assignment_notification`
requires `stage: won` and a contract that has not fallen through (`cancelled`/`rejected`);
`performed` passes. An Einsatz whose `end_date` has passed can still be notified **manually**, as
a deliberate late notice (Nachtrag) — only the platform's *automatic* sends stay silent on an
ended Einsatz. So the usual order — Vertrag gewonnen → Schichten bauen → Einsatzmitteilung senden
— still holds, and on an older roster the send is still on the table: offer it, say that the
Einsatz is already over and the notice is late, and send only after the operator confirms. Never
tell them the window has closed. What genuinely blocks it: an unsigned contract, a cancelled
Einsatz, or an employee without an email address. Details → `manage-contract-lifecycle`, step 5.

> **The Einsatzmitteilung goes to the employee, not to the customer.** §11 Abs. 2 Satz 4 AÜG is
> the *employee-facing* duty: the mail is addressed **TO the deployed Mitarbeiter**, with a fixed
> internal CC — the Einsatzvertrag owner, plus the sending operator on a manual send (the
> auto-send has no operator and CCs the owner alone). **No customer contact can ever be CC'd**,
> and the CC list cannot be picked per send: not the Ansprechpartner vor Ort, not a contract
> recipient. The *customer-facing* disclosure duty is a different paragraph, **§12 AÜG**,
> discharged by the AÜV itself and by the Konkretisierung (`→ manage-contract-lifecycle`,
> step 5). Never tell an operator this send informs the client.
>
> What separates it from the step 6a digest is not the audience — both reach the employee — but
> the trigger: this one is sent on the **operator's decision**, the shift-change digest is
> automatic and cannot be declined.

**A re-send re-opens the employee's read receipt.** Where the tenant asks employees to confirm
the Einsatzmitteilung, the corrected send creates a new receipt: the Assignment's
`assignment_notification_acknowledgement_state` (`0-401`) falls back to `pending` and
`assignment_notification_acknowledged_at` is cleared. That is intended — the employee has not
seen the corrected version yet — so don't report it as a regression, and don't treat the
pending state as something blocking the roster. The confirmation gates nothing: no Schicht, no
Zeiterfassung, no dispatch. Details and the tenant settings → `manage-contract-lifecycle`, step 5a.

### The Dienstplan is printed on the document the client signs

The Tätigkeitsnachweis carries an **Abw.** column beside the worked hours, and — where the client's
`document_planned_disclosure` setting is `full` — the planned block next to Ist as **Zeit · Pause ·
Std.**, its Von and Bis collapsed into one `06:00–14:12` cell (only Ist keeps them apart). So the
plan is no longer an internal artefact the client never sees: it
is on the sheet the Entleiher signs off (`→ approve-stundenfreigabe`, *what the Tätigkeitsnachweis
actually puts in front of the client*). How much of it is printed is per company and defaults to
`delta_only` — the deviation without the planned times — so check the setting before promising a
client either that they will see the roster or that they will not. Two consequences for planning:

- **A planned Schicht nobody worked prints as a highlighted gap row reading "Nicht gearbeitet".**
  It is not a blank line the client will skim past. Where a Schicht is genuinely obsolete, cancel
  it (step 6) rather than leaving it in the plan to surface as an unexplained gap — and where a
  declared Krankmeldung is the reason (submitted already counts, not just approved), that day
  carries "Krank" instead and is no deviation (`→ record-absence`). A `replacement_needed` Schicht
  keeps its planned times on the sheet too — the day prints "geplant · Krank" rather than
  vanishing from the document.
- **The printed Soll is frozen per timesheet day, not re-read from the plan.** It comes from the
  day's stamped `soll_*` values, so retiming or cancelling a Schicht after the period was built
  does **not** change what an already-generated Nachweis says — that is deliberate, since the
  Abweichung was measured against exactly that plan. Do not offer a plan edit as the way to fix a
  number on an issued Nachweis; correct it in time tracking (`→ approve-stundenfreigabe`), which is
  also the only route once the month is `locked`.

## Output

- Table of newly created / changed Schichten (date · start–end · hours)
- Open ArbZG warnings (if any, with section reference)
- Total hours in the month
- Status of the Dienstplan-Periode (`draft` or `published`) and, while it is still `draft`,
  the offer to publish it (step 7)
- Note on §11 AÜG notification if relevant

## Related skills
- `→ record-absence` — record the Krankmeldung/Urlaub that makes a Schicht change necessary.
- `→ bench-check` — find available employees when a Schicht needs different coverage.
- `→ manage-contract-lifecycle` — when the plan change requires a contract change first.
- `→ approve-stundenfreigabe` — review submitted hours against the planned Schichten, and see
  whether a published month's hours came back signed: the periods a Dienstplan materialises are
  listed in the web app under HR & Payroll → **Stundennachweise**, with the signed
  Tätigkeitsnachweis PDF one action away on an approved period. The periods themselves are
  MCP-readable (`Timesheet` `0-426`, plus `0-427` days and `0-435` client sign-offs), so a "welche
  Zeiträume dieses Monats sind zurück" figure is a query — but nothing about them is writable, and
  opening the PDF stays a click in the app.
- `→ build-automation-agent` — turn "melde mir jede Mitarbeiter-Änderung am freigegebenen Plan"
  (step 6b) into a workflow on model type `0-433`, instead of anyone checking the calendar.
