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

## Precheck: is the Talent Hub on?

Before creating a job, read `manage-settings` with `action: "get"`, `group: "talent_hub"`.
`is_enabled` must be `true`; otherwise the job exists but has no public page. Tell the user in
one sentence and offer to switch it on (`manage-settings` `action: "update"`, preview first).
Also note `default_placement_type` and `default_valid_through_days` (new jobs inherit them) and
`show_contact_phone` (off by default).

## Create the job (Phase 4, option 2)

Always use two stages: preview first, then user confirmation, then execution.

```
Tool: manage-model
action: "create"
model_type: "0-80"
data:
  title: "<Titel mit (m/w/d)>"
  description: "<kurzes Intro, Markdown, 2-4 Sätze>"
  status: "published"            # required: draft | preparing | review | published | completed
  location: "<Stadt>"
  postal_code: "<PLZ, 5 Ziffern>"
  placement_type: "<temporary_agency | direct_placement | own_position | freelance>"
  contract_type: "<permanent | fixed_term | minijob | midijob | working_student | internship | apprenticeship | freelance>"
  working_time: "<full_time | part_time | flexible>"
  weekly_hours: <Zahl 0-80, optional>
  work_hours: "<Freitext, z. B. 'Schichtdienst Früh/Spät', optional>"
  responsibilities: ["<Aufgabe>", "..."]
  qualifications: ["<Anforderung>", "..."]
  job_benefits: ["<Benefit>", "..."]
  salary_min: <Zahl in EUR, z. B. 3400>
  salary_max: <Zahl in EUR>
  salary_currency: "EUR"
  salary_unit: "MONTH"
  is_remote: <true|false>
  role_id: <ID aus dem Rollenkatalog, optional>
  published_at: "<ISO 8601 mit Offset, z. B. 2026-10-01T09:00:00+02:00>"
confirmed: false
```

Field rules (checked against the real schema; `get-model-schema` with `model_type: "0-80"` is the
authority when in doubt):

- `status` is **required** on create. `slug` is generated from the title; do not send it.
- `description` is only the short **Markdown intro**. Aufgaben, Profil and Benefits go into the
  three **string lists** (`responsibilities`, `qualifications`, `job_benefits`), one item per
  bullet, never as one text block. The page renders them as their own sections.
- `placement_type` defaults to the hub's `default_placement_type`; send it when it differs.
  `employment_type` (employee enum) is not the job's contract field — use `contract_type`,
  `working_time` and `weekly_hours`. Interview mapping: unbefristet -> `permanent`; befristet ->
  `fixed_term`; Minijob/Midijob -> `minijob`/`midijob`; Werkstudent -> `working_student`;
  Praktikum -> `internship`; Ausbildung -> `apprenticeship`; Freelance -> `freelance`;
  Vollzeit/Teilzeit/flexibel -> `working_time`; stated hours per week -> `weekly_hours`.
- `valid_through` (date `Y-m-d`, end of the advertising period): **send it only if the user names a
  date.** Otherwise the default `today + default_valid_through_days` applies on create. After
  expiry the job moves to `completed`; the owner gets a reminder 7 days before.
- `meta_title` is an optional SEO title; leave it out unless the user wants one.
- Salary is in euros, never cents. `salary_unit` is free text: `MONTH`, `HOUR` or `YEAR`.
  The page and Google only show salary when the hub's "show salary" setting is on.
- Read-only, never send: `talent_hub_url`, `creator_id`, `date_posted`, `meta_description`,
  `hiring_organization_*`, `identifier`. `is_remote` true adds a chip and, with
  `applicant_location_requirements` (list of country/region strings), the remote data for Google.

Show the preview, obtain confirmation, and repeat with `confirmed: true`. The result carries
`talent_hub_url`.

## Verify after publishing

Run the read-only Google-for-Jobs check; it needs no confirmation:

```
Tool: manage-record-action
action: "run"
model_type: "0-80"
model_id: <Job-ID>
action_name: "check-public-page"
```

It returns `talent_hub_url`, whether the hub is enabled, whether the job is published, active and
not expired, and `findings` (`error` or `warning` with field and message). `live: true` means no
errors. Report every finding in plain language, fix what the job data can fix (`manage-model`
update, preview first), and re-run. Only then show `talent_hub_url` as the final link and offer a
hero photo (recipe via `get-tool-guidance` with `tool_names: ["manage-media"]`).

If the user wants to assign the job to a campaign, call `search-model` with `model_type:
"0-191"` (JobPostingCampaign) and pass the ID as `job_posting_campaign_id`.

## Translations (after publishing)

The Talent Hub serves a job in every enabled language; the job's own text is the default
language, other languages need a translation record. The `check-public-page` findings with code
`missing_translation` name each enabled language that has none. For each, offer to write the
translation (nothing is translated automatically): `manage-model` with `model_type: "0-459"`,
`action: "create"`, `confirmed: false` first, then `true` after confirmation:

```
data: {job_opening_id: <Job-ID>, locale: "en", title: "...", description: "...",
       meta_title: "...", meta_description: "...", is_ai_translated: true,
       editorial_data: {tasks_bullets: ["..."], requirements_bullets: ["..."]}}
```

`locale` must be an enabled Talent Hub language other than the default one, once per job.
`description` is the Markdown intro; keep tone, structure and facts of the original and translate
every language-bound text (`editorial_data` accepts subtitle, honest_intro, tasks_intro,
tasks_bullets, requirements_bullets, cta_label, apply_heading, apply_intro, work_hours). Change
later with `action: "update"`; list a job's translations with `get-model` on the job (0-80) or
`query-model` on 0-459 filtered by `job_opening_id`.

**Always send `is_ai_translated: true` when you wrote the translation.** The public job page then
shows a small notice in the page language ("translated with AI", with the original language) and a
"View original" link to the job in the default language; the PDF carries the same line, and
`check-public-page` reports the language as an `ai_translated` warning so the team can review it.
A person who has reviewed or written a translation themselves sets `is_ai_translated: false`
(`action: "update"`); an update without the field keeps the stored value.

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
