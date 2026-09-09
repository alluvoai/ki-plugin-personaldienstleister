---
name: enroll-outreach
description: Enroll qualified companies in automated Outreach sequences and manage the enrollment lifecycle (create, check status, pause, resume, unenroll). Use this skill when the operator says "Unternehmen in Sequenz aufnehmen", "Outreach starten für Firma X", "enroll company in outreach", "Sequenz pausieren", "resume outreach", "attach profile", or wants to manage automated outreach enrollment for cold leads.
---

# Outreach Enrollment (Sequence Management)

## Purpose
Enroll qualified leads in automated email/outreach sequences, attach the matching
employee's profile link, and control enrollment status throughout the sequence lifecycle.

> All write steps are two-stage: `confirmed: false` (preview) →
> get confirmation → `confirmed: true`.

**Sequence, not conversation.** This skill is for *automated, multi-step* outreach to a cold
lead. A single hand-crafted pitch belongs in `→ profilvertrieb` (`manage-1on1-email`); a plain
one-to-one conversation with a known Contact that the team should see and answer in a shared
inbox is `manage-ticket` `action: "create"`, `mode: "email"` (`→ clean-inbox`) — it opens a
ticket instead of a sequence, and the reply comes back into that ticket.

## Prerequisites
- Company is already recorded in alluvo (run `→ prospect-companies` first if needed).
- Matching employee is known (name / ID, model type `0-2`).
- alluvo MCP tools (`mcp__alluvo__*`) are available.
- `manage-outreach-enrollment` belongs to the **Vertrieb** module. Without it the tool
  is absent and calling it answers `MODULE_LOCKED` — relay that German message verbatim
  (required Tarif + Testphase link) and offer a single, hand-written approach via
  `manage-1on1-email` instead of an automated sequence.
- The **sending user has an active connected mailbox**. Both `create` and `bulk-enroll`
  check this first, before anything else — on `create` even the `confirmed: false` preview
  is refused. See "Which mailbox has to be connected" below.

> ### Which mailbox has to be connected
>
> **Gmail *or* Outlook / Microsoft 365 — both satisfy the gate.** The check is whether the
> connection can send, not who the provider is, so never tell an operator to connect Gmail
> specifically. (IMAP exists as a provider but cannot send, so it does not count.)
>
> The gate applies to the **effective sender**: `sender_user_id` when set, otherwise the
> authenticated user. So when a manager enrolls on a colleague's behalf (`→ head-of-sales`),
> it is the **colleague's** mailbox that must be connected — the operator's own does not
> cover for it, and the error names that user instead of "You".
>
> Without one the tool answers, before any write:
> `<You | Sender "<name>" (#<id>)> must connect a mailbox before enrolling. Go to Settings → Email to connect.`
>
> Relay that and point at Einstellungen → E-Mail. Do not retry, and do not quietly swap in a
> different sender — an enrollment's `From` is a deliberate choice.

## Steps

### 1. Clarify inputs
Ask the operator:
- **Company** — name or ID (Company `model_type` via `list-model-types`)
- **Employee** — whose profile should be attached?
- **Action** — Enroll new / Check status / Pause / Resume / Unenroll

### 2. Check existing enrollment
Call `search-model` (or `query-model`) on `model_type: "0-125"`
(StaffingOutreachEnrollment) filtered by `company_id` — and by `contact_id` too when you
already know the addressee. Shows whether the company is already in a sequence and its
current `status` (`active` / `paused` / `completed`). Prevents double-enrollments.

```
query-model model_type:"0-125"
  fields:["id","company_id","contact_id","status","enrolled_at","sent_emails_count",
          "draft_emails_count","next_scheduled_emails_scheduled_for_min"]
  filter_groups:[{conditions:[{field:"company_id",operator:"eq",value:<company_id>}]}]
```

> `manage-outreach-enrollment` no longer has a `check` action — the tool now only creates
> (`create`, `bulk-enroll`). Reading, counting and "does one already exist for this
> contact+company pair" all run on `0-125` via `search-model` / `query-model` /
> `count-model`. Use `count-model` when you only need the yes/no.

> **Also check for a sibling/duplicate company.** A `new` record can be a duplicate of one
> already in an `open_deal` (same name root / parent-child / shared address) — enrolling it
> would cold-pitch into a live deal. Search the name root/address; if you find one, surface
> a duplicate warning and route to `→ merge-duplicate-companies` before enrolling. (See
> `→ profilvertrieb` Step 4.)
>
> **Confirm there is a usable contact.** An enrollment that sends email needs an addressee —
> verify the company has a decision-maker contact (Contact `0-105` / PortalMembership
> `0-430` filtered by `company_id`); if none, resolve/enrich one first.
>
> **Fachliche Eignung gate (#980).** Before enrolling, check the `EmployeeStaffingOpportunity`
> (0-126) for this employee↔company pair: read its top-level `specialty_fit`
> (`suitable` / `conflict` / `unknown`) and `meta.specialty_fit_reason`. **Never enroll a
> `conflict` match** — the facility's clinical focus doesn't match the employee's
> specializations (e.g. an adult-ICU nurse vs. a dedicated children's clinic), and a pitch
> would assert a false suitability (AÜG §12 credibility risk). On `suitable`, the sequence
> copy may reference only a department the employee's specializations actually cover; on
> `unknown`/absent, keep the attached-profile messaging general — no specific department claim.

> **Account-potential advisory.** `manage-outreach-enrollment` (`create` preview and the
> created-enrollment response — the retired `check` action no longer carries it) surfaces a
> non-blocking ⚠️ warning when the company's `account_potential` is `do_not_invest`. It never blocks enrollment, but treat it like the
> existing lead-status warning: surface it to the operator before proceeding rather than
> enrolling silently. `account_potential` (`expand` / `maintain` / `do_not_invest`) is also
> filterable/readable on Company (`0-3`) if you want to check it ahead of time.

### 3. Fetch employee profile URL
Call `get-profile` with `resource: "url"`, `model_type: "0-2"`, the employee's
`model_id`, and `link_type: "public_url"`. Returns the signed Talent Hub profile link
used as an attachment / CTA in the sequence. Never use `link_type: "completion_link"`
here — that link is candidate-only and outbound sends containing it are blocked.

> `get-profile-url` was merged into `get-profile`; pass `resource: "url"` and use
> `link_type` where you used to pass `action`. The values (`public_url`,
> `completion_link`) are unchanged. `resource: "url"` **writes** — it persists or
> refreshes the token row behind the link — so don't treat it as a pure read.

> **A sequence carries the profile as a link, never as a PDF.** The profile PDF
> (`profile_pdf_employee_ids`) exists only on the 1:1 email tool `manage-1on1-email`;
> `manage-outreach-enrollment` has no equivalent parameter. If the client wants the profile
> as a file, that is a hand-crafted single email (`→ profilvertrieb`, Step 6b), not a
> sequence step — which is the right split anyway: a permanent, untracked snapshot carrying
> the person's full surname does not belong in automated multi-step outreach.

### 4. Prepare enrollment action (preview)

**Enrolling** is `manage-outreach-enrollment`. **Everything after enrolling** is a record
action or a plain read — the tool was trimmed to creation only, so route by intent:

| Intent | Call |
|--------|------|
| Enroll one company (there is no `enroll` action — it is `create`) | `manage-outreach-enrollment` `action: "create"`, `confirmed: false` → `true`: `company_id`, `contact_id` (auto-selected if omitted), `selling_profile_id` (there is no `sequence_id` parameter), profile attachment (`attach_profiles_mode`, `primary_employee_id`, `staffing_requirement_id`, `explicit_employee_ids`, `with_availabilities`) |
| Enroll many companies | `manage-outreach-enrollment` `action: "bulk-enroll"` with `company_ids` (max 50); shared params apply to all |
| Look up status / list / count / "already enrolled?" | `search-model` / `query-model` / `count-model` on `model_type: "0-125"` (read-only) |
| Pause a running sequence | `manage-record-action` `operation: "execute"`, `model_type: "0-125"`, `record_id: <enrollment_id>`, `action: "pause_enrollment"` |
| Resume a paused sequence | same call with `action: "resume_enrollment"` |
| Unenroll (stop permanently) | same call with `action: "complete_enrollment"` |

The three lifecycle record actions are **snake_case** (`pause_enrollment`,
`resume_enrollment`, `complete_enrollment`) — unlike most hyphenated action names. There is
no `unenroll` action name any more: unenrolling *is* `complete_enrollment`, and it is
**irreversible**, unlike `pause_enrollment`. `pause_enrollment` is offered only on an
`active` enrollment, `resume_enrollment` only on a `paused` one — run
`manage-record-action` `operation: "list"` with the `record_id` if you are unsure which is
currently available and why.

Bulk lifecycle changes go through the same tool with `operation: "execute_bulk"` and
`record_ids: [...]` (max 100) instead of `record_id` — there are no `bulk-pause` /
`bulk-resume` / `bulk-unenroll` actions on `manage-outreach-enrollment` any more. Preview and
confirm the full list before any bulk write.

`create` returns a preview: which sequence, which employee, next scheduled step. A record
action previews the same way — `confirmed: false` (or omitted) shows the computed effect and
writes nothing, `confirmed: true` executes.

> **Which profiles the email attaches is decided by precedence, not by the mode name.**
> `create` resolves a profile list and stores it on the enrollment; each draft then takes the
> first branch that applies:
>
> 1. **hand-picked list** — `explicit_employee_ids`, or the list `create` derived. **Every** id
>    in it is rendered; a `primary_employee_id` only floats to the front, it never shrinks the
>    list to that one person.
> 2. **pinned primary, no usable list** — exactly **one** profile. A linked
>    `staffing_requirement_id` is *not* consulted on this branch.
> 3. **requirement** — `staffing_requirement_id`, no list and no primary → up to **3**
>    requirement matches, each carrying its own hourly rate, plus the requirement itself in the
>    email context.
> 4. **segment** — `attach_profiles_mode` other than `none` → up to 3 diverse candidates near
>    the company.
>
> So to pitch a pinned bench profile *together with* requirement matches, pass
> `attach_profiles_mode: "advanced"` **and** `primary_employee_id` **and**
> `staffing_requirement_id` — `create` then stores the primary plus 2 matches as the hand-picked
> list (branch 1). `advanced` **without** a `staffing_requirement_id` silently falls back to
> segment matching (branch 4); no error is raised, so check the preview rather than assuming the
> requirement was applied.

> **A requirement-linked enrollment now actually sends (fixed 2026-08).** The requirement branch
> used to throw on every non-empty match set, so the scheduling job failed and the email never
> went out — enrolling with a `staffing_requirement_id` silently produced nothing. That is fixed:
> treat such an enrollment as a live sequence, and preview it like any other before confirming.

> **`attach_profiles_mode: "none"` does not suppress profiles when a requirement is linked.**
> With `none`, no primary and a `staffing_requirement_id`, the draft still resolves branch 3 and
> renders up to 3 requirement-matched profiles. For a pure "introduce our staffing services" mail
> with no profiles at all, leave `staffing_requirement_id` unset too.

> **The requirement branch only ever surfaces verleihfrei employees.** `create`'s pre-selection
> and the draft-time requirement matching both exclude anyone with a running assignment, so the
> previewed profiles are exactly the ones that go out — approve the draft as previewed, there is
> nothing to sort out by hand.
>
> What is *not* re-checked is a list already stored on the enrollment (branch 1): those ids are
> frozen at `create` time and rendered as-is by every later touchpoint. So an employee placed
> after the enrollment started can still appear in a scheduled follow-up. Re-check the profiles
> when reviving or extending an older sequence — not when approving a fresh draft.

### 5. Get confirmation
Show the preview to the operator. Ask explicitly:
"Shall I [start / pause / resume / end] the enrollment now?"

### 6. Execute
Call the same tool again with `confirmed: true` and identical parameters —
`manage-outreach-enrollment` for a new enrollment (returns enrollment ID and the next
scheduled touchpoint), `manage-record-action` for a pause / resume / unenroll.

### 7. Add a note (recommended)
Call `manage-activity` with `activity_type: note`, `action: create`,
`subject_type: "0-3"` and the company's `subject_id`
(`confirmed: false` → `confirmed: true`):
`[Outreach] Sequence started – profile <EmployeeName>`, so the BDR can see
in the timeline feed when and why the sequence was triggered.

## Status overview

| Status | Meaning | Recommended action |
|--------|-----------|-------------------|
| Active | Running as scheduled | Wait or add a manual touch |
| Paused | Temporarily stopped | `resume_enrollment` record action when ready |
| Positive response | Reply / interest received | `manage-client-prompt` (MCP prompt) for client onboarding |
| Completed | Sequence finished | Document outcome in a note |

## Output
- Current enrollment status of the company
- Enrollment ID + next scheduled touchpoint (for active sequences)
- Profile URL of the attached employee
- Follow-up action: `manage-client-prompt` (MCP prompt) on a positive signal,
  `→ log-company-signal` on a new trigger

## Related skills
- `→ profilvertrieb` — the end-to-end pitch job this enrollment step belongs to.
- `→ prospect-companies` — build the qualified shortlist before enrolling.
- `→ merge-duplicate-companies` — when the duplicate/sibling check fires.
- `→ log-company-signal` — record the trigger that justified the enrollment.
- `→ clean-inbox` — writing a single Contact as a tracked ticket instead of enrolling them.
