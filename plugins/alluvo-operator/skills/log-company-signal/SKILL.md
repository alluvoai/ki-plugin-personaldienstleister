---
name: log-company-signal
description: Record a hiring, expansion, funding, product-launch, partnership, or leadership-change Signal on a company. Use this skill when the operator says "Signal loggen", "Firma stellt gerade ein", "Neueröffnung in Köln", "log a signal", "company is expanding", "funding round", "new location", "neue PDL", or wants to record any buying or market trigger on a company record.
---

# Record a Signal (Company)

## Purpose
Capture market and buying signals at the company level so that Disposition and BDRs
never miss the right moment to make contact or start Profilvertrieb.

> **MUTATING.** Writes one Signal record via the `log-signal` record action on the
> company (`manage-record-action`); always two-stage — preview (`confirmed: false`)
> → operator approval → `confirmed: true`.

## Prerequisites
- Company is already recorded in alluvo.
- alluvo MCP tools (`mcp__alluvo__*`) are available.

## Steps

### 1. Clarify inputs
Ask the operator (if not already provided):
- **Company** — name or ID
- **Signal type** — see table below
- **Details** — source, scope, context (1–2 sentences)

### 2. Log the signal (preview)
Signals are logged through the **`log-signal` record action on the company**, not a
tool of its own: `manage-record-action`, `operation: "execute"`, `model_type: "0-3"`,
`record_id: <company>`, `action: "log-signal"`, with the signal itself in `data`:

- `type` — **required.** One of the six values in the table below.
- `title` — **required.** Short headline, ≤ 500 characters.
- `description` — optional free text (source, scope, context).
- `metadata` — optional object for structured extras.
- `signals` — optional child entries `[{title, description?, source_url?}]`; each
  `title` is required, `source_url` must be a real URL.
- `contact_ids` — optional contact IDs to link to the signal.

Preview with `confirmed` omitted (or `false`). Nothing is written; the response echoes
company, type, title, description, the child-signal count, and the contacts to link.

### 3. Get confirmation
Present the preview. Ask explicitly: "Shall I save the signal now?"

### 4. Execute
Repeat the call with `confirmed: true`. Returns the signal group ID and title. Logging
the same signal twice does **not** create a duplicate — the action deduplicates by
fingerprint (company + type + title) and refreshes `last_seen_at` on the existing group
instead, reporting `deduplicated: true`. Say so when that happens rather than reporting
a fresh signal.

Writing a signal requires the `signals.create` permission; without it the action is
listed as unavailable with that reason.

## Signal types

The valid types (enforced by the action — anything else is rejected):

| Type | Example |
|-----|---------|
| `hiring` | Job posting for nursing staff spotted |
| `expansion` | New location / department opened |
| `funding` | Investment round closed |
| `product_launch` | New service line / offering announced |
| `partnership` | New cooperation / network membership |
| `leadership_change` | New PDL / new HR manager |

Not a signal type: "first contact / ICP-qualified" or a re-engagement after a pause —
record those as a note (`manage-activity` with `activity_type: note`,
`action: create`, preview → confirm) or update the lead status
instead.

## Output
- Signal group ID · type · company (name + ID), plus whether it was newly created or
  deduplicated onto an existing group
- Suggested follow-up action

## Related skills
- `→ enroll-outreach` — if no active enrollment is running for this company.
- `→ profilvertrieb` — if the signal makes the company a hot target for a profile pitch.
- `→ account-research` — build the internal dossier before making contact.
- A concrete callback appointment can be created as a task via the `manage-task` tool
  (preview → confirm).
