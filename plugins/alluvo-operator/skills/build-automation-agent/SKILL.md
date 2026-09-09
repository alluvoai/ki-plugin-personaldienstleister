---
name: build-automation-agent
description: Build or adjust an AI automation agent — either scheduled (a periodic report delivered by email or task) or deployed on an Inbox so it reacts to inbound tickets — no operator login needed once it's set up. Use when the operator says "Automatisierungs-Agent bauen", "geplanten KI-Bericht einrichten", "monatlichen Report automatisieren", "automatisiere einen wiederkehrenden Bericht", "build an automation agent", "schedule an AI report", "automate a monthly report", "set up a scheduled agent", "Erinnerung vor Vertragsende einrichten", "automatische Aufgabe pro Vertrag", "Meldung wenn ein Mitarbeiter den Tag abschließt", "Benachrichtigung bei Pausenverstoß", "Meldung wenn ein Mitarbeiter den Dienstplan ändert", "Benachrichtigung bei Dienstplanänderung nach Freigabe", "Agent auf einen Posteingang setzen", "Posteingang-Agent einrichten", "Agent auf die Inbox deployen", "deploy an agent to an inbox", "inbox agent", "welche Agenten laufen auf welchem Posteingang", "mehrstufigen Workflow mit Wartezeit bauen", "Erinnerungsstrecke einrichten", "Workflow soll stoppen sobald unterschrieben ist", "warum hängt der Datensatz im Workflow", "Datensatz aus dem Workflow nehmen", "build a multi-step workflow", "add a delay to a workflow", "Baustein anlegen", "Baustein an den Agenten hängen", "Bausteine des Agenten ändern", "Reihenfolge der Bausteine ändern", "Markenstimme / Anrede-Form / ICP in den Agenten aufnehmen", "attach an instruction block to the agent", "welche Bausteine gibt es", "was der Bewerber-Agent auf WhatsApp sagt", "Bewerber-Flow-Texte anpassen", "Anforderungen an Bewerber im WhatsApp-Agenten ändern", "Standort der Agentur für die Agenten hinterlegen", "Agent taggen", "Tag an den Agenten hängen", "Tag anlegen oder umbenennen", "welche Tags gibt es", "tag an agent", "rename a tag", "welche Agenten gibt es", "zeig mir den Prompt des Agenten", "was sagt der Talent-Hub-Assistent", "Anweisungen des Bewerber-Assistenten ändern", "Agent aktivieren / deaktivieren", "Prompt-Abschnitt zurücksetzen", "show an agent's prompt", "change what the chat assistant says", "reset a flow section to the default", "meine persönliche Anweisung für die KI", "persönliche Anweisungen der Nutzer", "firmenweite Anweisung für die KI-Nachbearbeitung", "set my personal AI instruction", or wants a recurring AI-generated report, a recurring per-record reminder/task, a multi-step sequence with waits and branches, or an agent that processes inbound tickets automatically, or wants to change what any AI agent is told (system blocks, tenant Bausteine, personal per-operator instructions, the candidate-facing WhatsApp flow sections, or the prompt layers of a conversational or task agent).
---

# Build-Automation-Agent (Automatisierungs-Agent & geplanter Workflow)

## Purpose

Set up a self-running **automation agent** (a scoped AI agent that calls a fixed set of read
tools and returns a structured output) and give it a trigger. Two trigger shapes:

- **Scheduled** — a **workflow** runs the agent on a cron/preset schedule and delivers the
  result (email, or a follow-up task). Typical job: "every 1st of the month, check which
  employees qualify for X, and email me the list." Steps 1–7 below.
- **Deployed on an Inbox** — the agent reacts to *inbound tickets* in an inbox instead of a
  clock, proposing and executing a whitelisted set of actions per mail. See
  *Inbox deployments* below.

Both shapes use the same Agent record; a single agent can be scheduled, deployed, or both.

This skill is also where **what any agent is told** lives — not just automation agents. The
tenant's conversational assistants (Bewerber-WhatsApp, Talent Hub, Mitarbeiter-Support) and
its task agents are reached through `manage-agent-prompt`; see *Conversational and task
agents* below. Nothing there creates or deletes an agent — those layers are configuration
only.

> **MUTATING.** Creates an Agent record (`type=automation`) and a Workflow record; both are
> two-stage — preview (`confirmed`-style review shown to the operator) → operator approval
> → the actual `create` call. `test` always runs the agent with zero side effects regardless
> of its capabilities. Most agents are read-only (see `describe-tools` — read capabilities
> carry no marker), but an agent **can** be granted a write capability in `execute` mode
> (`manage_model`, labeled **`(WRITE)`** in `describe-tools` output). A write-bridged agent
> can still only create **draft**-status records on models
> that lock their lifecycle field to `draft` for MCP writes (e.g. `CompensationComponent`) —
> it can never fully-effect anything; a human approves separately. The **workflow** is what
> causes an unconditional effect (sending an email, creating a task) once it goes live on its
> schedule.

## Prerequisites

- Exclusively via `mcp__alluvo__*` — no shell, no file I/O.
- A clear goal for the report: what to check, at what cadence, and who should receive it.
- Know (or ask) the delivery target: an email address, or a task assignee.
- `manage-automation-agent`, `manage-agent-prompt`, `manage-ai-preferences` and
  `manage-workflow` belong to the **KI & Automatisierung** module. Without it those
  tools are absent and calling one answers `MODULE_LOCKED` — relay that German message
  verbatim (required Tarif + Testphase link) rather than rebuilding the automation by
  hand. `manage-apps` `action: "modules"` shows the tenant's Tarif and any Testphase.

## Terms

| Term | Meaning |
|---|---|
| **Automation agent** | An `Agent` record (`type=automation`) with `instructions` (German, natural language), a `capabilities` map (`{key: "execute"\|"propose"}` — what it may do, and whether unsupervised or approval-gated), and an `output_schema` describing the structured result it must return. Runs "to completion" once, then stops — no chat, no follow-ups. |
| **Capability** | One entry of the unified catalogue `describe-tools` lists (~35 keys, snake_case: `query_employee_sick_days`, `query_model`, `manage_model`, `create_task`, `send_ticket_reply`, …). Each supports one or both **modes**: **`execute`** — runs as a tool during the agent's own run, no approval gate; **`propose`** — may appear as a step on an *inbox deployment*'s run card (whether that step then pauses for approval or runs on its own is a property of the step, see *Inbox deployments*). A key you omit is **off**. `enabled_tools` is the deprecated predecessor (see *Capabilities* below). |
| **System block (`blocks`)** | One of eight code-shipped prompt sections keyed `current-date`, `precedence`, `brand-voice`, `agency-location`, `formality`, `ai-disclosure`, `icp`, `selling-profile` (labels: Aktuelles Datum, Rangfolge-Erklärung, Markenstimme, Standort der Agentur, Anrede-Form (Du/Sie), KI-Offenlegung, Zielkundenprofil (ICP), Verkaufsprofil). Their *content* comes from tenant data (brand identity, ICP, selling profile, `company_city`/`company_state`, formality settings) — the agent only chooses *which* of them render, via the `blocks` array. `describe-tools` lists them. See *Prompt building blocks* below. |
| **Baustein (`InstructionBlock`, `0-442`)** | A tenant-authored, reusable prompt snippet — `name`, `content`, `is_active` — kept as its own record and attached to one or more agents. Rendered as `### Baustein: <name>` *after* the agent's own `instructions`, in the operator-chosen order. Read/write over the generic model tools with `model_type: "0-442"`. Attached to an **automation** agent via `manage-automation-agent`'s `instruction_block_ids` (full replacement), to a **conversational or task** agent via `manage-agent-prompt`'s `attach-baustein` / `detach-baustein` / `reorder-bausteine` (incremental). Both tools see **tenant-owned** blocks only. |
| **Personal instruction (user-owned `InstructionBlock`)** | The same record type with a `user_id` set: **one operator's own** additive text on **one agent**, affecting only that operator's runs of it. It hangs on the same agent↔block pivot as a Baustein but is deliberately invisible to `manage-automation-agent` and `manage-agent-prompt` — read and written only via `manage-ai-preferences` (see *Personal instructions* below). Not the same thing as a Baustein: a Baustein is tenant-wide and shared, a personal instruction is private to its owner. |
| **Agent (`0-400`) / AgentRun (`0-441`)** | `query-model` / `search-model` / `get-model` read both. `AgentRun` is read-only. On `Agent`, `manage-model` `update` writes a deliberately tiny allowlist — `name`, `display_name`, `tags` — and `create` is refused outright ("can be updated but not created via the generic model tools"); anything about behaviour, structure or lifecycle is refused there with a pointer to the owning tool. See *Renaming and tagging an agent* below. Use these tools to *find* an agent (any type) or review its run history; use `manage-automation-agent` or `manage-agent-prompt` to change what it says or does. |
| **Tag (`0-443`)** | One entry of the **tenant-wide** tag vocabulary — `name` plus a `color` (`gray`, `blue`, `indigo`, `purple`, `success`, `warning`, `danger`). Full read+write over the generic model tools with `model_type: "0-443"`; `slug` is derived from `name` on save and is not writable. Attaching tags *to* a record is a different write — it rides that record's own write path as a `tags` field. Twelve record types are taggable (`Agent` among them); the cross-cutting rules live in `using-alluvo-operator` → *Tagging a record*. See *Tags* below for the agent-specific write paths. |
| **Scheduled workflow** | A `Workflow` with `trigger_event=scheduled` that runs on a cron/preset schedule and executes one or more actions in order. Two modes: **record-less** (no `trigger_model_type`) — one run per tick, typically `run_agent` then `transactional_mail`; and **record enrollment** (`trigger_model_type` set) — each tick sweeps that model's records, evaluates `conditions` per record and fires the actions once per match. |
| **Enrollment** | What one firing of a workflow *is*, for one record (or record-less, for a plain scheduled run). It is durable: a workflow whose steps contain a `delay` or `wait_until` node **sleeps** and resumes later, so an enrollment can live for days or months. Statuses: `active`, `waiting` (parked on a delay/wait node), `completed`, `goal_reached`, `unenrolled`, `failed`. Inspect with `list-enrollments`, end one by hand with `unenroll`. A workflow with no waits still completes instantly — the enrollment is then just the audit record. |
| **Output bag / placeholders** | The `run_agent` action's structured output is stored under `output_key` (default `agent`) and available to every later action as `{{agent.<key>}}`. Built-in schedule tokens `{{run.date}}`, `{{run.month_name}}`, `{{run.year}}`, `{{run.previous_month_name}}`, `{{run.period_start}}`, `{{run.period_end}}` are always available on a scheduled run. A **record-triggered** run instead carries the record's own fields (incl. nested dot-paths) plus a `{{trigger.*}}` family describing who triggered it and where the record came from — see *Slack delivery* below. |
| **Deployment** | An `AgentDeployment` record (model type `0-306`, slug `agent-deployments`) binding one automation agent to one Inbox (optionally one channel of it). Instead of a schedule, *inbound tickets* trigger it. Created/removed via `deploy` / `undeploy`, listed via `list-deployments`. |
| **AI takeover run** | What a deployment produces per inbound message: a run card rendered inside the ticket conversation, holding the agent's summary and its ordered steps. Most steps execute automatically; a few pause for operator approval. Each executed step can be undone individually from the card. |

## Steps

### 1. Clarify the job-to-be-done

Before calling any tool, pin down with the operator:
- **What** should the agent check/report on (the qualifying condition, the data source)?
- **One output per run, or one per record?** A periodic report ("email me the list") is a
  record-less scheduled workflow with an agent; "do X for every record that matches" is a
  scheduled **enrollment** workflow with a `trigger_model_type` and conditions, and often
  needs no agent at all.
- **How often** — monthly (start/end of month), weekly, daily, or a specific date needing a
  raw cron (`schedule_cron`)?
- **Who receives it** — an email address (recipient/cc/bcc), or should it land as a task for
  someone?
- **Sensitivity** — does the report touch personal/health data (see "Data protection" below)?

### 2. See what the agent is allowed to do

Call `manage-automation-agent` with `action: "describe-tools"` to see the exact catalogue of
assignable **capabilities** — one line per key, `` `key` [modes] (WRITE)? — label ``, e.g.
`` `query_model` [execute] — … `` or `` `manage_model` [execute/propose] **(WRITE)** — … ``.
It lists **everything** `capabilities` accepts: the run-time tools (`query_employee_sick_days`,
`query_employee_hours`, `create_task`, the bridged read family `query_model`/`get_model`/
`search_model`/`count_model`/`get_notification_preferences`/`get_booking_availability` — all
filtered to the agent's owner — and the write-gated `manage_model`), **plus** every
classifier step an inbox deployment can propose (`create_note`, `send_email`,
`send_ticket_reply`, `close_ticket`, …). Read the `[modes]` column: pure read tools are
`[execute]` only, most classifier steps are `[propose]` only, `create_task` and `manage_model`
support both. Pick only the capabilities the job actually needs — never grant more than it
requires, and only grant a **`(WRITE)`** key in `execute` mode when the job is genuinely
"write a draft record for a human to approve," not a report. For a **scheduled** agent, only
`execute` entries matter; `propose` entries only come into play once the agent is deployed on
an inbox (see *Capabilities* below).

### 3. Design the output schema and instructions

- **`output_schema`** — an array of `{key, type, required?, description?, of?}` (types:
  string/integer/number/boolean/array). `of` belongs on a `type: "array"` field only: it is
  itself an `output_schema` array describing one item's shape, e.g.
  `{key: "employees", type: "array", of: [{key: "name", type: "string", required: true}, …]}`.
  Keep it minimal: usually a `body` (the ready-to-send German report text) plus one or two
  numeric/boolean fields the workflow or the operator may want to inspect (e.g.
  `qualifying_count`).
- **`instructions`** — German, natural language: what the agent checks, which tool(s) to
  call, how to build the `body` text, and an explicit **data-minimization instruction** (see
  below) so the agent only names the fields the report actually needs.

Prefer a structured **`array`** output field (e.g. `employees` with an item shape like
name/personnel_number/…) over a single pre-formatted text `body` when the result is a list —
a downstream `transactional_mail` action can render an array field as a real HTML table or
list via `{{<output_key>.<field> | table}}` / `| list` / `| sorted_list` (optionally
`table:H1,H2,…` for explicit headers), whereas a hand-formatted list inside a `body` string
loses its line breaks in HTML email. A short `body` string is still fine for prose-only
reports.

**When you use an `array` field, also name its item fields in `instructions`.** Today `of` is
validated and stored, but the item shape is not currently handed to the model at run time — the
agent is asked for "an array" and infers the per-item keys from your prose. So write them out
(«jeder Eintrag hat `name`, `personalnummer`, `tage`») in addition to setting `of`; otherwise the
keys drift between runs and a `{{employees.name | table}}` placeholder renders empty. Confirm the
actual keys in the `test` output (step 5) before wiring the field into a mail template. Set `of`
regardless — it documents the intent and the run-time gap is being fixed api-side.

Optionally set **`pseudonymize_pii: true`** when the agent doesn't need to reason over real
identities (e.g. a pure counting/aggregate report) — identity fields (names, personnel
numbers, emails, …) are tokenized before reaching the LLM and restored in the final output.
Tokens are not stable across runs. Combine with the data-minimization instructions below for
anything touching health/absence data.

Show the operator the planned `name`, `display_name`, `instructions`, `capabilities`
(key → mode), `output_schema`, `pseudonymize_pii`, any `tags`, and — when the agent writes prose a human will read —
its `blocks` selection and any Bausteine (`instruction_block_ids`, in order; see *Prompt
building blocks* below) as a **preview** before creating anything.

### 4. Create the agent

On operator approval, call `manage-automation-agent` `action: "create"` with `name`,
`display_name`, `instructions`, `capabilities` (e.g.
`{"query_employee_sick_days": "execute"}`), `output_schema`, and optional
`pseudonymize_pii`, `blocks`, `instruction_block_ids`, `tags`. Do **not** send `enabled_tools` — it is
a deprecated alias (see *Capabilities* below). There is no `model_provider`/`model_name` param — automation agents are
pinned to Anthropic Sonnet and the model is not operator-selectable. `owner_id` defaults to
the calling operator — the agent runs with that user's permissions; only set it explicitly if
the operator wants the agent to run as someone else, and confirm that choice first (see the
on-behalf-of caveat in `.claude/rules` — permissions always remain the authenticated
operator's own even when `owner_id` differs).

### 5. Test it — no side effects

Call `manage-automation-agent` `action: "test"` with the new `agent_id` (optionally an
`input` override). This runs the agent NOW and returns its structured output **without any
follow-up workflow actions or side effects**. Show the operator the actual `body` (and any
other output fields) so they can sanity-check the report before it's wired to auto-send.
Iterate on `instructions`/`capabilities`/`output_schema` via `action: "update"` and re-`test`
until the operator is happy. `capabilities` is a **full replacement** on `update` (like
`blocks`/`instruction_block_ids`/`tags`) — read the current map from `get` and send the whole map
back, not just the changed key.

`test` covers the **scheduled** path only. It does not simulate an inbox deployment (different
prompt, different schema, different actions) — see *Inbox deployments* below.

### 6. Build the scheduled workflow

Design the workflow as a preview:
- `trigger_event: "scheduled"` — for a plain periodic report leave `trigger_model_type`
  unset (record-less: one run per tick, `conditions` don't apply). Set
  `trigger_model_type` when the job is "do this once per matching record" — see
  *Scheduled record enrollment* below.
- Exactly one schedule source: `schedule_preset` (`monthly_start` / `monthly_end` / `weekly`
  / `daily` / `yearly` — Jan 1, 06:00) — prefer this whenever it fits — or `schedule_cron` for
  a shape a preset can't express. Optional `timezone` (IANA, e.g. `Europe/Berlin`); defaults
  to the tenant timezone.
- **Action 1 — `run_agent`**: `config: { agent_id, output_key: "agent" (default) }`.
- **Action 2 — `transactional_mail`**: `config: { recipient, cc?, bcc?, subject, body }`,
  referencing `{{agent.body}}` and `{{run.*}}` tokens in `subject`/`body` (e.g. subject
  `"Report {{run.previous_month_name}} {{run.year}}"`, body `{{agent.body}}`). If the
  delivery target is an internal owner/task instead of an inbox, use `create_task` as the
  second action instead — call `manage-workflow` `action: "describe-action"` with
  `action_type: "create_task"` for its exact config shape before building it. A third delivery
  target is Slack — see *Slack delivery* below.

Show the full action list (with the resolved recipient and rendered-looking placeholders) to
the operator before creating.

#### Slack delivery, and approve/reject buttons (`send_slack_message`)

Posts into a Slack channel and/or DMs an alluvo user. Requires a **connected Slack workspace**
on the tenant — that is a setup step outside MCP, so confirm the connection exists before
promising Slack delivery; without it the action fails at run time. Config: `channel_name`
and/or `channel_id` and/or `user_id` (at least one channel or user required), `message` (also
the fallback text when `blocks` are used), optional `blocks` (Block Kit layout), and optional
`record_actions`. Call `manage-workflow` `action: "describe-action"` with
`action_type: "send_slack_message"` before building one — for the full block-type table **and**
for the channel list described next.

**This is not the `@alluvo` Slack bot.** `send_slack_message` is a workflow *pushing* a message
out; the companion is the bot an operator *mentions* in a thread. They share nothing but the
workspace connection — a companion complaint ("der Bot antwortet nicht", "gib dem Channel feste
Anweisungen") is `manage-settings`, group `slack`, not a workflow (`→ using-alluvo-operator`).

**Name the channel, don't hunt for its id.** `channel_name` takes what the operator actually
says — `"alluvo-stundenfreigabe"`, with or without the leading `#`, any case. It is resolved
once when the workflow is saved and the **id** is what gets stored, so a later rename in Slack
cannot break the workflow. Never copy a raw id out of an existing workflow to reuse it; pass
`channel_id` only when the operator hands you a real id (`C0BM31LH3UM`), and note that it wins
if both are given. `describe-action` for this action type appends **the tenant's actual
channels** (name + id, each flagged `private` and/or `bot not a member` where it applies) — so
offer the operator that list by name instead of asking them for an id. An unknown name is
rejected at save time with the list of channels that do exist; a private channel the bot has
not been invited to simply does not appear, and the invite is a step in Slack, outside MCP.

**Every message is block-rendered and carries an automatic provenance footer.** Even a config
with only `message` and no `blocks` is delivered as blocks — the text is moved into a `section`
block so the footer can be appended after it. Never author your own "triggered by / source"
block: alluvo appends a muted `context` line as the **last** block of every workflow Slack
message, reading `Ausgelöst von <Name> · Quelle: <Quelle> · Automatisierung: „<Workflow>"`.
On an `action_performed` run it names the action too — `Aktion „Genehmigen" ausgeführt von
<Name>`, or `Aktion „Genehmigen" automatisch ausgeführt` when nobody was behind it. That is the
only thing in the post that tells an approval from a rejection, since both reach the workflow as
the same status change. With neither a human nor an action it reads `Automatisch ausgelöst`, and
the `Quelle:` part is dropped when the record carries no `record_source`.

**Word the message for the state, not for one origin path.** Conditions match a record's
*state*, never the path that produced it: a `stage equals won` contract workflow fires for a
customer's self-service portal checkout **and** for an operator marking a contract won by hand.
A header like "Neue Portal-Buchung abgeschlossen" therefore mis-describes half its runs — this
really happened, an operator-created AÜV was announced to a channel as a customer booking.
Describe the state change ("Vertrag auf *gewonnen* gesetzt") and let the footer say which path
it came through. When a workflow must genuinely fire **only** for client-portal self-service,
add a condition `record_source equals client_portal` — but confirm the model actually carries
that field first (AssignmentContract `0-31` does; FrameworkContract `0-30` does not, so there
the condition would simply never match).

**`{{trigger.*}}` placeholders** expose the same values to any text field on a
**record-triggered** workflow (`created`/`updated`, and a scheduled *enrollment* sweep):
`{{trigger.actor_name}}`, `{{trigger.actor_email}}`, `{{trigger.actor_id}}`,
`{{trigger.action}}` (the action key on an `action_performed` run, e.g. `approve`; empty on every
other trigger), `{{trigger.source}}` (the raw key, e.g. `client_portal`),
`{{trigger.source_label}}` (translated), `{{trigger.source_detail}}`. They render empty rather
than failing when absent. **`actor_name` is empty only when no human triggered the change at
all** — a scheduled sweep, an import, a cascade from another record. It is *not* empty for a
Slack-button click, a client-portal action, or an employee acting in the Mitarbeiter-App: the
actor is captured when the enrollment is written and travels with it, so a run that sat on a
`delay` for days still names the right person. Never tell an operator that a queued run loses the
actor. A **record-less** scheduled run has no `trigger.*` at all (only `{{run.*}}`); its footer
still posts, as `Automatisch ausgelöst · Automatisierung: „…"`.

**`record_actions` renders buttons that really execute the record's actions.** Set it to `true`
(every Slack-enabled action) or to a list of action names (e.g. `["approve", "reject"]`); omit it
for a plain notification. State these five things to the operator before wiring it up — none of
them are obvious from the config:

- **You cannot author the button set.** It is derived from the action catalog: an action appears
  only when it is marked Slack-enabled **in code** *and* the record's current state permits it
  right now — an already-approved absence renders no Approve button. A `blocks` `actions` entry
  can never produce one; those are link-out buttons only (`url` required, no callbacks). Today
  the only Slack-enabled actions are AbsencePeriod (`0-13`) `approve` and `reject`. Asking for
  `record_actions` on any other model silently renders nothing, and no MCP call lists which
  actions are Slack-enabled — so don't promise buttons for another model without checking.
  Slack-enabled is a **different** flag from workflow-triggerable: AbsencePeriod's four other
  triggerable actions (`submit`, `request-revision`, `cancel`, `reset-to-draft`) can *start* a
  workflow but render no button.
- **It needs a triggering record.** Buttons render on `created`/`updated` runs and on a
  **scheduled enrollment** sweep (`trigger_model_type` set). A record-less scheduled run has no
  record, so `record_actions` is ignored there — the periodic-report shape above gets no buttons.
- **Visibility is not capability — but don't lean on that alone.** A click runs as the *clicking*
  Slack user: they are resolved to their alluvo account, and the action's own permission check and
  state gate then run unchanged. An unmapped clicker (e.g. an external member of a shared /
  Slack Connect channel) or an unauthorized one gets a private refusal and nothing is written.
  Still use `user_id` (DM) when only one approver should even see the request.
- **The first click closes the message.** It resolves the whole button set — the sibling buttons
  stop working and the post is rewritten with who did what. Buttons expire after **7 days**, so a
  stale one in scrollback is refused rather than firing late.
- **A button carries no free text.** An action whose confirmation demands a written reason can
  never be Slack-enabled at all. Where the reason is merely *optional* it is simply absent: a
  Slack `reject` on an absence sets the status but leaves `review_note` empty, so the employee
  sees no explanation. When the reason matters, keep that approval in the app
  (`→ record-absence`) instead of on a button.

#### Scheduled record enrollment (`trigger_event: "scheduled"` + `trigger_model_type`)

When the job is "every N days, look at all records of type X and act once per record that
matches" — e.g. "on the 7th of each month, create a review task for every assignment
contract ending at the end of this month" — set `trigger_model_type` on the scheduled
workflow. Each schedule tick sweeps that model's records, evaluates `conditions` per record,
and fires the actions once per match, with the record's fields available as `{{placeholder}}`
tokens (including nested dot-paths).

- **`allow_reenrollment` applies here too, with different semantics than on `updated`:**
  `false` (default) = each record enrolls **once ever** (right for "remind me once per
  expiring contract"); `true` = the record re-fires on **every** tick it still matches.
  Pick deliberately and say which one you chose in the preview.
- **Always give it conditions.** A scheduled enrollment workflow with no conditions enrolls
  *every* record of the type on every tick; `create`/`update` return a ⚠️ advisory when that
  happens. A sweep is capped at **500 enrollments** — a workflow hitting that cap is a sign
  the conditions are too broad.
- **Condition operators** (ANDed together): `equals`, `not_equals`, `in`, `not_in`,
  `is_null`, `is_not_null`, `contains`, plus date operators evaluated against a
  date/datetime field in the **tenant-local calendar**:
  `date_is_last_day_of_month`, `date_in_current_month`,
  `date_within_next_days` (`value` = N, a number ≥ 0), `date_before_today`,
  `date_after_today`.
- **Record-relative due dates.** On a `create_task` action, `due_relative_to` (dot-path to a
  date field on the enrolled record, e.g. `valid_until`) plus a signed `due_offset_days`
  (e.g. `-7` = one week before) makes the task due relative to the record instead of the run
  date; `due_in_days` is ignored when `due_relative_to` is set. `describe-action` with
  `action_type: "create_task"` has the full config shape.
- A record-less scheduled run may also use `create_task` — it creates an **unlinked** task
  rather than failing.

Example: cron `0 6 7 * *` on model type `0-31` (AssignmentContract), conditions
`valid_until date_is_last_day_of_month` AND `valid_until date_in_current_month`, action
`create_task` with `due_relative_to: "valid_until"`, `due_offset_days: -7` — "on the 7th, one
review task per contract ending at this month's end, due a week before it ends."

Contract-renewal reminders like this are **not** automatic — there is no built-in AÜV renewal
reminder; if an operator wants one, build it as a scheduled enrollment workflow here (or point
them at `→ manage-contract-lifecycle` for the manual path).

#### Event-triggered instead of scheduled (`trigger_event: "updated"`)

If the operator wants the automation to react to a record change rather than a clock ("when a
contract *becomes* won, create a task"), use `trigger_event: "updated"` with a
`trigger_model_type` and `conditions` — but tell the operator the two firing rules up front,
because they are not what "on update" intuitively suggests:

1. **Transition, not state.** An `updated` workflow fires only when the save actually *changed*
   one of the fields its conditions look at. `stage equals won` means "when the record BECOMES
   won" — a record that has been won for weeks does not re-fire because an unrelated field was
   touched. A workflow with **no** conditions fires on every update.
2. **Enroll-once.** After it fires for a record, that record is enrolled and will not fire
   again — unless `allow_reenrollment: true` (boolean, default `false`), which permits firing
   again on each *later* transition. Editing a workflow's conditions does not re-arm records
   that already enrolled. (On a scheduled enrollment workflow the same flag means
   once-ever vs. once-per-tick — see above.)

   One rule sits **above** that flag and applies to every trigger type: a record never gets a
   second enrollment while an earlier one is still `active` or `waiting`. `allow_reenrollment`
   only decides what happens once the first enrollment has *finished*
   (`completed`/`goal_reached`/`unenrolled`/`failed`). This matters as soon as the workflow has
   a `delay` or `wait_until` node (below): the record is parked in `waiting` for the whole
   sleep, so re-triggers during that window are dropped even with the flag on. Never promise
   "it fires again immediately" for a workflow that waits.

So never promise an operator "this fires every time X" without passing
`allow_reenrollment: true` explicitly — and only do that for something genuinely recurring
(e.g. "notify me every time the owner changes"). Leaving it `false` is what prevents duplicate
tasks and mails. `list` marks such workflows `re-enrollment ON`; `get` returns
`allow_reenrollment`; both `create` and `update` accept it.

For an `updated` workflow, `action: "test"` **is** available (dry-run against a `record_id`, or
the latest record of the trigger model type). Its output includes an `Enrollment:` line
(not yet enrolled / already enrolled / re-enrollment allowed) plus a note that live firing also
requires a transition — read both back to the operator; "already enrolled" means a live run
would be suppressed for that record. It also includes the steps dry-run walk described in
step 7 below.

#### The other four trigger events (`trigger_config`)

Beyond `created` / `updated` / `deleted` / `scheduled`, four narrower triggers exist. Each
carries its own `trigger_config` object; picking the right one usually beats writing an
`updated` workflow with clever conditions.

| `trigger_event` | `trigger_config` | Fires when |
|---|---|---|
| `field_changed` | `{"field": "stage", "from"?: <scalar\|array>, "to"?: <scalar\|array>}` | `field` changes on save and (when given) the old/new value matches `from`/`to`. Enum fields compare by backing value. |
| `starts_matching` | none — `conditions` **are** the trigger (required, non-empty) | The instant a record starts matching: on create, or on an update where it did not match before and does now. Never while it was already matching. |
| `date_reached` | `{"date_field": "end_date", "offset_days": <int ≥ 0>, "direction": "before"\|"after"}` | A daily scan finds `date_field` ± `offset_days` landing on today (tenant timezone). |
| `action_performed` | `{"actions": ["<action_key>", …]}` | One of the listed record actions completes successfully on the trigger model. Legal keys are the actions flagged workflow-triggerable in api code — today **AbsencePeriod (`0-13`) only**. **See the note below.** |

- **`field`/`date_field`/`starts_matching` conditions must be OWN columns** — no dot-paths
  through relations. Dirty tracking and the daily scan cannot see relations, and the tool
  rejects a dot-path with an explicit error. (Regular `conditions` on other trigger types are
  not affected by this; only these three trigger inputs are.)
- **`date_reached` re-arms itself.** Moving the date re-arms the trigger, and a yearly
  recurring date (a birthday) fires every year. This is the right trigger for
  "X days before a contract ends" — prefer it over a scheduled sweep with date operators,
  which needs `allow_reenrollment` reasoning to stay correct.
- **`action_performed` works — on AbsencePeriod (`0-13`), and only there (for now).** The legal
  keys are exactly its six actions: `submit`, `approve`, `reject`, `request-revision`, `cancel`,
  `reset-to-draft`. On that model prefer it over `field_changed` on `status`: it fires when the
  action itself completes, and `{{trigger.action}}` plus the Slack provenance footer then tell
  an approval from a rejection — which a status change alone cannot, since both arrive the same
  way. On **every other model** the legal list is empty and any config is rejected with an error
  naming what *is* legal there (`(none — no #[WorkflowTriggerable] actions on this model)` where
  there is nothing) — so a save attempt is the cheapest check. No MCP call enumerates the flag:
  `manage-record-action` `operation: "list"` reports an action's MCP exposure and current
  availability, not whether it can trigger a workflow. Elsewhere keep using `field_changed` on
  the column the action writes, and re-check before promising a second model.

#### Multi-step sequences — the `steps` tree

`steps` is a recursive alternative to the flat `actions` list: a workflow can now branch and
**wait**. Pass either `steps` or `actions` on `create`/`update` — omit `steps` and the legacy
flat `actions` list keeps working exactly as before (nothing needs migrating). On `update`,
`actions: []` is a deliberate **clear** of a stale legacy actions list — accepted only when
the workflow already has a `steps` tree, or is being given one in the same update; otherwise
the tool rejects it (the workflow would be left with nothing to run). Use it when migrating a
workflow to `steps`, so the retired flat list does not linger next to the tree.

Every node has a `"type"` and a server-assigned `"id"`. **Omit `id` on a new node; keep it
unchanged when editing an existing one** — an in-flight enrollment resumes at its node id, so
rewriting ids strands records that are currently `waiting`.

| Node | Shape |
|---|---|
| `action` | `{"type": "action", "action": "<key>", "config": {…}}` — same action keys as a flat `actions` entry, validated the same way. |
| `if` | `{"type": "if", "conditions": [...], "then": [...], "else"?: [...]}` — `conditions` use the usual `{field, operator, value}` shape. `else` may be omitted. |
| `switch` | `{"type": "switch", "field": "company.segment", "cases": [{"match": <scalar\|array>, "steps": [...]}, …], "default"?: [...]}` — first matching case wins (`match` as array = contains). `field` **may** be a dot-path here. |
| `delay` | `{"type": "delay", "config": {"mode": "duration", "minutes"?/"hours"?/"days"?: <int>, "business_hours"?: true}}`, or `{"mode": "relative_to_date", "date_field": "contract.end_date", "offset_days": <int>, "direction": "before"\|"after", "business_hours"?: true}`. |
| `wait_until` | `{"type": "wait_until", "conditions": [...], "timeout_days": <1–365>, "on_timeout"?: [...]}` — sleeps until the conditions pass (woken instantly on a matching record change) or the timeout elapses; on timeout it runs `on_timeout` (if given) and continues either way. |

- **Limits:** max 100 nodes total, max nesting depth 10, and a single `delay` cannot exceed
  365 days (at least one of minutes/hours/days must be > 0).
- **`business_hours: true`** rolls a resume time into the next configured business window
  instead of firing off-hours. Use it for anything that pings a human.
- **`relative_to_date` re-resolves from the live record** when the node runs — so a contract
  whose end date moved while the enrollment slept waits until the *new* date.
- **A record-less scheduled workflow may only use `action` nodes and fixed-`duration`
  `delay` nodes.** `if`, `switch`, `wait_until` and `relative_to_date` all read the triggering
  record, and there is none — the tool rejects them.
- **Tell the operator the sequence is durable.** A `delay` of 30 days means the record sits in
  `waiting` for 30 days and the remaining steps fire then — including a mail that will land in
  someone's inbox long after this conversation. Show the full node tree and the resulting
  timeline in the preview before creating, and say plainly that the record cannot re-enroll
  while it waits.

#### Ending an enrollment early: `goal_conditions` and `unenroll_on_mismatch`

Both are optional and both stop a sequence that has become pointless — the reason a
multi-step chase sequence is safe to build at all.

- **`goal_conditions`** — same shape as `conditions`. When non-empty and they pass at any point
  during the enrollment (checked on every resume, and instantly on a matching record change),
  the enrollment ends as `goal_reached` and every remaining step is skipped. This is the
  "stop chasing the missing signature the moment the contract is signed" switch. Set it on any
  workflow whose later steps are reminders.
- **`unenroll_on_mismatch`** (boolean, default `false`) — when true, an `active`/`waiting`
  enrollment ends as `unenrolled` the moment the record no longer matches `conditions`. Use it
  for steps that only make sense while the original condition still holds (e.g. a sequence for
  bench employees that must stop when the employee gets placed).

#### Writing a field back — the `update_field` action

`update_field` sets, copies, or clears **one own column** on the triggering record.

- `config.field` — the target column, required. Must be an own column (no relation dot-path)
  and fillable.
- `config.value` — one of `{"mode": "set", "value": <scalar>}`, `{"mode": "copy", "source":
  "<dot-path>"}` (the source *may* cross relations, e.g. `company.default_priority`), or
  `{"mode": "clear"}` (writes null).
- **Enum columns** need a legal backing value. **Money columns** (`hourly_rate`,
  `billing_rate`, …) take **EUR, not cents** — the same convention as everywhere else in
  alluvo.
- **Action-managed lifecycle fields are hard-denied** (e.g. AssignmentContract
  `stage`/`status`), both when the workflow is saved and again when it runs. Do not try to
  route around it — if an operator wants a contract moved along, that is a lifecycle action
  (`→ manage-contract-lifecycle`), not a workflow field write.

This is the first workflow action that writes to a business record unattended, so treat it
like one: name the exact field, the exact resulting value, and how many records could match,
in the preview — and never use it to auto-clear a compliance or labour-law flag (see the
§ 4 ArbZG note below).

#### Trigger on an employee's Tagesabschluss (`0-422`, `trigger_event: "created"`)

"Wenn ein Mitarbeiter den Tag abschließt, poste/erstelle X" is a `created` workflow on model
type **`0-422`** (`TimeTrackingDayClosure`) — the row the employee's "Feierabend" writes
(`→ approve-stundenfreigabe`). It is one of two trigger targets you have to know by ID (the
other is `0-433`, the post-approval Dienstplan change, below):

- **`0-422` is not on the MCP allowlist.** `list-model-types` does list it — in the
  blocked table, as `not_available` with a reason — and `query-model` / `get-model` /
  `manage-model` refuse it. Pass the ID literally in
  `trigger_model_type`; do not go looking for it first and do not conclude it does not exist.
  `action: "test"` *does* work on it — it dry-runs against a given `record_id` or the newest
  closure — so use that to confirm conditions and placeholders before going live. When you need
  an actual `record_id` (for `test`, or to push a day in with `enroll`), `action:
  "list-candidates"` on the workflow is the only way to get one — see step 7.
- **Condition on `break_violated`, not on the two minute columns.** The row carries
  `required_break_minutes` and `tracked_break_minutes`, but the condition editor cannot compare
  two fields against each other. `break_violated` (boolean) is derived from exactly that
  comparison and is what "nur bei Pausenverstoß melden" must use:
  `field: "break_violated", operator: "equals", value: true`.
- **Other fields worth conditioning on or rendering:** `employee_id`, `date`, `closed_at`,
  `worked_minutes`, `first_start_at`, `last_end_at`, `no_break_reason`, `is_one_off`,
  `prevention_measures`, `support_requested`. `support_requested equals true` is the "employee
  asked for help" filter. Placeholders: the row's own attributes render flat
  (`{{worked_minutes}}`, `{{date}}`), and the record root key is
  `time_tracking_day_closure`, so the employee is reachable as
  `{{time_tracking_day_closure.employee.contact.first_name}}` — an Employee's identity fields
  (`first_name`, `last_name`, `email`) live on the linked **Kontakt**, so
  `employee.first_name` renders **empty**; `{{…employee.display_name}}` is the short form that
  does work — but it renders the tenant's `name_display_format`, so on a tenant set to
  `LastFirst` it produces "Müller, Anna". Use it where a full name belongs, and
  `…employee.contact.first_name` where a greeting does.
- **An unconditioned workflow here fires on every closed day of every employee** — that is one
  message per employee per working day. Say that number out loud to the operator before creating
  it; this is the model type where "no conditions" is loudest.
- **`created` fires once per employee+date, ever.** Closing a day writes the row keyed on
  employee + date, and a later withdraw-and-re-close *updates* that same row rather than creating
  a new one. So a `created` workflow does not fire a second time for a day the employee corrected
  — never promise "you'll be notified again if they redo the day".
- **`record_actions` buttons do not apply.** A day closure has no Slack-enabled actions (only
  AbsencePeriod `0-13` has any), so ask for a plain notification here.

Example: `trigger_model_type: "0-422"`, `trigger_event: "created"`, condition
`break_violated equals true`, action `send_slack_message` into the Disposition channel —
"Pausenverstoß beim Tagesabschluss von
{{time_tracking_day_closure.employee.contact.first_name}} am
{{date}}: {{worked_minutes}} min gearbeitet, Grund: {{no_break_reason}}."

> **Never build a workflow that weakens the § 4 ArbZG trail.** The closure IS the labour-law
> record. A workflow may report on it, raise a task, or route it to a human — it must never be
> presented to an operator as a way to clear, batch-acknowledge, or auto-resolve a break
> violation.

#### Trigger on a change to an already-approved Dienstplan (`0-433`, `trigger_event: "created"`)

"Melde mir, wenn ein Mitarbeiter einen freigegebenen Dienstplan ändert" is a `created` workflow
on model type **`0-433`** (`ShiftChangeLog`) — the § 11 Abs. 2 Satz 4 AÜG change trail
`→ build-dienstplan` step 6a describes. One row is written per Schicht whose time-relevant
fields changed (`date`, start, end, break), that was cancelled, that was deleted, or that was
**added** to the plan, **only** on a Periode in `published`, `locked` or `pending_approval`.
It is the second trigger target you have to know by ID, and it behaves like `0-422` in the
ways that matter:

- **`0-433` is not on the MCP allowlist.** Same shape as `0-422`: `list-model-types`
  reports it as `not_available` rather than omitting it, and `query-model` / `get-model` /
  `manage-model` refuse it. Pass the ID literally in
  `trigger_model_type`; `action: "test"` *does* work on it (a given `record_id`, or the newest
  row), so use that to confirm conditions and placeholders before going live. To learn a row's
  id at all — for `test`, or to push a missed change in with `enroll` — use `action:
  "list-candidates"` on the workflow (step 7); nothing else can list these rows.
- **`record_source` is what separates an employee's change from a Disponent's.** Condition
  `record_source equals external_panel` = the change came from the employee app;
  `manual` (web app) and `mcp` (this assistant) are operator edits. Without that condition the
  workflow reports the operator's own corrections back to them.
- **One trigger per changed Schicht.** An operator retiming seven days of a month fires the
  workflow seven times. The ~15-minute bundling (`→ build-dienstplan` step 6a) applies to the
  *employee's digest mail only* — it does not batch workflow runs. Say that number out loud
  before wiring a Slack action to it.
- **A Schicht ADDED to the plan fires too** (since 2026-08-12, `change_type = added`). The
  trail is no longer edits/cancellations/deletions only, so "sag mir Bescheid, wenn ein
  Mitarbeiter einen Einsatz einträgt" **is** buildable on `0-433` — as is the same alert for a
  Disponent's addition. The row is written by the creation itself, so it does not matter which
  surface the Schicht came from; filter by `record_source` as above if only one is wanted.
- **One addition is deliberately silent: the Schichten a client-portal booking creates.** That
  Periode is born `published`, so each booked Schicht would technically be an addition —
  reported minutes after the customer and the employee already received the Einsatzmitteilung
  for that very booking. A **later** booking onto the same Einsatz is not suppressed and does
  fire. (Same reasoning as the Umbesetzung suppression below.)
- **A full Umbesetzung fires nothing either.** Moving an employee's entire Einsatz away sends
  its own dedicated cancellation notice, and the change trail is deliberately suppressed for
  it (`→ build-dienstplan` step 6c) — so no row, no workflow run.
- **`change_type` has four values: `time_changed`, `cancelled`, `deleted`, `added`.** The
  employee app cancels and never hard-deletes, so an `external_panel` row is `time_changed`,
  `cancelled` or `added`; `deleted` is an operator path. Condition on it (e.g.
  `change_type equals added`) when the operator wants only one kind of change. Render it
  translated with `{{change_type | label:ShiftChangeType}}` — `added` reads "Hinzugefügt".
- **Placeholders.** The record root key is `shift_change_log`; the row's own columns render
  flat (`{{change_type}}`, `{{shift_id}}`, `{{employee_id}}`). `old_values` / `new_values` are
  **maps, not scalars** — `{{old_values}}` renders empty, address the field:
  `{{old_values.date}}` (`01.09.2026`), `{{old_values.start_at}}` / `{{new_values.start_at}}`
  (`07:00`, already in tenant time). `new_values` is absent on a deletion and `old_values` is
  absent on an **addition** — mirror images, since neither has a "before"/"after". So word an
  `added` message from `{{new_values.*}}` alone; `{{old_values.start_at}}` renders empty there.
  The employee is
  `{{shift_change_log.employee.contact.first_name}}` (or `…employee.display_name`, which
  renders the tenant's `name_display_format` — "Müller, Anna" on a `LastFirst` tenant), and the
  Schicht is `{{shift_change_log.shift.date | date}}`.
- **`{{reason}}` carries the employee's stated reason — and is empty for an operator's change.**
  Every employee change to a Dienstplan that has left draft has to state one (`→ build-dienstplan`
  step 6b), and it is stored per row, so an `external_panel` alert can quote *why* the plan moved
  instead of only *that* it moved — the single most useful thing to put in the Slack message. It is
  free text (max 500 characters), so keep it at the end of the line and never condition on its
  wording. `{{reason_by_user_id}}` is who stated it, deliberately separate from the row's creator.
  An operator's own edit records **nothing** here (`manage-shift-schedule` has no change-reason
  parameter), so a workflow without the `record_source equals external_panel` condition renders an
  empty reason on every Disponent row — one more argument for that condition.
- **On `change_type = deleted` the `shift.*` relation renders empty** — the Schicht is
  soft-deleted by then and the relation does not reach into the Papierkorb. Use the
  `old_values.*` snapshot for those messages; it is exactly what the Schicht looked like
  before removal.
- **`record_actions` buttons do not apply.** A change-log row has no Slack-enabled actions
  (only AbsencePeriod `0-13` has any), so ask for a plain notification here.

Example: `trigger_model_type: "0-433"`, `trigger_event: "created"`, condition
`record_source equals external_panel`, action `send_slack_message` into the Disposition
channel — "{{shift_change_log.employee.display_name}} hat den freigegebenen Dienstplan
geändert ({{change_type | label:ShiftChangeType}}): {{old_values.date}},
{{old_values.start_at}}–{{old_values.end_at}} → {{new_values.start_at}}–{{new_values.end_at}}."

That arrow wording only fits a retime. Use it verbatim only with `change_type equals
time_changed` added to the conditions — otherwise an `added` row renders the left-hand side
empty. For a workflow that covers every change type, word the message from
`{{new_values.*}}` and the `change_type` label alone.

> **The change log IS the AÜG § 11 Abs. 2 Satz 4 trail.** A workflow may report on it, raise a
> task, or route it to a Disponent — it must never be offered as a way to acknowledge away,
> batch-dismiss, or auto-approve an employee's Dienstplan change. Releasing or rejecting a
> change stays an operator decision (`→ build-dienstplan` step 6b-a).

#### Trigger on an incoming Meta-Lead (`0-313`) — and why `created` is the wrong event

"Sag mir in Slack Bescheid, wenn ein neuer Meta-Lead reinkommt" is a workflow on model type
**`0-313`** (`MetaLead`) — the row every Lead-Ad submission writes (`→ manage-meta-ads`).
Unlike `0-422`/`0-433` you do **not** have to know this one by ID: `MetaLead` is on the MCP
allowlist, so `list-model-types` shows it as `read_only` and `query-model` / `get-model` /
`search-model` accept it — resolve it there rather than hardcoding. Read-only means
read-only: `manage-model` create/update is rejected (leads are written only by the leadgen
webhook, the pull command and the lead processor), but a read-only type is still a legal
`trigger_model_type`.

- **Do not offer `Candidate` `created` as the equivalent.** The lead-to-Candidate mapper
  find-or-creates on `contact_id`, so a returning applicant — most of them — produces no
  `created` event at all (31 of 37 leads in one backfill). A trigger on `0-313` is the only
  one that sees every lead exactly once.
- **`trigger_event: "created"` fires with an EMPTY applicant.** On the webhook path the row
  is stored *before* the payload is fetched (capture-before-map, so a submission is never
  lost to a missing mapping), so at `created` time `status` is `pending`, `raw_data` is
  empty, and `{{lead_name}}` / `{{lead_email}}` / `{{lead_phone}}` all render **empty**.
  Use `created` only for a bare "a lead came in" count. The pull path
  (`query-meta-ads` `resource: "leads"` `action: "sync"`) does write the payload with the
  row, so the same workflow renders differently depending on how the lead arrived — never
  promise the name on `created`. (Reported to the alluvo team as alluvo#4458.)
- **Use `field_changed` on `status` for anything that names the applicant.**
  `trigger_config: {"field": "status", "to": "processed"}` = "a lead became a
  Candidate/Kontakt" — by then the payload and the mapping are both in place. `"to":
  "skipped"` = "a lead arrived and no active mapping converted it", which is the alert worth
  building for an operator (`→ manage-meta-ads` — fix the mapping, then `reprocess`).
  `"to": "failed"` catches the error path; `{{error_message}}` carries the reason.
  `status` has exactly four values: `pending`, `processed`, `failed`, `skipped`.
  `starts_matching` with `conditions` `status equals processed` is the equivalent shape.
- **Conditions must be own columns, and the three answer fields are not columns.**
  `lead_name`, `lead_email` and `lead_phone` are derived from Meta's positional `field_data`
  list, so they render in messages but **cannot** be conditioned on, sorted or filtered.
  Condition on `status`, `form_id`, `campaign_id`, `meta_page_id` instead.
- **Placeholders.** The record root key is `meta_lead`; own columns render flat
  (`{{status}}`, `{{leadgen_id}}`, `{{form_id}}`, `{{campaign_id}}`, `{{error_message}}`),
  and so do the three answers (`{{lead_name}}`, `{{lead_email}}`, `{{lead_phone}}`). A
  **custom qualifying question has no placeholder** — only name/email/phone are lifted out;
  everything else stays inside `raw_data`, which is a map, so `{{raw_data}}` renders empty.
  Once the lead is processed the person is reachable as
  `{{meta_lead.contact.first_name}}` (empty before that).
- **`record_actions` buttons do not apply.** A lead has no Slack-enabled actions (only
  AbsencePeriod `0-13` has any), so ask for a plain notification here.

Example: `trigger_model_type: "0-313"`, `trigger_event: "field_changed"`,
`trigger_config: {"field": "status", "to": "skipped"}`, action `send_slack_message` into the
Recruiting channel — "Meta-Lead ohne Zuordnung: {{lead_name}} ({{lead_email}},
{{lead_phone}}), Formular {{form_id}}. Mapping prüfen und nachverarbeiten."

### 7. Create, dry-run, and go live

- Create with `manage-workflow` `action: "create"`.
- A **record-less** scheduled workflow cannot be dry-run via `action: "test"` (there is no
  triggering record) — instead, confirm correctness via the automation-agent `test` from
  step 5, and review the config the operator already approved in step 6. A **scheduled
  enrollment** workflow (with `trigger_model_type`) *can* be dry-run: `action: "test"` with a
  `record_id` (or the latest record of that type) reports whether the conditions pass for
  that record. Do this before going live — it is the cheapest way to catch conditions that
  are too broad.
- The dry run also **walks the workflow's steps tree exactly as an enrollment would** —
  under `## Steps dry-run (branch decisions + rendered output, nothing sent):` it shows which
  `if`/`switch` branch the record takes, the rendered output of every `action` node on the
  taken path, and annotates `delay`/`wait_until` nodes without sleeping. Nothing is sent or
  executed. A workflow still on the legacy flat `actions` list is walked as the same
  converted tree a live enrollment would run — so what `test` shows is what would actually
  fire, branch decisions included. Read the taken branch back to the operator; a record
  landing in the wrong `if`/`switch` branch is as common a bug as a too-broad condition.
- The workflow is created enabled. If the operator wants to stage it first, `action:
  "disable"` after create, then `action: "enable"` when ready to go live. Confirm the go-live
  moment with the operator explicitly.
- After the schedule has run at least once, `action: "list-runs"` shows past executions
  (status, timestamp, any error).
- `action: "list-enrollments"` (`workflow_id` required, optional `status` filter and `limit`,
  default 20) is the per-record view: which record, current status, the node it is paused at,
  when it resumes, when it started/finished. This — not `list-runs` — is how you answer "why
  hasn't this record advanced yet"; a `waiting` row with a resume timestamp is the normal
  answer for a workflow with a `delay`.
- `action: "unenroll"` (`enrollment_id` required, optional `reason`) ends one `active` or
  `waiting` enrollment permanently — it will not resume. It needs update permission on the
  workflow, and it refuses an enrollment that already finished rather than silently doing
  nothing. Use it to pull a single record out of a running sequence; use `disable` when the
  operator wants the whole workflow stopped. Confirm with the operator first: there is no undo,
  and the record can only re-enter later if `allow_reenrollment: true`.
- `action: "enroll"` (`workflow_id` + `record_id` required, optional `force`, `reason`) is the
  inverse: it pushes **one** record into the workflow by hand, so the steps run now. This is how
  a record that existed *before* the workflow was created — or that was written while the
  workflow was disabled — still gets announced. It needs update permission on the workflow, and
  it is **single-shot** (no `confirmed` preview) and really fires the actions, so get the
  operator's explicit go-ahead first. Four things to say before offering it:
  1. **The conditions still apply.** A record the workflow was scoped to exclude is refused with
     an explicit error. `force: true` is a deliberate bypass and the result marks the enrollment
     as forced — never reach for it just to make a call succeed; the workflow was narrowed for a
     reason.
  2. **`allow_reenrollment` decides whether a repeat is possible at all.** A second enrollment is
     never created while an earlier one is `active` or `waiting`; once one has *finished*, a
     second push needs `allow_reenrollment: true` on the workflow — the refusal names the
     workflow's current setting. With the flag on, dedup is off, so a manual push is not silently
     swallowed.
  3. **The workflow must be enabled** — a disabled one refuses the enrollment outright.
  4. **The message says it was pushed in.** The Slack provenance footer gains a „manuell
     nachgereicht" marker, so the post cannot be mistaken for a fresh change made by whoever
     pushed it.
- `action: "list-candidates"` (`workflow_id` required, optional `limit`, default 20, capped at
  50) is the picker for `enroll` and read-only: the most recent records of the workflow's trigger
  model type as a table of id, creation time, and whether each one matches the conditions — a row
  marked `no` needs `force: true`. It is also the **only** way to see records of a trigger-only
  type (`0-422` TimeTrackingDayClosure, `0-433` ShiftChangeLog): those have no MCP read surface
  at all, so their ids are otherwise unobtainable.
- Both `enroll` and `list-candidates` refuse a **record-less** scheduled workflow (no
  `trigger_model_type`) — there is no record to push in or list.
- To retire an agent, `manage-automation-agent` `action: "disable"` (or the workflow's own
  `disable`) rather than `delete` — a **system** agent (`is_system: true`, e.g. shipped
  reference agents) rejects `delete` outright ("…is a system agent and cannot be deleted. Use
  the `disable` action to switch it off instead."). Agents the operator created via this skill
  are not system agents and can be deleted once disabled, but disabling is usually the safer
  default (preserves history, reversible).

## Capabilities — `execute` vs `propose`, and the retired `enabled_tools`

`capabilities` is one object on the Agent, `{"<key>": "execute" | "propose", …}`, validated
against the catalogue `describe-tools` prints. Facts that decide how you build it:

- **`execute`** = the agent may call this capability as a **tool during its own run**, with no
  human gate. This is the only mode that matters for a scheduled/workflow-triggered agent:
  its tool set is exactly the `execute` entries (`AutomationToolRegistry::resolveFor()`
  filters on the effective `execute` set). A `(WRITE)` key in `execute` mode writes
  unsupervised (draft-only where the model enforces it) — grant deliberately.
- **`propose`** = the post-run classifier of an inbox deployment **may put this step on the
  run card**. It does nothing on a scheduled run. Most classifier steps (`create_note`,
  `send_email`, `send_ticket_reply`, `close_ticket`, …) are `propose`-only; setting them to
  `execute` is rejected. **`propose` does not mean "always approval-gated"** — the tool's own
  description says a human must confirm before anything happens, but which proposed steps
  pause as `awaiting_approval` and which run unattended is fixed per step type
  (`create_task`, `manage_model`, `create_note`, `enrich_relationship`, … execute on their
  own; replies, emails, meetings, ticket control, contract proposals pause) — see *Inbox
  deployments → the step whitelist*. Grant a `propose` key with that in mind.
- **Omitted key = off.** There is no `"off"` value — leave the key out. An empty/omitted
  `capabilities` map means the agent can call **no** tool at all.
- **Validation is strict and self-explaining:** an unknown key → `Unknown capability: <key>.
  Valid keys: …` (the full list); a mode the key does not support →
  `Capability "<key>" does not support mode "<mode>". Supported: <modes>`; anything but
  `execute`/`propose` → `Invalid mode …`. Fix the payload from the message; never retry with a
  guessed key.
- **`enabled_tools` is deprecated, still accepted.** A plain array of tool names is mapped onto
  `{<name>: "execute"}` (kebab-case names are snake_cased: `manage-model` → `manage_model`)
  and **ignored whenever `capabilities` is also given**. New payloads use `capabilities`
  only; when you `update` an agent someone else built with `enabled_tools`, `get` already
  returns it as `capabilities` — `enabled_tools` no longer appears in `get`/`list` output
  (`list` shows «N capability(ies)»).
- **On an inbox deployment the agent map is a *ceiling*, not the whitelist** — the deployment
  can only downgrade (`execute` → `propose` → off), never upgrade, and for a key the agent
  leaves unmentioned the deployment supplies its own value. Which deployment value applies —
  and why `deploy`'s `enabled_steps` currently does *not* set it — is spelled out under
  *Inbox deployments → the step whitelist*.

## Prompt building blocks — system `blocks` and tenant Bausteine (`0-442`)

An automation agent's prompt is not just `instructions`. It is composed, in this fixed order:

1. **Aktuelles Datum** (`current-date`) — always, unconditionally.
2. The **selected system blocks** (`blocks`) — see the rendering rule below.
3. **Rangfolge-Erklärung** (`precedence`) — only when at least one system block or Baustein
   is present; it tells the model that nothing below may override what is above.
4. The agent's own **`instructions`** (the base — always, even when blank).
5. A deployment's `instructions` (inbox path only).
6. The agent's attached **Bausteine** (`instruction_block_ids`), in the stored order, each as
   `### Baustein: <name>` — then any deployment-level Bausteine (Studio-only, see below).

Bausteine sit at the very bottom **by design**: they are additive and can never override the
agent's `instructions` or a system block. Put *must*-rules (data minimization, what never to
report) into `instructions`; use Bausteine for reusable, tenant-wide phrasing (signature-style
closing lines, house glossary, the "how we address clients" paragraph) that several agents
should share.

### System blocks — `blocks`

- **Discover, don't guess:** `manage-automation-agent` `action: "describe-tools"` ends with a
  `# Blocks` list of every valid key with its German label. Four are marked
  **`(always on — not deselectable)`**: `current-date`, `precedence`, `agency-location`,
  `ai-disclosure`. The other four are operator-selectable: `brand-voice`, `formality`, `icp`,
  `selling-profile`.
- **What actually renders (verified against the composer, not the tool text):**
  - `blocks` **omitted or `[]`** → **no** system block renders at all — only the date (and
    `precedence` if a Baustein is attached). This keeps every pre-existing agent's prompt
    byte-identical; it is also what the Agent Studio form saves for a fresh agent.
  - `blocks` with **at least one selectable key** (e.g. `["brand-voice"]`) → that key renders
    **plus** `agency-location` and `ai-disclosure` are forced on alongside it. So the
    "always on" marker means "cannot be *deselected* once you select anything", not "renders
    on an agent with no selection".
  - The tool's own description claims the opposite for the omitted case ("omit to include
    every declared block") — that wording is wrong for automation agents and is tracked as
    api issue #4026. Trust the rule above; when it matters, have the operator check the
    agent's prompt layer preview in the Agent Studio — it is composed by the same code as the
    real run, so it shows exactly which blocks render.
- `blocks` is a **full replacement** on `update` — read the current value from `get` first and
  send the whole list back. `get` returns `blocks` verbatim (`null` = never configured).
- Content is tenant data, not agent config: `brand-voice` reads the `brand_identity` settings
  (mission/bio, writing style, banned terms, inclusivity), `agency-location` reads
  `company_city`/`company_state` from the `general` group of `manage-settings` (while
  `company_city` is empty the block still renders — as an instruction to never claim or guess a
  location), `icp`/`selling-profile` read the tenant's IdealCustomerProfile / SellingProfile
  records. `brand-voice`, `icp` and `selling-profile` render **nothing** when their source is
  empty even if selected — fix the source, not the selection (`→ define-icp` for the ICP side).
  `formality` (Anrede Du/Sie) is resolved per *Contact*; an automation agent's run carries no
  Contact, so selecting it there is harmless but currently renders nothing.

### Tenant Bausteine — `InstructionBlock` (`0-442`)

- **Read/list:** `query-model` / `search-model` / `get-model` with `model_type: "0-442"`.
  Fields: `name`, `content`, `is_active`. Confirm the exact schema with `get-model-schema`
  (`context: create` / `update`) before writing — as always.
- **Create/edit:** `manage-model` on `0-442` (`name` and `content` required on create;
  `is_active` optional). Two-stage like every write: `confirmed: false` preview → show the
  operator → `confirmed: true`. Gated by the `instruction_blocks.*` permissions.
- **Attach / order:** `manage-automation-agent` `create` or `update` with
  `instruction_block_ids: [<id>, <id>, …]`. Semantics that matter:
  - **Full replacement (sync), not append.** Omitting the param leaves attachments untouched;
    passing it replaces the whole set. Always `get` the agent first (it returns
    `instruction_block_ids` in current render order) and send the complete list back — or you
    silently detach the rest.
  - **Array position = render order.** The order you send is persisted (`sort_order`) and is
    exactly the order the Studio's drag-sortable list shows and the prompt renders. To reorder,
    resend the same ids in the new sequence.
  - Unknown ids are rejected ("One or more instruction_block_ids do not exist in this tenant.").
  - **Tenant-owned only, on both ends.** `get` reports only tenant Bausteine under
    `instruction_block_ids`; personal instructions attached to the agent are filtered out. The
    `update` sync carries those user-owned attachments through unchanged, so the normal
    `get` → modify → `update` round-trip can no longer detach somebody's personal instructions
    as a side effect. The corollary: you also cannot detach one from here — `manage-ai-preferences`
    is the only path.
  - An attached Baustein with `is_active: false` stays attached but is **skipped** at render
    time — deactivating is the reversible way to switch a shared snippet off everywhere without
    touching each agent's list.
- **One shipped, deliberately inactive block:** "Ausnahme für Leitungs-/Führungsrollen
  (archiviert)" (`is_active: false`, attached to nothing) archives prompt text that was removed
  from the Bewerber-Flow default. Leave it alone unless asked — the section on
  `candidate_flow_prompts` below explains what it is and why re-attaching it does not restore
  the old behaviour.
- **Deployment-level Bausteine** (attached to one inbox deployment rather than the agent) exist
  but are **not** settable over MCP — `deploy` has no `instruction_block_ids`. Point the operator
  to the Agent Studio for those; agent-level ones cover most needs.
- **Scope of MCP visibility.** `manage-automation-agent` `list`/`get` only see *automation*
  agents. The tenant's **conversational** agents (Talent Hub, Profil-Assistent,
  Requalifizierung, Mitarbeiter-Support) and its **task** agents are reached through the
  separate `manage-agent-prompt` tool — including `attach-baustein` / `detach-baustein` /
  `reorder-bausteine` for exactly this. See *Conversational and task agents* below for the
  split and its different attach semantics.

### Personal instructions — `manage-ai-preferences`

An operator's **own** additive instruction on **one agent** — the rows the agent page's
*Anweisungen* tab edits. It layers *under* the base prompt and *under* the tenant's Bausteine
and affects only that operator's own runs of that agent. This is the only tool that reaches
them; `manage-agent-prompt` and `manage-automation-agent` treat a user-owned id as "not found".

- **Actions:** `get` (read), `set` (replace — an **empty string deletes** it), `list`
  (every personal instruction on the agent, with owner names).
- **`agent`** — optional: an `agent_key` (`activity-takeover`, `email-formulation`, …) or the
  numeric agent row id. Defaults to `activity-takeover` (the KI-Nachbearbeitung agent), so a
  call that omits it still means what it always meant. Get the ids/keys from
  `manage-agent-prompt` `list`.
- **Not every agent accepts one.** An agent with personal instructions switched off is refused
  by name rather than storing text nothing would render. Relay the refusal and offer
  `manage-agent-prompt` (change what the agent says for *everyone*) instead.
- **Permissions:** your own instruction needs none — omit `user_id`. Passing another
  operator's `user_id`, or using `list`, needs `settings.manage`.
- **`list` means "everyone on this agent", not "every user".** It returns the users who
  actually stored a personal instruction there (columns: User ID / Name / Personal
  instruction), so an operator missing from it simply has none — not a permissions problem.
  Take the `user_id` for a follow-up call from this table verbatim: it is **not** the id other
  tools report for tenant users.
- **`task_auto_accept`** rides on `set` and is unrelated to the instruction text: it decides
  whether the AI follow-up creates its proposed tasks outright (retractable from the run) or
  proposes each for confirmation. Omitting either param leaves it unchanged — setting one never
  clears the other.
- **Company-wide ≠ personal.** "Alle sollen das so machen" is a Baustein on the agent
  (`manage-agent-prompt`), not a personal instruction, and no longer a `manage-settings` field.

**Worked mini-flow — "häng unseren Standard-Abschluss an den Monatsbericht":**
1. `search-model` `0-442` by name → id 17 exists, `is_active: true`.
2. `manage-automation-agent` `get` `agent_id: 42` → `instruction_block_ids: [9]`.
3. Preview to the operator: "attach #17 after #9 → order `[9, 17]`; `blocks` unchanged".
4. `manage-automation-agent` `update` `agent_id: 42, instruction_block_ids: [9, 17]`.
5. `test` the agent and show the operator the output actually reflects the new closing line.

### Tags — the tenant-wide vocabulary (`0-443`)

Tags are free-form labels drawn from **one tenant-wide pool** shared by every taggable record —
the way to group agents ("Vertrieb", "Monatsbericht", "experimentell") without inventing a
field. `Agent` is one of **twelve** taggable model types: Company `0-3`, Contact `0-105`,
Employee `0-2`, Candidate `0-81`, StaffingDemand `0-415`, Task `0-5`, Ticket `0-300`,
KnowledgeBase `0-180`, KnowledgeBasePage `0-181`, NewsArticle `0-187`, Workflow `0-365`,
Agent `0-400`. The rules below — names not ids, full replacement, unknown names created,
`tags_colors` on read — hold for every one of them; `using-alluvo-operator` → *Tagging a
record* carries the cross-cutting version, including the rule that a person's tags live on
their **Kontakt** (so a Mitarbeiter is tagged via Contact `0-105`, not via `0-2`). Only
outside that list of twelve is `tags` not a field, and there a custom field
(`manage-custom-field`) stays the answer.

- **Tag an agent — pick the write path by agent type:**
  - **Automation agent:** `manage-automation-agent` `create` / `update` with
    `tags: ["Vertrieb", "Monatsbericht"]`.
  - **Conversational or task agent:** `manage-agent-prompt` `action: "set-tags"` with
    `agent_id` + `tags`. An automation agent is refused here with a pointer back to
    `manage-automation-agent`. Unlike every other write in that tool this one is **one-stage —
    no `confirmed` needed**: a tag is a label, it changes nothing the agent says and is
    trivially reversible.
  - **Either type:** `manage-model` `update` on `model_type: "0-400"` with `tags` also works
    (see *Renaming and tagging an agent* below) — two-stage like every generic write.
  - **Names, not ids — and an unknown name is created for you.** No lookup and no "create the
    tag first" step; a name that does not exist yet becomes a new tenant-wide tag on save.
  - **Full replacement (sync), not append** — same rule as `instruction_block_ids`. Omitting
    `tags` leaves them untouched; passing it replaces the whole set; `[]` clears them. `get`
    returns the agent's current `tags`, so read it, extend the list, send the complete list
    back — or you silently strip the rest.
  - Names collapse case- and whitespace-insensitively (`Vertrieb` and `vertrieb ` are one
    tag), and the **first** spelling wins as the display name — a later differing case never
    silently renames the existing tag.
- **Manage the vocabulary itself** (rename, recolor, delete): `query-model` / `search-model` /
  `get-model` / `manage-model` / `delete-model` with `model_type: "0-443"`. Writable fields are
  `name` (required) and `color` — one of `gray`, `blue`, `indigo`, `purple`, `success`,
  `warning`, `danger`. `slug` is derived from `name` on save and is **not** writable (a rename
  carries the slug with it). Two-stage like every write: `confirmed: false` preview → show the
  operator → `confirmed: true`. Gated by the `tags.*` permissions; merely *attaching* a tag is
  gated by the target record's own update permission instead.
  - **Renaming or deleting a tag hits every record carrying it, tenant-wide.** Say so in the
    preview. When the operator means "this one agent shouldn't have that tag", remove it from
    the agent's own `tags` list — do not delete the tag.
- **Reading tags.** A record returns `tags` as the same flat list of names, plus a
  `tags_colors` companion map (name → color) for display. `tags` is a *relation*, not a
  column, so it does not appear in a plain column listing — `get-model-schema` does advertise
  it and the write paths do honour it.

**Worked mini-flow — "häng dem Monatsbericht-Agenten den Tag Vertrieb an":**
1. `manage-automation-agent` `get` `agent_id: 42` → `tags: ["Monatsbericht"]`.
2. Preview to the operator: "ergänzt `Vertrieb` → `["Monatsbericht", "Vertrieb"]`; den Tag gibt
   es noch nicht, er wird tenant-weit neu angelegt."
3. `manage-automation-agent` `update` `agent_id: 42, tags: ["Monatsbericht", "Vertrieb"]`.

Same flow for a conversational or task agent, with `manage-agent-prompt` `get` in step 1 and
`manage-agent-prompt` `action: "set-tags"` in step 3 — no `confirmed` on that call.

## Inbox deployments (Posteingang-Agenten)

A **deployment** binds an automation agent to an Inbox so it reacts to *inbound tickets*
instead of a clock. Three verbs on `manage-automation-agent`: `deploy`, `undeploy`,
`list-deployments`. Steps 6–7 (the scheduled workflow) do not apply — a deployment needs no
workflow at all.

### First: the tenant feature gate

Inbox agents are gated by a **tenant feature flag that is off by default**. Creating a
deployment while it is off succeeds and then nothing ever fires — no runs, no error, no
warning. Tell the operator this before deploying, and if `list-deployments` shows an active
deployment but no run cards appear on tickets, treat the flag as the first suspect. It is
**not** operator-switchable — the alluvo team enables it per tenant. Never conclude "the
agent is broken" without ruling this out first.

### What a deployed agent actually uses

A deployment run reuses the Agent's `execute`-mode `capabilities` (the agent can still look
things up) and its `pseudonymize_pii` flag, but **not its `output_schema`** — the run is forced onto the
inbound classifier's own schema, so whatever `output_schema` you designed in step 3 is unused
here. What shapes behavior instead is a fixed inbound-classifier prompt (action catalogue,
record-reference rules, date grounding) with two **additive** instruction layers on top: the
Agent's own `instructions`, then the deployment's `instructions` for this one inbox. Later
layers augment, never replace. So put inbox-independent behavior in the agent and
inbox-specific behavior ("this is the Bewerber inbox, always …") in the deployment's
`instructions`.

Consequence: **`action: "test"` does not exercise the deployment path** — there is no dry-run
for a deployment. The step whitelist (agent `capabilities` ceiling + the deployment's own map,
see below) and the caps are what makes a first rollout safe, so set them deliberately rather
than relying on a test.

### `deploy`

Two-stage: without `confirmed: true` it returns a preview (agent, inbox, channel, owner,
step whitelist as derived from `enabled_steps` — **not** what will apply at run time, see
below — instructions excerpt) and writes nothing; show that preview to the operator, then
call again with `confirmed: true`.

| Param | Notes |
|---|---|
| `agent_id` | required — must be an automation agent |
| `inbox_id` | required |
| `owner_id` | **required** — the run-as identity for the deployment's actions. Must resolve to an **active internal** tenant user; stricter than `owner_id` on `create`/`update`, which only requires an active user. Confirm the choice with the operator, since every record the agent touches is attributed to that person. |
| `inbox_channel_id` | optional — must belong to `inbox_id`. Omit to cover **every** channel of the inbox. |
| `instructions` | optional — the per-deployment additive layer |
| `enabled_steps` | optional — **currently inert at run time**, see below |
| `daily_cap` / `per_ticket_daily_cap` | optional integers; omitted means **200** / **5** |
| `is_active` | optional bool, defaults `true`. Pass `false` to stage a deployment the operator wants to switch on later. |

`(agent_id, inbox_id, inbox_channel_id)` is unique — a duplicate is rejected with a clear
message. "All channels" (`inbox_channel_id` omitted) is its own distinct slot, so one agent
can hold both an all-channels deployment and a channel-specific one on the same inbox.

**`confirmed` is new on this tool and applies to `deploy`/`undeploy` only.** `create`,
`update`, `delete`, `enable` and `disable` are still single-shot — keep showing the operator
an explicit preview and getting approval before calling those (steps 3–4).

### The step whitelist — how a deployment's proposals are actually gated

What the classifier may **propose** on a run card is the set of capabilities that resolve to
`propose` for *this agent on this deployment*. That is computed, per key, from two layers:

1. **The deployment's own capability map** (`AgentDeployment.capabilities`). When it is
   empty (the normal case for anything created over MCP — see the caveat below) a
   conservative default applies: `create_task`, `create_note`, `manage_model`,
   `enrich_relationship`, `create_staffing_requirement` are `propose`, everything else —
   replies, emails, meetings, invites, contract preparation, owner reassignment, ticket
   control — is off. When it is set, it is an **exhaustive** whitelist that *replaces* the
   default (it never augments it).
2. **The agent's `capabilities` as a ceiling.** For a key the agent mentions, the deployment
   can only downgrade it (`execute` → `propose` → off), never upgrade it; a key the agent does
   not mention is left to the deployment's value. So `{"send_email": "propose"}` on the
   agent does **not** enable `send_email` on a deployment whose own map does not list it.

> **`enabled_steps` on `deploy` currently does not feed this.** `deploy` validates and stores
> `enabled_steps` (the preview and `list-deployments` echo it back), but the run-time filter
> reads only the deployment's `capabilities` map, which `deploy` never writes — so every
> MCP-created deployment runs on the default set above, no matter what `enabled_steps` you
> pass. Widening (`["send_ticket_reply"]`) silently changes nothing; narrowing
> (`["create_note"]`) does not narrow either. Tracked as api issue #4027. Until it is fixed:
> say so to the operator, do not promise a whitelist you set over MCP, and for anything
> beyond the default set point them to the deployment's capability picker in the Agent Studio
> ("Einsatzorte") — that form is what actually writes the map. Verify the outcome on the first
> real run card, not on the `deploy` preview.

Two things to state precisely to the operator once the whitelist is set (by whichever route):

- **Out-of-whitelist directives are dropped, not queued for approval.** The run's summary
  records it («N Vorschläge außerhalb des erlaubten Umfangs verworfen (…)»). The whitelist is
  therefore the boundary of what the agent can do at all — widen it deliberately, one
  capability at a time.
- **Whitelisted steps largely execute unattended.** The gated ones pause as an
  `awaiting_approval` card: `send_email` and `send_invite`, `reassign_owner`, the meeting steps
  (`create_meeting`, `move_to_meeting`, `update_meeting`), `send_ticket_reply`, the four
  ticket-control steps below, and the two contract proposals (`prepare_contract_extension`,
  `prepare_assignment_contract`) whenever they resolve to a concrete record. The rest run on
  their own. In particular the default whitelist's
  `manage_model` **writes records without asking** — each executed step is individually undoable
  from the run card in the ticket, but it does write first. Grant a capability only when
  unattended execution of it is genuinely wanted.
- **`manage_model` refuses Art. 9 GDPR special categories in free text.** A directive that
  would write health, disability, pregnancy, religion, union or party membership, sexual
  orientation or a criminal record into `bio`, `notes`, `availability_notes`,
  `other_profile_notes`, `headline` or `summary` is rejected outright — the step fails with a
  message naming the field and the matched terms and pointing at the structured field that does
  hold the fact (e.g. `Employee.is_severe_disability` / `degree_of_disability`). This is by
  design, not a step to work around: `bio` is rendered on the customer-facing profile. Tell the
  operator to expect it whenever the agent summarises call notes or mails into profile text —
  the fact belongs in its structured field or in a task for the responsible colleague.

Valid step keys (identical to the `[propose]`-capable capability keys `describe-tools`
lists, and to `AiTakeoverStepType`): `rewrite_body`, `activity_stored`, `create_task`,
`prepare_email`, `send_email`, `create_note`, `manage_model`, `create_meeting`,
`move_to_meeting`, `update_meeting`, `send_invite`, `send_profile_completion_link`,
`reassign_owner`, `create_staffing_requirement`, `enrich_relationship`,
`prepare_contract_extension`, `create_reservation`, `prepare_assignment_contract`,
`send_ticket_reply`, `close_ticket`, `set_ticket_status`, `assign_ticket`,
`set_ticket_priority`, `classify_inbound_email`, `mark_ai_checked`, `send_redirect_reply`,
`archive_mail`. An unknown value is rejected with the full list.

### Ticket control: what the agent may do to the ticket itself

Beyond drafting a reply, an inbox deployment can steer the ticket its run answers — but only
when the operator whitelists it. Four step types, all **off by default**:

| Step | What it proposes |
|---|---|
| `close_ticket` | Close the ticket, with a `close_reason_key` picked from the tenant's **active** `ticket_status` close reasons (the real list is injected into the agent's prompt, so it cannot invent one) plus a `close_reason_note` when that reason requires one. On a Gmail inbox an approved close also **archives the mail thread** (reversed if the ticket is reopened) — see `→ clean-inbox`. |
| `set_ticket_status` | Move the status between `new`, `waiting_on_user` and `waiting_on_us`. Never `closed` — that is `close_ticket`'s job. |
| `assign_ticket` | Hand the ticket to a named colleague (`assignee_user_id`). The step is rejected outright when that user is **not a member of the ticket's own inbox** — an agent cannot assign work to someone who has no access to it. |
| `set_ticket_priority` | Raise or lower `low` / `medium` / `high` / `urgent` on an explicit escalation or all-clear. |

Two facts to state to the operator before widening the whitelist to any of them:

- **Every one of them is gated, always.** Each becomes a single `awaiting_approval` step — the
  ticket is not closed, re-statused, reassigned or re-prioritised until a human approves the
  card. Gating is a property of the step, not of who triggered the run, so this holds for an
  unattended inbox deployment too. There is no configuration that makes them auto-execute.
- **Gated is not harmless.** An approval queue that fills with proposals nobody reads is how a
  ticket gets closed on a glance. Whitelist `close_ticket` only for an inbox whose runs are
  actually reviewed, and prefer starting with `set_ticket_status` / `set_ticket_priority`
  (reversible in one click) over `close_ticket` (which writes a close reason into the record).

Nothing here weakens the evidence rule that `→ clean-inbox` works under: an agent proposal is
not evidence. The operator approving the card is the one who has to be able to justify the
close reason.

### When it fires, and the caps

- On **every** genuinely inbound message from the contact — not only the first of a ticket. The
  agent's own sends and an operator's manual reply never re-trigger it.
- Burst channels (WhatsApp, chat, web) are debounced ~2 minutes, so a contact typing four
  messages yields **one** run covering all of them. Email and phone fire without that delay.
- `daily_cap` (default 200) bounds runs per deployment per day; `per_ticket_daily_cap`
  (default 5) bounds them per ticket per day. Hitting either **silently skips** the run — it
  is logged server-side, not surfaced in the ticket. So on a long thread, "the agent stopped
  reacting" is usually the per-ticket cap, not a failure. Set both explicitly when the
  operator wants a cautious rollout.

### `undeploy` / `list-deployments`

- **`undeploy`** takes `deployment_id`; two-stage (preview → `confirmed: true`). It
  **soft-deletes**. ⚠️ The uniqueness slot is *not* released: re-deploying the same
  agent/inbox/channel combination afterwards fails with "already deployed to inbox …" even
  though `list-deployments` no longer shows it. So treat `undeploy` as **one-way** and warn the
  operator before confirming. To switch a deployment off reversibly, deploy it with
  `is_active: false` from the start, or use the settings UI (Inbox settings →
  "Posteingang-Agenten"), which can edit an existing deployment's active flag, instructions,
  steps and caps — the MCP tool has no update verb for a deployment.
- **`list-deployments`** is read-only, no confirmation. Optional `inbox_id` / `agent_id`
  filters. Per deployment it returns id, active flag, agent, inbox, channel (or "all
  channels"), owner, enabled steps (or `Default`), caps and last run time — this is the answer
  to "which agents run on which inbox". For filtering beyond those two params, `query-model` on
  `0-306` (`agent-deployments`) reads the same records.

Permissions: `deploy`/`undeploy` need the automation-agents **update** permission,
`list-deployments` the view-any permission.

### Data protection for a deployed agent

A deployment reads whatever arrives in the inbox — including unsolicited health data,
applications and pay questions — and acts under `owner_id`'s permissions. Two rules:
keep `owner_id` a person who legitimately has access to that inbox's content, and do not
whitelist a step type that would move sensitive content somewhere new (`send_email`,
`send_ticket_reply`, `manage_model` onto unrelated records) unless the operator has
explicitly asked for it. Note `pseudonymize_pii` only tokenizes **tool output** — the mail
body, the contact and the assignable-user roster are part of the prompt and reach the model as
written, so it is not a mitigation for sensitive inbound content.

## Conversational and task agents — `manage-agent-prompt`

`manage-automation-agent` owns automation agents and nothing else. Everything the tenant's
**conversational** agents (the chat/WhatsApp assistants that talk to Bewerber and
Mitarbeiter — Talent Hub, Profil-Assistent, Requalifizierung, Mitarbeiter-Support) and its
**task** agents (the code-defined extraction/scoring/classification agents) are told is
managed by a second tool, `manage-agent-prompt`.

**The split is strict, and the direction matters:**

- Automation agent → `manage-automation-agent`. `manage-agent-prompt` can *read* one
  (`list`, `get`), but every write on one is refused with a pointer back — capabilities,
  `output_schema`, `pseudonymize_pii` and deployments exist only there.
- Conversational or task agent → `manage-agent-prompt`. `manage-automation-agent` cannot
  see these at all.
- There is **no `create` and no `delete`** here. Conversational agents come from tenant
  migrations, task agents from the code registry — they can be configured, never created or
  removed. Don't offer to build one.

**Verbs:** `list`, `get`, `set-instructions`, `set-blocks`, `attach-baustein`,
`detach-baustein`, `reorder-bausteine`, `enable`, `disable`, `set-tags`, `list-flow-sections`,
`set-flow-section`, `reset-flow-section`.

### Always read the composed prompt first

`get` (params: `agent_id`) returns the agent's **composed prompt, section by section** —
each part with its `tier` (`law`, `capability`, `policy`, `play`, `facts`), a human `label`,
the `source` to change it at, and `editable`. It is the only way to see what an agent
actually says, and it is composed by the same builder the real run uses, so it cannot show
something the runner would not send. The converse is not currently guaranteed: on a **task**
agent it can *omit* a declared system block the run does render (api issue #4380 — see *The
call-notes classifiers' two settings-backed blocks* below). Never write a layer without reading it: the layers
stack, and an instruction that contradicts a section above it does not win — it just makes
the agent inconsistent. `list` (optional filters `type`: `conversational` | `automation` |
`task`, and `is_active`) is how you find the `agent_id`; each row carries `writable_here`.

### The three editable layers — not interchangeable

1. **Flow sections** (`list-flow-sections` / `set-flow-section` / `reset-flow-section`) —
   REPLACE one named section of the flow's own prompt. Stored **per tenant, not per agent**:
   editing a section on the Requalifizierungs-Assistent also rewrites it for every other
   conversational agent whose flow renders it. `list-flow-sections` names those under
   `shared_with`, and the write preview repeats the warning — read it before writing, and
   tell the operator which other agents move with it. Each section also reports its `text`,
   the shipped `default`, and `configured` (whether the tenant has overridden it).
   Conversational agents only; on a task or automation agent the action errors out.
2. **`instructions`** (`set-instructions`, params `agent_id` + `instructions`) — the agent's
   own additive text, this agent only. Renders below the flow prompt and above the Bausteine.
   An empty string clears the layer.
3. **Bausteine** (`attach-baustein` / `detach-baustein` / `reorder-bausteine`) — the same
   `0-442` records described above, attached per agent in an operator-controlled order.

Layers 2 and 3 are **additive** and capped by the binding precedence section: they add to the
flow's rules but never override them. A rule the flow states outright cannot be undone by a
Baustein — edit the flow section that carries the rule, or it is product behaviour and is not
editable at all.

**`blocks`** (`set-blocks`, params `agent_id` + `blocks`) is a different thing from Bausteine
despite the name: it selects which code-defined system blocks render for this agent. Pass the
**full desired list** — it replaces the previous selection; omitting the param leaves it
untouched, `[]` switches off every removable one. Law-tier blocks (AI disclosure) render
regardless.

- **The key list is per agent, not one global set.** The tool's `blocks` parameter text names
  only `brand-voice`, `agency-location`, `formality`, `ai-disclosure` — that is the
  conversational set. Every code-defined agent declares **its own** keys, and that declaration
  is the **ceiling**: a key the agent never declared is not rendered no matter what you select.
  The two call-notes classifiers declare `callback-timing` and `task-routing` and none of the
  four above (next subsection). Never offer a key from memory — read the agent's own sections
  with `get` first.
- **On a code agent, a never-configured (`null`) selection means every declared block is ON**,
  not off — the opposite of an automation agent, where `null`/`[]` render nothing. An explicit
  `[]` here still keeps the non-removable ones. Selecting is only how you switch a *removable*
  block off.

**Baustein attach semantics differ from the automation tool — do not carry the habit over.**
`manage-automation-agent` syncs the whole set from `instruction_block_ids`; here each verb is
incremental. `attach-baustein` takes one `instruction_block_id` plus an optional `sort_order`
(defaults to last) and only *moves* one that is already attached. `reorder-bausteine` takes
`instruction_block_ids` — the attached set in the desired render order — and **reorders only,
never detaches**: ids you leave out stay attached and sort after the listed ones. Ids that are
not attached are rejected, not attached implicitly. Detaching is `detach-baustein`, one id at
a time.

**All three verbs are tenant-Baustein-only.** A user-owned block id (an operator's personal
instruction) behaves as **not found** here, and `get` leaves those blocks out of the reported
attachment set — the assistant can neither graft one operator's private text onto an agent for
everyone, nor detach somebody's personal instructions. Relay the error's pointer:
`manage-ai-preferences` is the tool for those.

### Two-stage writes — where `confirmed: true` is required

- **Every prompt write on a CONVERSATIONAL agent, and every flow-section write on any agent,
  needs `confirmed: true`.** Without it the tool returns a **diff of the composed prompt**
  (per section: added / changed / removed, with before and after) and writes nothing. These
  agents are mid-conversation with real people and an edit lands on their very next message.
  Show the operator that diff, get an explicit yes, then re-call with `confirmed: true`.
- **Task agents write in one stage** — no human is waiting; the effect shows up in the next
  extraction run. `enable` / `disable` are one-stage too (immediately reversible), and every
  read action never needs confirmation.
- **`set-tags` is one-stage on every agent type it accepts**, conversational included — the
  single write here that never gates on `confirmed`. A tag is a label: it alters nothing the
  agent says, so a composed-prompt diff would show no difference. Params `agent_id` + `tags`
  (full list of names, replaces the previous set, creates unknown names, `[]` clears).
  Automation agents are refused with a pointer to `manage-automation-agent`'s `tags` param.

Permissions: reads need `view` on the Agent, writes `update`; a **flow-section** write
additionally needs `settings.manage`, because a flow section is tenant settings rather than a
property of the agent it is edited from.

### The call-notes classifiers' two settings-backed blocks (`callback-timing`, `task-routing`)

`call-action-classifier` — the "Recommended Follow-ups" block `manage-activity` returns after a
logged call (`→ call-summary`) — and `inbound-email-classifier`, which applies the same policy to
inbound mail, each declare exactly two blocks. They are the first blocks whose **text is not agent
config at all**: it renders from `manage-settings`, group `ai_takeover`.

| Block | Renders | Fields on `ai_takeover` |
|---|---|---|
| `callback-timing` — **not deselectable** | `## Rückruf-Zeiten` — the `due_at` rule for a `create_task` of type `call` | `callback_same_day_cutoff_hour` (int, 0–23, default 16) + `callback_retry_after_hours` (int, 1–12, default 3) |
| `task-routing` — removable | `## Aufgaben-Zuständigkeiten` — which topic goes to which internal function when the note names nobody | `task_routing_instructions` (string \| null, ≤ 2000 chars) |

**There is no free-text instruction field on `ai_takeover` any more.** Every field in the group
is a switch or a scoped rule like the two above; `instruction_snippet` is gone and an `update`
naming it is rejected as an unknown field. The company-wide instruction for KI-Nachbearbeitung
is now an ordinary **Baustein on the `activity-takeover` agent** (`0-442` + `manage-agent-prompt`),
and a per-operator one is a **personal instruction** (`manage-ai-preferences`).

- **"Bei uns wird anders zurückgerufen" / "Stundennachweise gehen nicht ins Backoffice" is a
  `manage-settings` update — not `set-instructions`, not a Baustein, and not a personal
  instruction.** Those three layers are *additive* and are told outright
  that they may not override what stands above them, so an operator writing callback hours or
  responsibilities into them changes nothing. These two blocks **are** the rule the classifier
  follows; only the fields above move it.
- **`callback-timing` cannot be switched off**, only re-numbered — the base prompt points at the
  "## Rückruf-Zeiten" section by name for `due_at`. Set `callback_same_day_cutoff_hour: 11` and
  every miss from 11:00 on becomes a next-workday callback instead of a same-day retry.
- **An empty `task_routing_instructions` is a supported choice, not a gap.** The block then
  renders nothing and the classifier routes on the bare function labels in the internal-user
  list — the same outcome as leaving `task-routing` out of an explicit `set-blocks` list. Its
  seeded default ("Stundennachweise, Abrechnung und Vertragsunterlagen gehören ins Backoffice;
  Bewerber und Onboarding zum Recruiting.") reproduces what used to be hardcoded, so a tenant
  that never touches it sees no change.
- **`ai_takeover` is not `confirmed`-gated** — only `candidate_flow_prompts` is. But this is the
  live prompt of a classifier that runs on every call an operator logs, so `get` the group, show
  the operator the current and intended values, and only then `update`. The tool renders no diff
  of its own here.
- **Known preview gap — api issue #4380.** `manage-agent-prompt` `get` derives the declared set
  from the *stored* selection, so on a task agent that never configured one — the default after
  `agents:sync` — both sections are **missing from the preview even though the real run renders
  them**. The Agent Studio's block cards inherit the same gap. Until it is fixed, read the truth
  from `manage-settings(action: "get", group: "ai_takeover")`, not from the composed prompt, and
  do not tell an operator the blocks are off because the preview does not list them.

### Renaming and tagging an agent — `manage-model` on `0-400`

An agent is **update-manageable** over the generic model tools, through an allowlist small
enough to state in full. Reach for it when the operator only wants to rename or re-label an
agent — nothing here touches what the agent says, so no dedicated tool is needed.

- **Writable — the whole list:** `name` (the internal identifier operators sort and search
  by), `display_name` (the human-facing bot name a visitor is addressed by), `tags`.
- **`create` is refused outright.** A generically created agent would have no `type` and no
  `agent_flow_key` — a broken row. Conversational agents come from tenant migrations, task
  agents from the code registry, automation agents from `manage-automation-agent` `create`.
- **Refused with a pointer to the owning tool** (the error names it, so relay it rather than
  retrying): `system_prompt`, `instructions`, `blocks`, `instruction_block_ids`,
  `capabilities`, `enabled_tools`, `output_schema`, `is_active`, `greeting_message`,
  `initial_message` → `manage-agent-prompt` or `manage-automation-agent` per agent type.
- **Refused as immutable:** `type`, `agent_flow_key`, `agent_key`, `is_system`, `owner_id` —
  they define what the agent *is*, not how it behaves. Create the agent you need instead.
- **Silently dropped** (reported back as an ignored field, not an error): every other column,
  e.g. `language`, `model_name`, `quick_replies`. Check the ignored-field report before
  telling the operator a change landed.

Two-stage like every generic write: `confirmed: false` preview → show the operator →
`confirmed: true`.

## The Bewerber-WhatsApp-Agent's tenant-owned prompt sections (`candidate_flow_prompts`)

The candidate-facing WhatsApp agent (Bewerber-Flow) is a conversational agent — not an
automation agent, so `manage-automation-agent` cannot see or edit it. What a tenant *can*
change over MCP are **eight** sections of its prompt. Two tools reach the same stored values:

- `manage-settings`, group `candidate_flow_prompts` (`action: "get"` / `"describe"` /
  `"update"`) — the field-level path. Reading is free; **an `update` now requires
  `confirmed: true`**. `describe` returns the group's field docs — including the
  `candidate_requirements` ↔ `soft_requirements` pairing warning below — which are **not** in
  the tool description; call it (or rely on this section) before touching a field.
- `manage-agent-prompt` `list-flow-sections` / `set-flow-section` / `reset-flow-section` on
  the agent — the same write behind a **composed-prompt diff** and a `shared_with` list of
  the other agents the change moves. Prefer this one when the operator asks about a specific
  agent, because it shows the effect in that agent's assembled prompt.

| Field | Overrides |
|---|---|
| `agent_persona` | WHO the agent is: the role it presents as, the company it writes for, the register (du/Sie). This is the **very first sentence** of the composed prompt, so a wrong company name here is the first thing every Bewerber reads. Was hardcoded before — check it on a new tenant |
| `company_model` | Engagement model + employer-brand story (AÜG vs. Vermittlung, typical placement length, why work here) |
| `candidate_requirements` | The hard deal-breakers (K.O.-Kriterien) and how the agent ends the conversation once one applies. Most carry **numeric thresholds** (commute km/min, weekends per month, monthly hours), but not all — criterion 7 is qualitative (see below) |
| `qualification_profile` | What sales needs from a candidate, in which order, core vs. secondary fields, plus the sector vocabulary used to ask |
| `sector_focus` | Which sectors/roles the agency places — opens the conversation, lets it decline out-of-scope callers |
| `soft_requirements` | **The same criteria as `candidate_requirements`** — thresholds *and* the qualitative ones — phrased softly for conversation types that must not end on them (a human decides instead) |
| `sector_vocabulary` | Example lists (nursing software, devices, specialties) offered as quick replies |
| `hard_rules` | What the agent may never promise or reveal in chat: pay, bonuses, Firmenwagen, Fahrtkosten, Unterkunft, Vertragskonditionen — plus that internal thresholds and the internal K.O. classification stay internal. Commercial policy, not conversation mechanics. Changing a threshold in `candidate_requirements` usually means checking this field too, since it is what forbids naming that number to the candidate |

Four rules the operator must hear before you write anything:

- **The write is two-stage.** An `update` without `confirmed: true` returns a preview of what
  each field currently holds and **writes nothing** — that is the tool working as intended,
  not a failure. Show the preview, get an explicit yes, then re-call with `confirmed: true`.
  `get` never needs it. `candidate_flow_prompts` is the only settings group gated this way.

- **`null` means "use alluvo's shipped default"; `""` means "an empty section".** They are
  different. A tenant that leaves a field `null` inherits every future improvement to the
  default; setting text freezes them on that text. **To reset, set the field back to `null`
  — never to an empty string.**
- **`candidate_requirements` and `soft_requirements` carry the same rules twice.** Not just the
  numbers: the qualitative criteria (excluded Einsatzumgebungen, see below) sit in both too,
  hard in one and soft in the other. Change a threshold (e.g. max commute 40 → 60 km) or a
  qualitative rule in one and the agent contradicts itself between the hard and the soft
  conversation type. Always update both in the same step, and say so in the preview.
- **This is the live prompt of an agent talking to real Bewerber right now.** An update applies
  on the very next message of an ongoing conversation. `get` first, read what is there, and
  never replace it blind — a mid-conversation contradiction is a real applicant experience.

**Two things about the current shipped default an operator will ask about:**

- **Excluded Einsatzumgebungen are a K.O. criterion (no. 7), and it is not numeric.** It bites
  only when the candidate rules out *everything* the agency überlässt into — Pflege: Altenheim
  **and** Krankenhaus; Pädagogik: Kita — or wants work outside direct care entirely (pure
  office, consulting, training). A **single** exclusion is explicitly *not* a K.O.: an
  Altenpflegerin who only rules out hospitals stays placeable, and the restriction is simply
  recorded in the profile (`other_profile_notes`). The soft counterpart in `soft_requirements`
  asks the same question once, openly, and records the answer without any hint of unsuitability.
- **Leadership/management roles no longer have an exemption.** PDL, stellv. PDL, WBL,
  Einrichtungs-/Heimleitung and non-bedside Fachrollen (QM, Hygiene) run through the same gates
  as everyone else — the 3-Schicht K.O. included. If an operator remembers the old carve-out
  (no shift/weekend K.O., looser commute, `flag_hot_lead` instead of ending), tell them it was
  removed on purpose: it came from a Personalvermittlung motive that does not convert for this
  agency and was letting candidates without shift readiness through qualification. Its verbatim
  wording lives on as a **deactivated Baustein** — see below.

**The "Ausnahme für Leitungs-/Führungsrollen (archiviert)" Baustein.** Every tenant has a
`0-442` InstructionBlock by that name with `is_active: false`, attached to no agent
(`record_source: system`). It is an archive of the three removed passages (K.O. criteria,
qualification checklist, engagement model), kept so the wording is not lost. It shows up in the
Agent Studio and in any Baustein list — that is expected, nothing is broken. If an operator
wants the old behaviour back, be precise about what re-activating it does and does not do:
a Baustein is **additive and renders below** the flow's own prompt and the precedence block, so
it cannot override a rule the flow states outright. The current default says the shift K.O.
applies to leadership roles too, so attaching this block alone just leaves two contradicting
instructions and the flow wins. Genuinely restoring the exemption means editing
`candidate_requirements` **and** `qualification_profile` in this settings group as well.

Everything else in the flow (question order, tone mirroring, calendar choreography) is fixed
in code — do not promise changes beyond these eight sections. Note that resetting differs by
tool: on `manage-settings` set the field back to `null`, on `manage-agent-prompt` call
`reset-flow-section` (which also **refuses** an empty `text` on `set-flow-section`, rather
than silently blanking the section). Related knob in the same tool:
`company_city` / `company_state` on the `general` group feed the **Standort der Agentur**
block rendered into every agent prompt (voice, chat, and — once any system block is selected —
automation agents); while both are empty, agents are told to never claim or guess a location.

## Data protection & AÜG note

Automation agents that read personal or health data (e.g. sick-day counts, absence history,
salary) must be scoped to **expose only the minimum needed to make the report actionable** —
aggregates and qualifying names, never raw record dumps or unrelated fields. Say this
explicitly in the agent's `instructions` (see the "Spendit Qualifier" example below: "nenne
ausschließlich die vom Tool gelieferten Namen, Personalnummern und
Krankheitstage-Summen — keine weiteren Gesundheitsdaten oder Rohdaten"). The report
**recipient** must be a legitimate internal address with a business need to know (HR,
Disposition lead) — never a broad distribution list for anything touching health/absence
data. This mirrors the AÜG/ArbZG posture the rest of the plugin holds: automating a report
must never loosen who gets to see sensitive employee data.

## Worked example — "Spendit Qualifier" (shipped reference)

A monthly agent that flags employees with fewer than 2 sick days in the previous month and
emails a report:

- **Agent**: `capabilities: {"query_employee_sick_days": "execute"}`; `output_schema`:
  `body` (string, required — the ready-to-send German report text) and `qualifying_count`
  (integer, required). Instructions (German): check approved sick days for the previous
  calendar month, list qualifying employees (name, personnel number, sick-day count) as a
  short professional German report, name only what the tool returned — no other health data.
- **Workflow**: `trigger_event: "scheduled"`, `schedule_preset: "monthly_start"`.
  1. `run_agent` → `{ agent_id: <id>, output_key: "agent" }`
  2. `transactional_mail` → `{ recipient: "<hr-address>", subject: "Spendit-Qualifikation
     {{run.previous_month_name}} {{run.year}}", body: "{{agent.body}}" }`

## Output

- Automation agent: id + name + `capabilities` (key → mode) + `output_schema` summary, plus its `blocks`
  selection and attached Bausteine (`instruction_block_ids`, in render order) when set
- Conversational or task agent: id + name + type + which prompt layer changed, and — for a
  conversational one — the composed-prompt diff the operator confirmed, plus the other agents
  a flow section moved with (`shared_with`)
- Test-run result: rendered `body` (or other structured fields) shown to the operator
- Workflow: id + trigger (event + `trigger_config` where one applies) + schedule (preset/cron +
  timezone) + the ordered action list or step tree, incl. every wait and its duration
- Any `goal_conditions` / `unenroll_on_mismatch` set, stated as the exit rule in plain words
- Enabled/disabled status, and (once run) a pointer to `list-runs` for history and
  `list-enrollments` for what individual records are currently doing
- For a **deployment** instead of a workflow: deployment id, agent → inbox (+ channel or "all
  channels"), owner, the step whitelist that will *actually* apply (the default set unless the
  deployment's capability map was set in the Studio — not the `enabled_steps` you passed, see
  #4027), caps, active flag — and an explicit note that nothing fires until the tenant's
  inbox-agent feature gate is on

## Related skills
- `→ head-of-disposition` / `→ head-of-sales` — good sources for recurring reporting ideas
  worth turning into an automation agent.
- `→ triage-data-quality` — a natural companion job-to-be-done for a scheduled data-quality
  digest agent.
- `→ define-icp` — the ICP records the `icp` system block reads; an agent with `icp` selected
  but no ICP defined renders nothing for that block.
- `→ clean-inbox` — the manual triage routine for the inbox a deployment runs on; go there
  when the operator wants to work tickets themselves rather than automate them.
- `→ record-absence` — the AbsencePeriod approve/reject the Slack `record_actions` buttons
  currently carry; go there for the in-app path (and whenever a rejection needs a reason).
- `→ approve-stundenfreigabe` — what a Tagesabschluss (`0-422`) actually is, what the row
  records, and the § 4 ArbZG rules a workflow on it must not undercut.
- `→ build-dienstplan` — what a post-approval Dienstplan change (`0-433`) actually is: which
  Periode-Status records one, what the employee already receives without any workflow, and how
  an employee's change is released or rejected.
