---
name: call-summary
description: Capture and process call notes — structure raw notes or a transcript, save as a Call/Note in the CRM, create Action Items as tasks, and draft a follow-up email. Always writes with preview first. Use this skill when the operator says "Gesprächsnotiz erfassen", "Call nachbereiten", "fasse das Gespräch zusammen", "Notizen vom Telefonat", "log this call", "call summary", "summarize my call", or "write the follow-up".
---

# Capture and Process Call Notes

## Purpose

Turn raw notes or a transcript into a structured summary, save it as an activity
(Call or Note) in the CRM, create all Action Items as tasks, and draft a follow-up
email — all without opening the alluvo UI.

> **WRITING** — every write step is two-stage: first `confirmed: false` (show preview),
> then ask for explicit confirmation, then execute with `confirmed: true`.
> Only `mcp__alluvo__*` tools are used. No shell, no web, no file I/O.

## Prerequisites

- Raw call notes or transcript from the operator.
- Name or ID of the relevant company (type `0-3`) and/or contact (type `0-105`) — or,
  for a conversation about a specific contract, the Rahmenvertrag (`0-30`) or
  Einsatzvertrag (`0-31`).
- alluvo MCP (`mcp__alluvo__*`) connected and authorized.

## Steps

### 1. Resolve references

Identify the company and contact in the CRM:

- Company: `search-model` with `model_type: "0-3"` and the company name.
- Contact: `search-model` with `model_type: "0-105"` and the contact name (optionally
  filtered to the company). If multiple matches — let the operator choose.

> Note: Activities to be linked to an employee must be saved on the associated
> **Contact** (`0-105`), not on the Employee record.

**A Vapi-handled inbound call is already logged — don't duplicate it.** An inbound call
answered by the phone assistant is automatically recorded as a `call` activity (with
direction, outcome, duration and full transcript) the moment the ticket is created — before
the operator ever runs this skill. Check `get-timeline` on the contact/company for a Call
entry matching the conversation's time before creating a new one; if it's already there,
this skill's "raw notes" are the transcript itself, and step 3 becomes `action: "update"` on
that `engagement_id` (e.g. to fill `title`/`body` with the structured summary) rather than
`action: "create"` — a second `call` record for the same conversation is a duplicate on the
timeline.

### 2. Structure the content

Extract the following blocks from the notes / transcript:

| Block | Content |
|---|---|
| **Summary** | 2–4 sentences: What was discussed, what is the outcome? |
| **Discussion points** | Bullet points covering topics, questions, answers |
| **Priorities / requirements** | Mentioned positions, volumes, timelines |
| **Objections / risks** | Pricing concerns, existing suppliers, reservations |
| **Competitive signals** | Named competitors or alternative providers |
| **Action Items** | Concrete next steps with owner and due date |

### 3. Create the activity

Use `manage-activity` with `activity_type: call` (for a phone call) or
`activity_type: note` (for a written note), plus `action: create`. The subject is
addressed as `subject_type` + `subject_id` — `0-105` for a Contact, `0-3` for a
Company, `0-30` for a Rahmenvertrag, `0-31` for an Einsatzvertrag (AÜV). Activities
about an Employee or Candidate are logged on the **linked Contact**, never on the
Employee record.

> Pick the subject by what the conversation was *about*: a relationship call goes on
> the person (`0-105`), account-wide news on the company (`0-3`), and a conversation
> about one specific contract on that contract (`0-30` / `0-31`) — contracts have their
> own timeline. A contract activity does **not** roll up to the client's company
> timeline, so if the account owner needs to see it, log it on the Company instead.
> Contract subjects also return no follow-up suggestions — derive Action Items yourself
> in step 4.
>
> **A written note has a wider reach than a call.** `activity_type: note` additionally accepts any
> record type that carries notes — a Stundennachweis (`0-426`), for instance — so a remark about one
> specific record goes **on that record** instead of on the person it is loosely related to. The list
> is derived, not hand-kept: `list-model-types` confirms an id, and a rejected `subject_type` names
> the accepted ones. `call` and `meeting` stay on Contact / Company / contract, because a
> conversation happens with a person, an organisation or against a contract.

1. `confirmed: false` — show preview with `title`, `body` (structured summary),
   `subject_type` / `subject_id`, and `owner_id`. The `owner_id` defaults to the logged-in user;
   the activity can be assigned to another BDR on explicit request only (note: the
   MCP has no true impersonation — the write is attributed via `owner_id`, but
   permissions remain the authenticated operator's own; show the attribution in
   the preview).
2. Present the preview: "Should I save the call now?"
3. `confirmed: true` — save the activity. Output the engagement ID and timestamp.

For a call, `direction` (`inbound`/`outbound`) and `outcome` (`connected`,
`no_answer`, `left_voicemail`, `busy`, `wrong_number`) are required on create; for
a note, `body`. If the conversation actually happened inside an already-scheduled
meeting, the preview flags it — prefer `activity_type: meeting`, `action: update`
(set `outcome` + `internal_notes`) over creating a second record.

> **What the returned "Recommended Follow-ups" block will and will not propose.** Saving a call
> or note runs the tenant's call-notes classifier and appends its suggestions to the response
> (`suggest_follow_ups: false` skips it — worth it for bulk logging). Nothing there is executed
> server-side: you carry each one out yourself with the normal tools, after confirming with the
> operator. Its policy, so you can say why a suggestion is missing rather than inventing one:
>
> - **No Rückruf task when the notes document disinterest** — "nicht interessiert", "kein Bedarf
>   mehr", "bitte nicht mehr anrufen", "hat abgesagt" — *even with* `outcome: "no_answer"`. The
>   text beats the outcome. The right follow-up there is a lead-status change (`manage-model`),
>   never a call task that contradicts what was just recorded.
> - **No task that only records what you just wrote.** "Outcome protokollieren", "Ergebnis
>   dokumentieren", "Gespräch festhalten", "Status im CRM aktualisieren" are refused as duplicate
>   work — the activity from step 3 *is* that documentation. A task is only right when it demands
>   something still outstanding and beyond noting: call someone, send papers, prepare a contract.
>   A data change is a `manage-model` write instead. Hold your own Action Items in step 2 to the
>   same bar.
> - **The Rückruf `due_at` follows tenant settings, not a fixed hour.** Before
>   `ai_takeover.callback_same_day_cutoff_hour` (default 16:00, tenant-local) it proposes a
>   same-day retry `callback_retry_after_hours` (default 3) later, deliberately at a different
>   time of day; from that hour on, the next workday. Both are tenant-editable, as is who is
>   responsible for which topic (`task_routing_instructions`) — `→ build-automation-agent`.

### 4. Create Action Items as tasks

A debrief usually yields several action items, and a call's follow-up normally concerns
both the person and their company. Create them all in **one** `bulk-manage-model` call
with `model_type: "0-5"` (Task) — not a loop of single creates:

1. `confirmed: false` — preview `operations: [{ action: "create", data: { … } }, …]`
   (max 50 per call). Per `data`: `title`, `body`, `owner_id` (defaults to the
   authenticated user — set it only to delegate), `due_at` when a due date was mentioned,
   and `attachments`.
2. `attachments: [{type_id, id}, …]` takes any number of entries of **different** types,
   so one task can hang off the Contact **and** the Company:
   `[{"type_id": "0-105", "id": <contact>}, {"type_id": "0-3", "id": <company>}]`.
   For a follow-up tied to a person, always use the person's Contact (`0-105`) — never
   their Employee (`0-2`) record. Other types seen in this flow: `0-81` Candidate,
   `0-31` Einsatzvertrag, `0-30` Rahmenvertrag.
3. **`due_at` here needs an explicit timezone offset** — `2026-07-22T09:00:00+02:00` or
   `...Z`. That is *not* the tenant-local `Y-m-d H:i` that `manage-task` takes; the two
   formats are not interchangeable and a bare local string is rejected. Same for
   `reminded_at` and `wait_until`.
4. Summarize all tasks compactly and ask for joint confirmation
   ("Should I create these tasks now?"), then repeat the identical call with
   `confirmed: true`. All operations are validated upfront and run in one transaction —
   if one fails, none are written.

Stay on `manage-task` (single record, tenant-local `Y-m-d H:i`, `confirm_token` replay)
only for the cases the bulk path does not cover: a follow-up that must genuinely **recur**,
or a task that must appear in a ticket thread (`ticket_id`).

> The bulk path does now persist `repeat_interval` / `repeat_frequency` / `repeat_until` on
> `0-5` — it used to drop them silently — but it cannot set **`is_repeating`**, which has no
> validation rule and comes back in the write's ⚠️ IGNORED FIELDS block. Without that flag the
> scheduler never spawns the next instance, so a repeat schedule written through
> `bulk-manage-model` never fires. `manage-task` `action: "create"` with `repeat_interval` sets
> the flag itself (and defaults `repeat_frequency` to 1); no MCP path makes an *existing* task
> repeating (alluvo#4519).

### 5. Draft the follow-up email

Create an email draft with `manage-1on1-email`:

- **`body_html` must be real HTML — never escape the tags.** `<p>…</p>` paragraphs and
  `<br>` for hard line breaks (plain text with `\n\n` separators is also accepted; never
  mix the two styles in one body). An escaped body (`&lt;p&gt;` instead of `<p>`) shows
  its own tags to the recipient. `draft` and `update` repair an escaped body once and add
  a warning line containing `HTML-escaped` to the preview and to the response after the
  write — if it appears, fix the composing step instead of shipping the draft on the
  repair.
- **Saved template?** If the tenant keeps follow-up templates, pass `template_id` on
  `draft` to start from one — discover them via `search-model` on the `email-templates`
  model type (`"0-418"`; fields incl. `name`, `category`, `language` `de`/`en`,
  `is_active`; only **active** templates that are shared or your own are usable). The
  template's `{{root.field}}` placeholders render against the resolved contact/company
  before the draft is created. Roots: `contact.*` (incl. `greeting`, which resolves the
  du/Sie salutation through the formality chain — prefer it over hand-writing a
  salutation into a template), `company.*` (incl. `portal_link`, the client-portal URL),
  `user.*` (incl. `signature`), `tenant.*`. An explicit `subject` or `body_html`
  overrides the rendered value **for that field only** — not all-or-nothing. Any
  placeholder that cannot resolve (unknown key, or an empty value — e.g. `company.name`
  when the contact hangs off no company) is listed in the preview, and a
  `confirmed: true` write is **refused** naming the keys until it is fixed: override
  that field explicitly, or pass a `company_id` that fills the gap.
- Check `get-timeline` beforehand for any prior correspondence — use it to determine the
  correct salutation (first name vs. last name, formal vs. informal tone). When the
  recipient contact is known, query **that contact** (`subject_type: "0-105"`); a company
  timeline (`0-3`) does not roll up its contacts, so activities logged on the person alone
  will be missing from it. Fall back to the company only when no contact is identified.
- **Never carry our own engagement tracking into the draft.** Opens, clicks and profile views
  are internal-only — use them to decide what to do next, never tell the recipient about them
  ("Sie haben die Mail zweimal geöffnet"), not even as a friendly opener. They are also often
  wrong: an open can come from a forward or an image proxy. The risk here is specific — a call
  note or an internal task may state the number in plain prose, and the `get-timeline` you just
  read hands those bodies back verbatim; a sentence being in the timeline does not make it safe
  to reuse. `draft` and `update` **refuse** a `confirmed: true` write whose body contains such a
  phrase (or `Öffnungsrate`/`Klickrate`/`Tracking`), and the unconfirmed preview flags the exact
  phrase with `Confirming this body as-is will be refused.` That refusal is a **content
  correction, not a technical error**: rewrite the passage around what was actually discussed
  and agreed on the call, then confirm — never re-confirm the same body. `send` and `schedule`
  re-check the **stored** body and refuse it too, so an older draft cannot slip out: that
  refusal arrives **without `confirmed`** (even the preview is refused — sending passes no new
  text to correct), and the only fix is `action: update` on the same `email_id`, then send —
  never a second draft. That repair needs the draft to be **yours**: `update` requires
  `emails.edit` on the record, or `emails.create` plus ownership of the draft, and otherwise
  refuses with `You do not have access to update this email.` (alluvo#4780). An older draft
  somebody else wrote has to go back to them — details in `→ profilvertrieb` Step 6b.
- **A Nachweis the client asked for on the call** can ride along: pass
  `employee_document_ids` on `draft`, `update`, `reply`, `reply-all` or `forward` —
  EmployeeDocument ids (`0-346`, from `manage-employee-document` `action: "audit"`), not
  media ids. Only
  document types the tenant has released for sending are accepted and that list is **empty by
  default**, so attempt it and relay the refusal instead of promising the operator it will
  work; one unattachable id rejects the whole call and writes nothing. Read the preview's
  employee, type and file list out before confirming — this is personnel data going to a
  client. Full rules: `→ profilvertrieb`.
- **If the call was itself a reply to the client's mail**, answer with `reply` /
  `reply-all` (`reply_to_email_id` + `body_html`) rather than a fresh `draft` — recipients and
  the `Re:`-subject come from the parent, and the attachment parameters work there too. Your
  body is stored as-is, so quote the original yourself if the answer needs it. Details in
  `→ profilvertrieb` Step 6b.
- **"Schicken Sie mir das Profil" on the call → link or PDF, and say which.** The public
  profile link stays the default. If the client explicitly asked for a *file*, attach
  alluvo's profile PDF: `profile_pdf_employee_ids` (or `profile_pdf_candidate_ids`) on
  `draft`, `update` or any reply action, rendered fresh when you confirm — nothing to
  generate beforehand.
  `profile_pdf_show_assignments` (default false) adds the Einsätze. Understand the trade
  before you offer it: the PDF is a permanent snapshot carrying the person's **full**
  surname (the link abbreviates it), and it cannot be withdrawn or tracked once sent. The
  full decision rule is in `→ profilvertrieb`.
- Write the email in the operator's preferred language: factual opening, brief summary
  of discussed points, clear next steps / CTA.
- Present the draft (subject + body) to the operator for approval before saving or
  sending.

## Output

**Internal summary**
Structured overview of the conversation (summary, discussion points, objections,
competitive signals).

**Action Item table**

| Task | Owner | Due |
|---|---|---|
| … | … | … |

**Email draft**
Subject + full email body.

## Related skills

- `→ call-prep` — Prepare for the next conversation with this company/contact.
- `→ enroll-outreach` — Enroll the contact in an outreach sequence if no active
  enrollment is running yet.
- `→ manage-contract-lifecycle` — If the conversation produced concrete contract topics,
  move directly to the contract workflow.
- `→ build-automation-agent` — Change what the call-notes classifier proposes: callback hours
  and task responsibilities live in `manage-settings`, group `ai_takeover`.
