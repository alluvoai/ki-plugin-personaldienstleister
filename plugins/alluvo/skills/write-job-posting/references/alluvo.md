# alluvo connection (optional)

Applies only when the alluvo assistant (MCP server) is connected. Detect this when a tool
`manage-settings` or `get-workflow-guidance` exists. In Claude Code, MCP tools often appear
only after a tool search; search for `manage-settings` before assuming that no connection
exists. All calls in Phase 0 are read-only.

## Read context (Phase 0)

| What | Call | Use |
|---|---|---|
| Form of address, tone, bio, taboo words, inclusivity | `manage-settings` with `action: "get"`, `group: "brand_identity"` | `default_formality` (formal = Sie, informal = du), `default_tone`, `brand_bio` (opening and „Über uns"), `terms_to_avoid`, `inclusivity_gender_neutral`, the other inclusivity flags, and `personality` |
| Company name and contact | `manage-settings` with `action: "get"`, `group: "general"` | Sender, contact person, standard application route |
| Role catalogue | `search-model` with `model_type: "0-100"` (StaffingRole), `q: "<Position>"` | Roles as options for question 1; `role_id` for creation |
| Branches | `search-model` with `model_type: "0-73"` (Branch) | Location options for question 2 |
| Client staffing requirement | `search-model` with `model_type: "0-102"` (StaffingRequirement), `q: "<Kunde oder Rolle>"`, then `get-model` | Pre-fill position, location, period, and requirements; name the client in the posting only with permission |
| Benefits catalogue | `list-model-types` (no parameters), find the type with „Benefit" in its name, then `search-model` with that `model_type` | Benefits as options for question 6, grouped by security, money, health, and leisure; ask question 6 normally if no such type exists |
| Style reference | `search-model` with `model_type: "0-80"` (Job), filter `is_active: true`, `per_page: 3`, then `get-model` on a job | Match the tone and structure of existing postings; do not copy them |

If a call returns `MODULE_LOCKED`, tell the user in one sentence and continue without that
source.

## Create the job (Phase 4, option 2)

Always use two stages: preview first, then user confirmation, then execution.

```
Tool: manage-model
action: "create"
model_type: "0-80"
data:
  title: "<Titel mit (m/w/d)>"
  description: "<Volltext als Markdown oder Absätze>"
  location: "<Stadt>"
  postal_code: "<PLZ>"
  employment_type: "<full_time | part_time | temporary | contractor | intern | other>"
  work_hours: "<z. B. 'Vollzeit 39 h, Schichtdienst'>"
  responsibilities: "<Aufgaben>"
  qualifications: "<Profil>"
  job_benefits: "<Wir bieten>"
  salary_min: <Zahl in EUR, z. B. 3400>
  salary_max: <Zahl in EUR>
  salary_currency: "EUR"
  salary_unit: "MONTH"
  role_id: <ID aus dem Rollenkatalog, optional>
  published_at: "<ISO 8601 mit Offset, z. B. 2026-10-01T09:00:00+02:00>"
  immediate_start: <true|false>
confirmed: false
```

Show the preview, obtain confirmation, and repeat with `confirmed: true`. The result contains
`talent_hub_url`; show it and offer to add a hero photo (recipe via `get-tool-guidance` with
`tool_names: ["manage-media"]`).

Always express salaries in euros, never cents. `salary_unit` is free text: `MONTH` for
monthly pay, `HOUR` for hourly pay, and `YEAR` for annual pay. `employment_type` is a closed
value; when unsure, call `get-model-schema` with `model_type: "0-80"` and `context: "form"`.

If the user wants to assign the job to a campaign, call `search-model` with `model_type:
"0-191"` (JobPostingCampaign) und die ID als `job_posting_campaign_id` mitgeben.

## Publish to the Bundesagentur (Phase 4, option 3, only with alluvo)

Offer this only when the job exists in alluvo (option 2) and the Bundesagentur integration is
connected. Check with `manage-record-action` (`action: "list"`, `model_type: "0-80"`, the job id):
if `publish-job-to-channel` is not listed, the integration is not connected or the user lacks
`jobs.edit` — say so in one sentence and fall back to the channel copy from structure.md.

Readiness checklist, tell the user before calling the action:

- **Postal code** on the job (`postal_code`, five digits) and a location in Germany.
- **BA occupation** (`ba_title_code`): on the job, or on its staffing role (`role_id`). The code
  comes from the BA occupation catalogue and must be an active occupation title.
- A description of at least 30 characters and a Talent Hub address (the job needs a slug).

Then run the action with the usual two stages:

```
Tool: manage-record-action
action: "run"
model_type: "0-80"
model_id: <Job-ID>
action_name: "publish-job-to-channel"
data: {}
confirmed: false
```

Show the preview, obtain confirmation, repeat with `confirmed: true`. When the readiness checklist
is not met, the action answers with the missing details in plain language: relay them and fix the
job (`manage-model` update) rather than retrying. The job goes to the Bundesagentur with the next
automatic submission (about every ten minutes); applications still arrive through the Talent Hub.
`data: {"not_published": true}` is a test mode that is not published at the BA — use it only if the
user explicitly wants to test. Later: `update-job-on-channel`, `withdraw-job-from-channel`,
`preview-job-at-ba` (PDF preview, nothing published). After 21 days without a change the owner
gets the task „Ist die Stelle noch offen?“; after 30 days without confirmation the job is
withdrawn from the BA (it stays on the Talent Hub). Confirm with `confirm-job-still-open`.

## Meta campaign (Phase 4, option 4, only with alluvo)

For a real campaign rather than short copy, call `get-workflow-guidance` with
`workflow: "manage-meta-ads"` and follow its guidance. The Talent Hub URL of the created job
is the landing page; the Meta short copy from structure.md is the creative.
