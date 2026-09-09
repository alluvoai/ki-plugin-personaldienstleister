# alluvo Operator Skills

Guided workflows (**English-first, German industry trigger terms retained**) for
alluvo staffing-agency operators (Disponenten, Recruiter, BDRs). This plugin is a thin workflow layer on top of
the **alluvo MCP server** — it turns ~90 raw MCP tools into the handful of
*jobs-to-be-done* an operator runs every day.

## Prerequisites

You need an **alluvo account** (with access to your tenant/organization). The
plugin **bundles the alluvo MCP server** (`.mcp.json`) — installing the plugin
declares the server at `https://api.alluvo.ai/mcp`, and your Claude client will
prompt you to **sign in via OAuth** and pick your organization on first use. No
API tokens, shell access, or manual MCP setup required. These skills call only
`mcp__alluvo__*` tools; every action runs in your tenant, respects your
permissions, and mutating steps always preview before they write.

## Install

**Claude Cowork (org marketplace):** your org admin connects this repo under
Organization settings → Plugins → Add plugin → GitHub; the plugin then appears
for the org. On first use, authenticate the bundled **alluvo** MCP server (OAuth)
and select your organization.

**Claude Code:**
Ask your alluvo contact for the marketplace to add, then install the
**`alluvo-operator`** plugin.
On first use you'll be prompted to authenticate the bundled **`alluvo`** MCP
server via OAuth. (Already connected the alluvo MCP yourself? It still works —
the bundled declaration just makes setup one step.)

Then just describe what you want in plain language — e.g. *"Wer ist gerade
verleihfrei?"*, *"Finde Einsätze für die Bank"*, *"Nimm einen Personalbedarf
auf"* — and the matching skill activates. Not sure where to start? Just ask
*"Was kannst du?"* and the **`using-alluvo-operator`** wegweiser lists everything
and routes you to the right workflow.

## What's inside

**Start here**
- `using-alluvo-operator` — wegweiser / entry point: catalogs every workflow and routes you to the right one

**Leitung / management (overview & coordination)**
- `head-of-sales` — sales overview, weighted forecast, pipeline review, BDR coordination
- `head-of-disposition` — utilization, expiring assignments, open demand, Disponent coordination

**Disposition & placement**
- `bench-check` — who is verleihfrei now / about to be (urgency-ranked)
- `match-bench-to-clients` — match the bench to clients with a Rahmenvertrag, draft Einsatzverträge
- `onboard-new-employee` — completeness gate + nearby opportunities + prospecting tasks
- `build-dienstplan` — create/adjust shifts with ArbZG guardrails
- `record-absence` — log Krankmeldung / Urlaub / AU
- `approve-stundenfreigabe` — review and approve hour releases

**Sales & outreach (BDR)**
- `profilvertrieb` — bench → placement: find companies and actively sell employee profiles
- `prospect-companies` — find & qualify target companies for an employee (geo + ICP + signals)
- `enroll-outreach` — enroll qualified companies in outreach sequences
- `define-icp` — define Ideal Customer Profiles per segment
- `log-company-signal` — record hiring/expansion/funding signals
- `account-research` — internal dossier on a company/contact from alluvo data
- `call-prep` — prepare a meeting from CRM history
- `call-summary` — wrap up a call: log note/call + tasks + follow-up email

**My day**
- `daily-briefing` — today's meetings, due tasks, outreach replies, priorities

**Verträge & Bedarf**
- `intake-personalbedarf` — capture a client staffing requirement end-to-end
- `manage-contract-lifecycle` — Rahmenvertrag + Einsatzvertrag create → sign-off

**Daten & CRM**
- `triage-data-quality` — review & bulk-triage data-quality issues
- `merge-duplicate-companies` — find, preview, and merge duplicate companies
- `enrich-contacts-from-activities` — enrich contacts from their emails / calls / signatures (review-first)
- `clean-inbox` — triage a shared company inbox: close only with evidence, task the rest, never fabricate operational data

**Marketing & recruiting ads**
- `manage-meta-ads` — Meta (Facebook/Instagram) recruiting campaigns: campaigns, creatives, lead forms, conversion events, performance

**Automation**
- `build-automation-agent` — build/adjust a scheduled AI agent that produces a periodic report and delivers it automatically (email or task)
