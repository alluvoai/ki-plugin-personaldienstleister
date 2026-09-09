---
name: daily-briefing
description: Daily briefing — what's on today: upcoming meetings, due tasks, Outreach replies, pipeline alerts, and top priorities pulled from your own alluvo data. Use this skill when the operator says "was steht heute an", "Tagesbriefing", "mein Tag", "Tagesüberblick", "was ist heute wichtig", "daily briefing", "what's on today", "my day", or "morning briefing".
---

## Purpose

A prioritized daily overview for the logged-in operator — usable across roles,
whether Disponent, Recruiter, or BDR. The skill aggregates due tasks, today's
meetings, waiting Outreach replies, and pipeline signals into a compact, action-oriented
summary so the workday starts structured.

> **READ-ONLY.** This skill does not modify any data. Only `mcp__alluvo__*` tools
> are used — no shell access, no files, no web.

---

## Prerequisites

- alluvo MCP is connected.
- The skill works by default for the **logged-in user** (`owner_id` = own user ID from `0-1`).
- No additional parameters required; the operator can optionally specify a different date
  or a different person.

---

## Steps

Run all steps sequentially. Do not abort if a single step returns no results — note it
as "nothing found" and continue.

**1. Fetch due and overdue tasks**

Call `mcp__alluvo__query-model` with `model_type: "0-5"` (Task) and one `filter_groups`
condition set for the logged-in user's still-open work:

```
query-model model_type:"0-5"
  fields:["id","title","body","status","type","priority","due_at","owner_id"]
  filter_groups:[{conditions:[{field:"owner_id",operator:"eq",value:<current_user_id>},
                              {field:"status",operator:"in",value:["not_started","in_progress"]},
                              {field:"due_at",operator:"lte",value:"<today 23:59>"}]}]
  sort_by:"due_at" sort_dir:"asc"
```

`get-open-tasks` was retired — `query-model`/`search-model` on `0-5` is the whole surface now.
`owner_id` is **not** implicit here the way it was on the old tool: without that condition you
get every user's tasks, so always set it (and drop it deliberately when the operator asks for
the team's view). Task status is `not_started` / `in_progress` / `completed`; there is no
separate "open" flag.

Key fields: `title`, `due_at`, `priority`, `type`, and the linked record (e.g. employee or
company) — load the attachments via `include` or `get-model` on the task.

`query-model` returns the task `body` in full rather than the excerpt the old tool cut at
~150 characters, so budget for long bodies: keep `fields` narrow, or omit `body` in the
listing pass and read it with `get-model` only for the tasks you actually brief on.

**2. Load today's meetings**

Call `mcp__alluvo__query-model` with `model_type: "0-201"` (Meeting). Filter for
meetings whose **`start_at`** falls within today's calendar day and that belong to the
logged-in user or where they are a participant. Sort chronologically. (The field is
`start_at` — confirm available filters via `get-model-schema` if unsure.)

Key fields: title, time, conversation partner/contact, notes or agenda.

**3. Check Outreach replies and waiting enrollments**

Call `mcp__alluvo__query-model` with `model_type: "0-125"`
(StaffingOutreachEnrollment). `manage-outreach-enrollment` no longer has a `stats` /
`list` action — it only creates enrollments; everything read-only rides
`search-model` / `query-model` / `count-model` on `0-125`.

```
query-model model_type:"0-125"
  fields:["id","company_id","contact_id","status","draft_emails_count",
          "approved_emails_count","sent_emails_count","open_tracking_events_count",
          "click_tracking_events_count","next_scheduled_emails_scheduled_for_min","enrolled_at"]
  filter_groups:[{conditions:[{field:"status",operator:"in",value:["active","paused"]}]}]
```

Status is only `active` / `paused` / `completed` — there is no `reply_received` status and no
`awaiting_manual_step` flag. Read "waiting on the operator" off the counters instead:
`draft_emails_count` above `approved_emails_count` means drafts are sitting unapproved and the
sequence is stalled until someone releases them. `next_scheduled_emails_scheduled_for_min` is
the next touchpoint.

Show: enrollments with unapproved drafts, paused sequences, the next scheduled touchpoints,
and the contact/company names behind them.

**4. Pipeline signals: own Einsatzverträge at a glance**

Call `mcp__alluvo__count-model` with `model_type: "0-31"` (AssignmentContract). Filter
for the logged-in user's contracts (`owner_id`). Count separately:

- Contracts **expiring within the next 14 days** (`end_date` ≤ today + 14 days).
- Contracts in **"stuck"** status or with no activity in the last 7 days (if the field
  is available).

These numbers serve as an early-warning system for expiring assignments without renewal.

**5. Prioritize and compile the briefing**

Order all collected information by urgency:

1. Overdue tasks (highest priority)
2. Today's meetings (chronological)
3. Waiting Outreach replies / manual steps
4. Pipeline warnings (expiring contracts, stalled deals)
5. Tasks due today (not yet overdue)

---

## Output

Present the briefing in a clear structure:

**#1 Priority today** — one line with the most important action of the day (e.g. "Call
Müller GmbH — contract expires in 3 days").

**Today's meetings** — times, conversation partners, any preparation needed?

**Due & overdue tasks** — compact list with due date and linked record.

**Outreach status** — number of replies and waiting steps; who should the operator
contact first?

**Pipeline alerts** — expiring Einsatzverträge, number of stalled deals.

**Suggested next steps** — 2–3 concrete actions for the morning.

> **Short mode:** If the operator says "short" or "quick summary", reduce output to:
> #1 priority, meeting list, open task count, pipeline alert count — maximum 10 lines.

> **End-of-day variant:** If the operator asks "Tagesabschluss" or "what did I
> accomplish today?", list completed tasks (finished today) and remaining open items
> that should be moved to tomorrow.

---

## Related skills

After the daily briefing, these skills are natural next steps:

- `→ call-prep` — Prepare for a specific meeting from today's list (conversation partner,
  recent activities, open points).
- `→ head-of-disposition` — Team view for Disponenten: Bench overview, which employees
  are verleihfrei today or will be soon.
- `→ head-of-sales` — Team view for BDRs / Sales: pipeline overview across all users,
  Outreach performance, open opportunities.
