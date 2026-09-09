---
name: head-of-sales
description: Sales leadership overview and BDR coordination — pipeline status, BDR performance, weighted Forecast (best/likely/worst, Commit vs. Upside, Gap-to-Quota), Pipeline-Review (stale / stuck / single-threaded / overdue), and triggering Prospecting, Outreach, or Profilvertrieb jobs for individual BDRs. Use this skill when the operator asks "how is sales going", "sales overview", "Vertriebsübersicht", "Forecast", "Umsatzprognose", "Forecast-Export", "Einsätze als CSV/Excel exportieren", "Pipeline-Review", "how are my BDRs performing", "wie performen meine BDRs", "coordinate my BDRs", "BDRs koordinieren", "head of sales". Defaults to the logged-in user; can be scoped per BDR on request.
---

# Head of Sales — Sales Overview & BDR Coordination

## Purpose

Leadership skill for business development: reports on sales (pipeline status,
weighted Forecast, pipeline risks, BDR performance) and coordinates BDRs
(triggering Prospecting, Outreach, Profilvertrieb). Delegates to job-skills rather
than re-implementing their logic — this skill is the cockpit, not the engine.

> **Read-only parts** (Reporting, Forecast, Pipeline-Review) are **READ-ONLY** and
> do not modify any data. **Coordination** is **WRITE** and always runs in two steps:
> `confirmed: false` (preview) → request confirmation → `confirmed: true`.
> Exclusively `mcp__alluvo__*` tools. No shell access, no scraping, and never build a
> file yourself. (The **Forecast-Export** below is the one download: you only *trigger* an
> MCP action — the backend generates the CSV and emails the requester the download link.)

## Prerequisites

- alluvo MCP server connected (`mcp__alluvo__*`).
- Tenant scope is active — all queries are automatically restricted to the operator's organisation.
- Quota (revenue target) is **not** an MCP field — ask the operator when needed.

---

## Reporting (read-only)

### Pipeline & Forecast

Read AssignmentContracts (`model_type: "0-31"`) using `query-model`. Relevant fields:

| Field | Meaning |
|---|---|
| `stage` | ContractStage — resolve the exact enum values via `get-model-schema` (per-stage timestamps exist as `marked_as_<stage>_at`, e.g. `marked_as_won_at` / `marked_as_lost_at`) |
| `forecast_status` | `actual` · `booked` · `committed` · `forecasted` · `lost` |
| `forecast_probability` | Probability 0–100 |
| `billing_rate` | Agreed hourly billing rate, **in EUR** (the Money cast returns euros over MCP, never cents) — the figure actually invoiced |
| `list_billing_rate` | Regular rate before a Nachlass, EUR. Empty unless the contract states a concession |
| `discount_percent` | Nachlass on the regular rate, 0–100. Empty unless a concession is stated |
| `total_hours` | Planned hours |
| `valid_from` / `valid_until` | Contract period |
| `owner_id` | Responsible BDR (User ID `0-1`) |

`stage` and `status` are **filterable** in `filter_groups`, so a stage cut ("all WON
contracts", "everything still in `offered`") is one server-side query — never page the whole
table and group client-side. `stage` stays **read-only** through the generic tools: it is a
managed lifecycle field, so `manage-model` will not write it. A stage only moves via
`manage-assignment-contract` `action: "transition"` with `target_stage`, and that belongs to
`manage-contract-lifecycle` — this skill reports, it does not move deals.

**Weighted value** per contract: `billing_rate × total_hours × forecast_probability / 100`.

**`billing_rate` stays the right multiplier even with a Nachlass** — it is the agreed rate, so
the forecast is already net of any concession. Don't rebuild it from `list_billing_rate`. But
read `list_billing_rate` / `discount_percent` alongside it whenever you *show* a rate: a
contract at 0,00 €/h is an unentgeltliche Überlassung (a stufenweise Wiedereingliederung, say),
not a data error, and it contributes 0 € to the pipeline on purpose. Name it as a Nachlass with
its regular rate rather than reporting a broken-looking zero — or flagging it to
`→ triage-data-quality`.

For a BDR breakdown, group on **`query-model`** — `aggregate: {function: "count"}` (or
`"sum"` with a `field`) plus a top-level `group_by: "owner_id"`. `group_by` is a `query-model`
parameter only: **`count-model` takes just `model_type`, `filter_groups` and `search`** and
returns a single total, so a per-BDR cut needs either `query-model` or one `count-model` call
per BDR. An aggregate call returns aggregate rows *instead of* the row list (it is mutually
exclusive with `include`), and is capped at the **top 200 groups**, ordered by the aggregate
descending.

### Activity per BDR

Activity volume per BDR over the last N days (default: 30):

```
count-model model_type:"0-202"  # Calls
  filter_groups:[{conditions:[{field:"owner_id",operator:"eq",value:<bdr_id>},
                              {field:"occurred_at",operator:"gte",value:<since>}]}]

count-model model_type:"0-200"  # Notes
count-model model_type:"0-201"  # Meetings
```

For all BDRs combined, replace the per-BDR loop above with one `query-model` call per
activity type — same `occurred_at` filter, `aggregate: {function: "count"}`,
`group_by: "owner_id"`. Output as a BDR comparison table (Calls · Notes · Meetings ·
Pipeline value).

### Outreach health

```
query-model model_type:"0-125"   # StaffingOutreachEnrollment
  aggregate:{function:"count"} group_by:"status"

query-model model_type:"0-125"
  fields:["id","company_id","contact_id","status","draft_emails_count","approved_emails_count",
          "sent_emails_count","open_tracking_events_count","click_tracking_events_count",
          "next_scheduled_emails_scheduled_for_min","enrolled_at"]
  filter_groups:[{conditions:[{field:"status",operator:"in",value:["active","paused"]}]}]
```

`manage-outreach-enrollment` has no `stats` / `list` action any more — it only creates
enrollments (`create`, `bulk-enroll`). Outreach health is read off `0-125` directly with
`query-model` / `count-model`, which also gives you cuts the old action never had (group by
`status`, filter by `company_id`/`contact_id`, aggregate the counters).

Statuses are `active` / `paused` / `completed`. Sequence progress and drop-off come from the
per-enrollment counters: `draft_emails_count` vs `approved_emails_count` (drafts waiting on an
approval — a stalled sequence), `sent_emails_count`, and the
`open_tracking_events_count` / `click_tracking_events_count` engagement pair. There is no
Selling-Profile roll-up field on the enrollment; group by `selling_profile_id` if you need the
per-profile cut and confirm the field with `get-model-schema` (`context: list`) first.

---

## Forecast capability

**Goal:** deliver a weighted revenue Forecast with scenarios and Gap-to-Quota.

1. **Read pipeline** — `query-model model_type:"0-31"` with fields `forecast_status`,
   `forecast_probability`, `billing_rate`, `total_hours`, `owner_id`, `stage`.

2. **Split Commit vs. Upside:**
   - **Commit** = `forecast_status` in `actual`, `booked`, `committed`
   - **Upside** = `forecast_status` = `forecasted`
   - **Excluded** = `lost`

3. **Calculate scenarios** from `forecast_probability`:
   - **Best Case** — all Upside deals count in full (p = 100%)
   - **Likely** — weighted Σ(billing_rate × total_hours × probability / 100)
   - **Worst Case** — Commit deals only (Upside drops out)

4. **Ask for quota** (not an MCP field): "What is the revenue quota for this period?"
   Gap-to-Quota = Quota − Likely value; positive = gap, negative = buffer.

5. **Output:**
   - KPI tiles: Total Pipeline · Commit · Upside · Likely · Gap-to-Quota
   - Scenario table: Best / Likely / Worst in EUR
   - Pipeline by stage (deal count + EUR)
   - Top-3 deals by weighted value
   - Recommendations: where is the biggest risk, where is the biggest opportunity?

---

## Forecast-Export capability (downloadable CSV)

**Goal:** hand the operator a downloadable, Excel-ready per-**Einsatz** revenue forecast
when the in-conversation Forecast above isn't enough (e.g. they want to model in a
spreadsheet). Triggered by "Forecast-Export", "Einsätze exportieren", "CSV-Export der
Einsätze", "Umsatzprognose als Excel".

This is an **async action**, not a report you build here:

```
manage-record-action operation:"execute_index" model_type:"0-401"
  action:"export-forecast" confirmed:true
  data:{ year: <optional int>, status: <optional: draft|scheduled|active|completed|terminated> }
```

- `model_type:"0-401"` = Assignment (Einsatz). Omit `data` for the current calendar year and
  all non-cancelled Einsätze.
- The backend queues the export and, when ready, **emails the requester** (and posts an
  in-app notification) a **download link**; the file also appears under
  **Einstellungen → Datenverwaltung → Import/Export**. You do **not** receive or build the file.
- One row per Einsatz: Mitarbeiter-/Personalnummer, Kundennummer, Zeitraum, Ø Monatsstunden,
  **Stundenverrechnungssatz** (Kunden-Sicht), Zuschläge je Art, and the estimated **per-month
  revenue** for the year (Jan–Dez, only active months, prorated).
- Confirm to the operator that it's been started and that the download will arrive by email —
  don't wait on it in the conversation.

---

## Pipeline-Review capability

**Goal:** identify at-risk deals early and escalate.

Read all open AssignmentContracts (`stage` not `won` / `lost`) and check each contract:

| Flag | Criterion | Check method |
|---|---|---|
| **Stale** | No activity for > N days (default: 14) | `get-timeline` on the contract (`subject_type: "0-31"`, `subject_id` = contract ID; `"0-30"` for a Rahmenvertrag); check most recent entry. Contract timelines are object-level — activities logged on the client Company or a Contact do **not** appear here, so check those too before calling a deal stale |
| **Stuck** | In the same stage for > N days without progress (default: 21) | per-stage timestamps `marked_as_<stage>_at` (e.g. `marked_as_sent_at`) or Timeline — there is no generic `stage_changed_at` field |
| **Overdue** | `valid_until` has passed, stage not yet `won`/`lost` | `valid_until` < today |
| **Single-Threaded** | Only one linked contact person at the company | `count-model model_type:"0-430"` (PortalMembership — one row per linked contact) with filter on `company_id` — Contacts (`0-105`) themselves have no `company_id` filter. Add `archived_at` `is_null`: a customer can archive a contact off their Kontakte list, and your count still includes those rows while the client's own screen does not — an archived-only second contact is a single-threaded account, not a covered one |

Output grouped by `owner_id` (per BDR) so sales leadership can see where each BDR has
fires burning. Remediation recommendation per flag:
- Stale / Stuck → reach out to BDR, schedule an activity
- Overdue → call `manage-contract-lifecycle` (update stage or close)
- Single-Threaded → identify another contact at the client (`search-model 0-105`, or
  `query-model 0-430` by `company_id`)

---

## Coordination (write, preview first)

1. **Select BDR:** `search-model model_type:"0-1"` with filter `is_active: true`.
   Display the list of active users; operator selects the target BDR or confirms
   "for myself" (default: logged-in user).

2. **Trigger job** — as needed:
   - **Prospecting** → `→ prospect-companies` with `owner_id: <bdr>`
   - **Outreach sequence** → `→ enroll-outreach` with `owner_id: <bdr>` and
     `sender_user_id: <bdr>` (so emails go out in the BDR's name). `sender_user_id` moves
     the mailbox precondition onto the BDR: **that** user needs an active connected mailbox
     — Gmail or Outlook / Microsoft 365, either one — or the enrollment is refused with
     `Sender "<name>" (#<id>) must connect a mailbox before enrolling.` before any write.
     Your own mailbox does not cover for theirs.
   - **Profilvertrieb** → `→ profilvertrieb` with employee + BDR's target clients

3. **Persist results:** tasks and enrollments are created with `owner_id: <bdr>`,
   so they appear in the BDR's personal view.

4. **Default scope:** without an explicit instruction, the skill acts for the logged-in user.
   Acting for another BDR requires **explicit confirmation** from the operator.

5. **No impersonation:** the MCP has no true impersonation — writes are *attributed*
   to the BDR via `owner_id` / `sender_user_id`, but **permissions remain the
   authenticated operator's own**. Show the planned attribution clearly in every
   preview before writing.

---

## AÜG / Equal Pay

Reporting and Forecast display only **hourly billing rates** (what the client pays)
and probabilities. Equal Pay (AÜG § 8) and the Überlassungshöchstdauer (§ 1 Abs. 1b)
only arise at the level of the concrete Einsatzvertrag — never communicate deployment
duration or employee pay during reporting.
For contract questions → `→ manage-contract-lifecycle`.

---

## Related skills

- `→ profilvertrieb` — actively market Bench employees to matching clients
- `→ prospect-companies` — geo-prospecting for new target clients
- `→ enroll-outreach` — start or manage an Outreach sequence
- `→ manage-contract-lifecycle` — create a Rahmenvertrag/Einsatzvertrag or update stage
- `→ account-research` — deep-dive a single client before a first conversation
