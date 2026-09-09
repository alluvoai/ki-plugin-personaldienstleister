---
name: match-bench-to-clients
description: Match verleihfreie Mitarbeiter to clients with active Rahmenverträge, generate shareable profile URLs, draft Einsatzverträge, and create Disponent review tasks. Use when the operator says "matche die Bank", "finde Einsätze für verleihfreie Mitarbeiter", "match the bench", "create draft assignment contracts", "wer passt zu welchem Kunden", "Einsatzmöglichkeiten für den Bench", or wants to turn an availability gap into a placement.
---

# Bench → Client Matching (Placement Workflow)

## Purpose
Systematically match verleihfreie or soon-to-be verleihfreie employees with clients
that have an active Rahmenvertrag and require capacity — from a match list through
to a draft Einsatzvertrag and a Disponent review task.

> Upstream: `bench-check` provides the prioritized candidates.
> Write steps (Einsatzvertrag, task) always require a preview →
> operator confirmation.

## Prerequisites
Uses only the connected alluvo MCP tools (`mcp__alluvo__*`). No tokens, no shell.
Everything runs inside the operator's tenant.

## Steps

### 1. Scope employees and timeframe
If not yet known: call `manage-employee-availability` (bench view) to obtain the list
of verleihfreie employees. Ask the operator for the desired timeframe and, if
applicable, specific employees.

### 2. Start the matching prompt
Call `find-matches-prompt` for each employee. The prompt evaluates:

- **Geographic proximity** — employee home location vs. deployment site of open
  requests / client locations.
- **Qualification/position match** — compare position, certificates, and training
  from `get-profile` (`resource: "profile"`, `model_type: "0-2"` + the employee's `model_id`).
  `get-profile` belongs to the **Recruiting** module — if it is absent or answers
  `MODULE_LOCKED`, read the qualification data straight off the Employee with `query-model`
  (`staffingRoles`, `staffingExperiences`, `staffingTrainings`, licenses) and tell the
  operator the ready-made profile view is not part of this tenant's Tarif.
  To pull *which* bench employees actually hold a given role, filter Employee (`0-2`) with a
  `filter_groups` condition on the bare **`staffingRoles`** field — both `search-model` and
  `query-model` accept it as sugar for `staffingRoles.id`, and a near-miss like
  `staffingRole` comes back with a did-you-mean pointing at `staffingRoles.id`. Resolve the
  role id first with `resolve-staffing-role`; never guess it.

  > **A different role is not automatically a miss — #NachUntenGehtImmer.** Matching scores the
  > role feature by hierarchy, not by label equality. In the order the rule is evaluated:
  >
  > | Case | Role score |
  > |---|---|
  > | Exact role | **1.0** |
  > | Same `staffing_role_group_id`, employee's `level` ≥ the demanded level | **0.8**, decaying by 0.05 per extra level of distance beyond one, floored at **0.6** |
  > | Same group, the **demanded** role's `level` unknown | **0.6** (honest unclassified fallback) |
  > | Same group, employee's `level` lower than demanded | **0.0** (never upward) |
  > | Same group, the **employee's** `level` unknown but the demanded one known | **0.0** |
  > | Different group, or the employee's role has no group at all | **0.0** |
  >
  > Where a demand names several roles of one group, the **lowest** of their levels is what a
  > candidate must meet; a stricter role never excludes someone who satisfies a looser one.
  >
  > **The unknown-level case is not symmetric.** An employee whose role carries no `level`
  > scores **0.0** against a demand whose level *is* known — an unclassified person is never
  > treated as possibly-qualified. Only the reverse (demanded level unknown) falls back to 0.6.
  > So a gap in the Rollenkatalog now costs you candidates outright rather than blurring them:
  > `→ triage-data-quality` step 3c is the fix.
  >
  > So an Intensivpflege-Fachkraft also covers a plain Pflegefachkraft-Bedarf, while a
  > Pflegehilfskraft never covers a Fachkraft-Bedarf. Don't drop a higher-qualified candidate
  > for not matching the role label exactly, and say in the rationale which of the two cases a
  > match is.
  >
  > `resolve-staffing-role` returns **neither** group nor level — read `level` and `group.name`
  > off the role (`0-100`) with `get-model`/`search-model` if you need to place it. A role
  > score of 0.6 means the catalog is unclassified, not that the candidate is a mediocre fit;
  > `→ triage-data-quality` step 3c fixes that, and the MCP prompt
  > `manage-staffing-role-hierarchy-prompt` carries the full rules.
  >
  > **The Fachweiterbildung axis now scores — but only on the `0-415` demand path.** A role also
  > carries a `specialty` (Intensiv, Anästhesie, OP, Notfall, …), and the substitution rule uses
  > it in two more cases: a covering specialty bridges *across* role groups (**0.5**), and a
  > mismatching one *within* a group demotes to **0.4**. Both need the **demand** side to state a
  > specialty too, and that is now the case for a `StaffingDemand` (`0-415`) — its shortlist
  > (`0-416`) carries the required role's specialty, so an Intensiv-qualified candidate offered
  > against a **Notfall** demand of the same Gruppe and Level lands on 0.4, not 1.0. It is a real
  > downgrade, **never** an exclusion: such a candidate can still be legitimate, so read a 0.4 as
  > "fachlich daneben, prüfen" and say so in the rationale rather than dropping them silently.
  >
  > **Two carve-outs.** A demand naming several roles of one Gruppe with *different* specialties
  > is treated as having no specialty constraint for that Gruppe (same permissive fallback as an
  > un-leveled Gruppe). And the nightly `EmployeeStaffingOpportunity` (`0-126`) shortlists — what
  > `get-profile` and `→ profilvertrieb` read — still carry **no** specialty on the requirement
  > side, so a role score there can only be EXACT / downward / unclassified / too-low. Don't
  > explain a `0-126` match with a specialty case. Where specialty is enforced *hard* (exclusion,
  > not a penalty) is employee **visibility** — `manage-employee-availability` view `explain`, client
  > portal / team calendar — Einsatz substitution, and the `specialty_fit: conflict` gate above.
- **Rahmenvertrag active + capacity available** — use `search-model` for the
  client's Rahmenverträge; use `list-model-types` to resolve the correct
  `model_type` ID for the Rahmenvertrag.
  To see whether one actually prices the matched role, call `manage-framework-contract`
  with `action: "list_roles"` (read-only) — it names each priced role and its base price.
  **An empty list means the Rahmenvertrag prices nothing itself** (rates are agreed per
  individual AÜV), *not* that it covers everything — so don't quote a rate from it, and
  don't drop the match either.

### 3. Present the match list
Output per match:

- Employee Name · ID · Position · home location
- Client Name · ID · site · estimated distance
- Rahmenvertrag ID + validity
- Match rationale (qualification, proximity)

> **Fachliche Eignung gate (#980).** Where an `EmployeeStaffingOpportunity` (0-126) exists
> for the pair, read its top-level `specialty_fit` (`suitable` / `conflict` / `unknown`) and
> `meta.specialty_fit_reason`. **Skip any `conflict` match — hard, regardless of proximity
> or revenue** (e.g. an adult-ICU nurse to a dedicated children's clinic); if listed, label
> it **"nicht fachlich geeignet — übersprungen"**. For `suitable`, only state suitability for
> a client department the employee's specializations actually cover; for `unknown`/absent,
> keep the rationale general — never claim a specific clinical fit the employee can't back.

> **An uncovered Schicht is not a StaffingDemand — do not route it through here.** When an
> approved Abwesenheit leaves Schichten with nobody to work them, the Einsatz raises a
> `staffing` Issue (`UncoveredShiftsDuringAbsence`, `→ triage-data-quality` 3f). The answer is the
> **Umbesetzung** on that existing Assignment — `reassign_shifts`, which keeps the signed AÜV and
> sends a § 12 AÜG Konkretisierung (`→ build-dienstplan` step 6c) — not a new demand, a new match
> and a new Einsatzvertrag. This skill's flow would create a second contract for work that is
> already contracted. Use it only to *find* a suitable replacement (step 2's scoring is the same
> question); execute the move through the Umbesetzung.

> **Automatic matching is off — a demand carries a shortlist only if someone built one.**
> The autonomous pipeline sits behind the Pennant flag `AutomaticDemandMatching`, off by
> default per tenant, because it proposed candidates who had reported themselves unavailable
> and skipped the fachlich right person by ignoring higher, neighbouring roles. While it is
> off, a new or re-qualified `0-415` produces **no** `0-416` match rows, **no** "Personalbedarf
> prüfen" or "Anschlusseinsatz prüfen" task, **no** auto-drafted proposal email and no Slack
> shortlist reply. So do not open this skill by reading a demand's matches and stop when there
> are none — an empty `0-416` list is the normal state, not a verdict that nobody fits. Work
> the demand the manual way: this skill's own search, `→ bench-check`, `search-model` on
> `0-126` (EmployeeStaffingOpportunity, **not** gated) for the client company, or the
> operator-driven matching workspace (`/staffing/matching`, `/staffing/company-matching`,
> also not gated — the same scoring engine, run on request).
>
> Everything below about how matches are scored, gated and read still holds for the rows that
> **do** exist: demands worked before the shutdown, and tenants that have the flag switched
> back on. Check, don't assume.

> **A StaffingDemand (0-415) may already carry an auto-drafted proposal — where matching ran.**
> `0-415` is where all current demand lives, whatever channel it came from. Where a matching
> run happened, it auto-drafts one candidate-proposal email for the shortlist about 15 minutes
> after matching (unless an operator offered first) and parks it as an approval-gated run for
> the mailbox/contact owner — the
> demand's matches (`0-416`) then show `offered_at` and `proposal_email_id`. Before
> pitching candidates for such a demand yourself, check its matches for those fields: if
> a draft is already awaiting approval, point the operator there instead of drafting a
> competing proposal. With the flag off no such draft is ever created, so absence of one
> means nothing has been pitched yet.
>
> **That mail now restates the Bedarf and names each candidate's own Rolle.** The auto-draft
> opens with what the customer asked for ("Sie suchen 1× Pflegefachkraft für <Einsatzort>,
> von … bis …, 40,00 Std./Woche") and lists each candidate under the **StaffingRole that
> actually qualifies them for this demand** — not the free-text `current_position`, which is
> often empty. So don't "fix" a draft by pasting `current_position` in, and expect the
> candidate's stated role to be the *qualifying* one, which for a downward substitution is
> the higher role they hold, not the demanded one. The demand itself is attached to the mail
> (it shows in the "Verknüpft mit" line), so `get-timeline` on `0-415` returns it — see below.

> **An empty or very short shortlist is now a scoring verdict, not just a cap.** Two floors
> run before the shortlist cap of 10:
> - a **minimum score of 25** (0–100 deterministic scale) — candidates who cleared every gate
>   but scored below it are dropped and counted in the reason breakdown as *below_min_score*.
>   A demand whose only eligible person is a weak fit now yields **no** proposal rather than
>   proposing them as the sole candidate. Read "keine Vorschläge" for such a demand as
>   *"nobody scored well enough"*, and widen the Bedarf (role, radius, period) or pitch
>   manually — do not assume the pool was empty.
> - a **hard Sektor gate**: where the employee **and** the client company both state a Sektor
>   and they share none, the pairing is rejected outright rather than merely losing the sector
>   weight. It fails open — an unknown Sektor on either side never blocks. A cross-sector
>   candidate you think is right is a data question (is the Sektor on the employee correct?),
>   not something to argue past.
>
> **Freistellung excludes.** An employee whose current EmploymentPeriod carries a
> `duties_suspended_at` on or before today is freigestellt and is excluded from automated
> matching entirely — the same rule the client portal already applied. They will not appear in
> any `0-416` shortlist, so don't hand-pitch one either.

> **A Schwerpunkt-No-Go does NOT filter this list — but it does block the client portal.** A
> person can declare a Schwerpunkt (`FocusArea`, `0-369`) a no-go; it sits on their **Contact**
> (`0-105`) and takes effect **only in the client portal**, where they are neither shown nor
> bookable for an Abteilung carrying that active Schwerpunkt. Matching, Dienstplan and AÜV
> ignore it **by design** — such a candidate still appears here, still scores normally, and you
> may legitimately place them, because the Disponent decides informed where the self-service
> channel must not. So do not read their presence in a shortlist as "no no-go exists", and do
> not report the divergence as a bug. Where it matters — a customer who books their own staff
> for that Abteilung will not find the person — check the department's Schwerpunkte and the
> person's no-gos before promising a portal booking. Setting them: `→ onboard-new-employee`
> (the person's no-go) and `→ intake-personalbedarf` (the Abteilung's Schwerpunkte).

> **The "Anschlusseinsatz prüfen" task is the ROI signal on a demand — where matching ran.**
> With `AutomaticDemandMatching` off it is never filed, so its absence carries no information;
> treat the section below as how to read one you find, not as a work queue to wait on. Besides
> the familiar "Personalbedarf prüfen" task, a matching run files a **second, separate** Task
> (`0-5`) titled *"Anschlusseinsatz prüfen: <Bedarf>"* whenever a matched employee is currently
> verleihfrei or their running Einsatz ends within ~14 days. It is attached to both the demand
> (`0-415`) and the client Company (`0-3`), owned by the demand's creator, priority high, due on
> the demand's `valid_from`, and its body names per employee: the situation (verleihfrei / Einsatz
> bei X endet in N Tagen), the **additional hours** and **additional revenue** booking them here
> would secure, plus a confidence marker (revenue is omitted where the rate or hours are unknown).
> Read it as a prioritisation aid — these matches close a bench gap on top of filling the Bedarf,
> so pitch them first. Where matching did run, it exists **only** when there is a real
> opportunity. Find it with `search-model` on `0-5` (Task) — `search` on the title,
> `status` `in ["not_started","in_progress"]`; `get-open-tasks` was retired — or via
> `get-timeline` on the demand.

> **Check whether the employee is already proposed — query `0-416` directly.** Matches are
> readable on their own, not only through a demand's `matches` include: `search-model` on
> `0-416` filtered by `employee_id` returns every demand this bench employee was matched to,
> across all demands and without a parent demand id. Also filterable: `score`, `outcome`
> (`offered` / `accepted` / `declined`), and the `staffingDemand` / `employee` relationship
> filters — confirm the fields with `get-model-schema` (`context: list`). Read
> `outcome` + `offered_at` before pitching: an `offered` match means the client already has
> this person on the table, and an `accepted` one is already becoming an Einsatzvertrag —
> don't propose them a second time. `0-416` is **read-only** (`manage-model` writes are
> rejected); `mark_offered` / `accept` / `decline` go through `manage-record-action`. Reading
> it requires the `staffing_demand_matches.view` permission.

> **A demand has a timeline of its own now.** `get-timeline` accepts `subject_type: "0-415"`
> and returns the demand's `action` / `task` / `issue` / `ticket` / `email` history — the
> status-change trail, both generated tasks, and the candidate-proposal mail (emails are
> attached to the demand directly). Use it to answer "what has already happened on this
> Bedarf" in one call instead of reassembling it from the company timeline.

Ask the operator to confirm which matches to pursue.

### 4. Generate profile URLs (optional)
For approved matches: call `get-profile` with `resource: "url"`, `model_type: "0-2"`,
the `model_id`, and `link_type: "public_url"` — a link that is read-only *for the
client*, valid 7 days, safe to share. (`link_type` replaced the old `action` param when
`get-profile-url` was merged into `get-profile`; the values are unchanged. Note the call
itself **writes** — it persists/refreshes the profile token — so it is not a free
lookup, even though nothing about the person changes.) Optional: `show_availability_calendar`
(+ `availability_from` / `availability_until`) and `show_agency_assignments`.

> **The calendar flag is confirmed, not assumed — read the response line back.** The
> availability calendar is fed by the **employee's** availability periods, so a person
> with no Employee record (any pure Kandidat, reached via `0-81`/`0-105`) can never have
> calendar data. For those, the response no longer says `Enabled` but **"Requested, but
> NOT shown — this person has no employee record …"**, and the profile page renders no
> calendar at all. Never promise a client "Verfügbarkeit sehen Sie im Profil" off the
> flag you passed; promise it off the line the tool returned. When it comes back *NOT
> shown*, either capture availability on the employee first (`→ bench-check`) or drop the
> flag and state the free ranges in the mail instead.

### 5. Draft Einsatzvertrag (preview → confirm)
For each confirmed match: call `manage-assignment-contract` with
`confirmed: false` — show the draft (employee, client, timeframe, position,
hourly rate) to the operator. Only execute with `confirmed: true` after explicit
approval.

Resolve the correct `model_type` for Einsatzverträge via `list-model-types`
beforehand — do not hardcode.

**Only send `discount_percent` when the operator actually agreed a Nachlass.** With it set, the
`billing_rate` you send is read as the **regular** rate and the agreed one is derived from the
two — and the `create` preview still shows the undiscounted figure, so the rate you present
would not be the rate the contract gets. A matching draft prices at the plain agreed rate;
concessions (incl. the 100 % unentgeltliche Überlassung) belong to
`→ manage-contract-lifecycle` step 2, which spells out the rules.

The `create` parameters (timeframe, Stundenregelung) describe the contract's **first Einsatz**
and seed it automatically. A skeleton draft from matching is fine here, but it cannot be sent
to the client until that Einsatz has an Abteilung, an Ansprechpartner vor Ort, a
Stundenregelung and a Dienstplan decision — `manage-contract-lifecycle` step 2 fills these in
via `action: "manage_einsatz"`. Flag the gap in the review task rather than guessing values.

When the match answers a `StaffingDemand` (`0-415`), its Abteilung may exist only as
`company_department_text` (the name the inbound source reported) with no
`company_department_id` — a machine-channel demand usually has no linked Abteilung. That text
does **not** satisfy the Einsatz's `company_department_id`: check the company's Abteilungen
(`0-107`) for a match by name and, if none exists, have the operator confirm the department
before one is created. Do not silently turn a reported string into master data.

When you do find one by name, **read `archived_at` on it** (`fields: ["name", "code",
"archived_at"]`). A client can retire an Abteilung by archiving it, and nothing on our side
blocks the retired one afterwards: it is still returned by `search-model` (`archived_at` is not
a default display column) and still accepted as an Einsatz's `company_department_id`. Confirm an
archived Abteilung with the operator instead of putting it on the draft — details in
`→ manage-contract-lifecycle`, mechanics in `→ using-alluvo-operator`.

A later match of the **same employee to the same client** (a follow-on period, another ward)
does not need a second contract: add an Einsatz to the existing AÜV instead
(`action: "manage_einsatz"`, `sub_action: "add"` — or `"extend"` for a seamless follow-on
period; see `manage-contract-lifecycle` step 2). Check for an existing draft/active AÜV for
that employee + company before creating a new one.

> **A signed Rahmenvertrag is only needed to commission, not to approve or send.** The
> draft Einsatzvertrag can be approved and sent to the client for signature regardless of
> the matched Rahmenvertrag's stage — a standalone AÜV signs through the portal like any
> other. A signed Rahmenvertrag (covering the assignment's staffing role and period) only
> matters if the Disponent later wants to use the `commission_as_agreed` shortcut instead
> of sending for signature (in `manage-contract-lifecycle`) — that call fails with
> `FRAMEWORK_CONTRACT_REQUIRED` without one.

### 6. Create review tasks (preview → confirm)
One task per drafted Einsatzvertrag, all in **one** `bulk-manage-model` call with
`model_type: "0-5"` (Task) — one `operations` entry per contract (max 50), not a loop of
single creates. Per `data`: `title`, `body`, `owner_id` (the Disponent; defaults to the
authenticated user), `due_at`, and `attachments: [{type_id, id}, …]` so the task hangs off
every record it concerns at once — the Employee (`0-2`), the client Company (`0-3`) and
the AssignmentContract (`0-31`).

`due_at` on this path is an ISO datetime **with an explicit offset**
(`2026-07-22T09:00:00+02:00` or `...Z`), not `manage-task`'s tenant-local `Y-m-d H:i`.

Preview with `confirmed: false`, show the operator the full list, then repeat the
identical call with `confirmed: true` — all operations run in one transaction.

## Output
- Match matrix: employee → suitable clients (with rationale)
- List of generated profile URLs (clickable: Name + ID)
- Status per Einsatzvertrag: draft created / pending
- Open follow-up tasks for the Disponent

## Related skills
- `→ bench-check` — the upstream prioritized candidate list.
- `→ profilvertrieb` — when no Rahmenvertrag client fits, pitch the profile to new companies.
- `→ manage-contract-lifecycle` — finalize the drafted Einsatzvertrag through to `won`.
- `→ intake-personalbedarf` — capture the client demand this match answers.
