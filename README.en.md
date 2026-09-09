# alluvo – AI plugin for staffing agencies (Claude, Codex)

🇩🇪 **Deutsche Version: [README.md](README.md)**

**alluvo** is the AI plugin for German staffing agencies (Personaldienstleister, Zeitarbeit). It turns Claude and Codex into an assistant that handles dispatching, recruiting, sales, contracts, shift plans and timesheet approval by natural language: directly in your alluvo data, with a preview before every write, and with the AÜG and ArbZG checks the industry requires.

## Who it is for

- **Dispatchers** – who is on the bench, who fits which client request, shift plans, sick notes, timesheet approval.
- **Recruiters and HR** – onboarding new employees, the digital personnel questionnaire, master data, invitations to the employee app.
- **Sales and BDRs** – profile marketing, target companies nearby, outreach sequences, call preparation and follow-up.
- **Management and team leads** – daily briefing, dispatching and sales overviews, task delegation.

## What you can say

Workflows activate on natural phrases, German or English:

| You say … | alluvo does … |
|---|---|
| "Who is on the bench right now?" | lists employees without an assignment, ranked by urgency, with home town and qualification |
| "Find assignments for the bench" | matches available employees to clients with a framework contract and drafts assignment contracts |
| "Sell the candidate Max Mustermann" | finds matching companies nearby, qualifies them and starts the outreach sequence |
| "New staffing request from Klinikum Musterstadt" | captures the request completely and proposes candidates |
| "Create the October shift plan" | plans the shifts with ArbZG checks and publishes them |
| "Sick note for Ms Beispiel from Monday" | books the absence and files the certificate in the personnel record |
| "Review the submitted hours" | shows submitted hours, deviations and open client approvals |
| "Create a framework contract for Pflegedienst GmbH" | creates the contract, walks it through its stages and sends the §11 AÜG notification |
| "What's on today?" | daily briefing from meetings, tasks, outreach replies and pipeline |
| "Clean up the inbox" | triages the team inbox, closes with evidence, creates follow-up tasks |

## All workflows

| Area | Workflows |
|---|---|
| Dispatching | `bench-check`, `match-bench-to-clients`, `intake-personalbedarf`, `build-dienstplan`, `record-absence`, `approve-stundenfreigabe`, `head-of-disposition` |
| Contracts | `manage-contract-lifecycle` |
| Recruiting and HR | `onboard-new-employee`, `manage-meta-ads` |
| Sales | `profilvertrieb`, `prospect-companies`, `enroll-outreach`, `define-icp`, `account-research`, `call-prep`, `call-summary`, `log-company-signal`, `head-of-sales` |
| Service and data quality | `clean-inbox`, `triage-data-quality`, `merge-duplicate-companies`, `enrich-contacts-from-activities` |
| Automation and overview | `build-automation-agent`, `daily-briefing`, `using-alluvo-operator` |
| Free (no account) | `stellenanzeige` |

Each workflow's trigger phrases are in the [catalogue](plugins/alluvo/README.md). Any workflow can also be started explicitly, for example `/alluvo:bench-check`.

## Installation

### Claude Code

1. Add the marketplace (once per machine):
   ```
   /plugin marketplace add alluvoai/ki-plugin-personaldienstleister
   ```
   Without GitHub, exactly the same — alluvo hosts the same marketplace itself:
   `/plugin marketplace add https://api.alluvo.ai/plugins/marketplace.json`
2. Install the plugin:
   ```
   /plugin install alluvo@alluvoai
   ```
3. Connect the assistant. The plugin brings the alluvo MCP server with it; on first use Claude Code asks you to sign in. You can also start it yourself:
   ```
   /mcp
   ```
   Choose **alluvo**, sign in with your alluvo credentials in the browser, and pick your organisation.
4. Try it: "Who is on the bench right now?"

**Updating:** Auto-update is **off by default** for third-party marketplaces — Claude Code won't download a new plugin version on its own otherwise. Turn it on once under **`/plugin` → Marketplaces → `alluvoai` → "Enable auto-update"**; after that, Claude Code checks after every start and asks you to `/reload-plugins` when a new version is available. Without it, update manually: `/plugin marketplace update alluvoai`, then `/plugin update alluvo@alluvoai`. Workflow guidance itself is served live by the assistant and needs no plugin update either way.

### Claude Cowork

**Recommended: connect the assistant organisation-wide.** An Owner of your Claude organisation adds a custom connector under **Organisation settings → Connectors** with the address `https://api.alluvo.ai/mcp`. Members sign in once; every workflow then starts without a plugin at all, because the alluvo server serves them.

**The plugin itself reaches Cowork only through GitHub sync of your own copy.** This repository is a GitHub template:

1. Choose **"Use this template"** and create a private copy in the customer's GitHub organisation.
2. Install the **Claude GitHub App** in that organisation and grant it access to the copy.
3. In Cowork, point **Sync from GitHub** at that copy.
4. On first use the assistant asks for the alluvo sign-in (OAuth) and the organisation.

### Codex

1. Add the marketplace:
   ```
   codex plugin marketplace add alluvoai/ki-plugin-personaldienstleister
   ```
2. Install the plugin:
   ```
   codex plugin add alluvo@alluvoai
   ```
3. Sign in to the bundled assistant:
   ```
   codex mcp login alluvo
   ```
   If the bundled server is not picked up, add it once by hand and sign in afterwards: `codex mcp add alluvo --url https://api.alluvo.ai/mcp`

Updating: `codex plugin marketplace upgrade`, then re-add the plugin.

### Without the plugin

Every MCP client can connect to the alluvo assistant directly; the plugin only adds the guided workflows on top. Claude Desktop, claude.ai and other clients use the connector URL `https://api.alluvo.ai/mcp`. Details, including the personal-token path: [Connect the Assistant](https://docs.alluvo.ai/en/alluvo-mcp/connect).

## Security and compliance

- **Your data stays with you.** The plugin contains no data and no instructions, only the trigger phrases. Everything else is served by the alluvo server at runtime, after sign-in, within your permissions and only for your organisation.
- **A preview before every write.** No contract, shift or contact is created or changed until you have confirmed the preview.
- **AÜG and ArbZG built in.** Shift plans are checked against maximum working time, rest periods and Sunday work; maximum assignment duration, equal pay and the §11 notification are part of the contract workflow.
- **Plan boundaries are visible.** A workflow outside your alluvo plan answers `MODULE_LOCKED`, names the plan it needs and links to the trial.

## Troubleshooting

| Symptom | What to do |
|---|---|
| `alluvo … Needs authentication` in `/mcp` | Sign in via `/mcp` → alluvo. Tokens expire; signing in again fixes it. |
| A workflow does not activate | Use a trigger phrase from the catalogue, or start the workflow explicitly: `/alluvo:bench-check`. |
| `MODULE_LOCKED` | The workflow belongs to a module your organisation has not enabled. The message names the plan and links to the trial. |

## About alluvo

alluvo is the software for staffing agencies: employees, clients, contracts, shift planning, time tracking, billing and sales in one system, with an AI assistant and an employee app. More at [alluvo.de](https://alluvo.de), documentation at [docs.alluvo.ai](https://docs.alluvo.ai/en).

Support: your alluvo contact.
