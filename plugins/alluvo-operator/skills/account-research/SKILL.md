---
name: account-research
description: Research a company or contact from your own alluvo data — an internal dossier from master data, Timeline (Calls/Notes/Meetings), open Opportunities and contracts, as preparation for Outreach or a conversation. No web, no external enrichment. Use this skill when the operator says "research company X", "info on company Y", "what do we know about", "Kontakt nachschlagen", "recherchiere Firma X", "Infos zu Unternehmen Y", "was wissen wir über", "research [company]", "look up [contact]", "intel on", or "tell me about [company]".
---

## Purpose

Before an Outreach call, a first conversation, or any contact attempt, compile a complete internal picture of a company or contact — exclusively from data stored in alluvo. The goal is a structured dossier that lets the operator see in under two minutes: who the key contact is, what has been discussed so far, what open opportunities exist, and what makes sense as a next step.

> **READ-ONLY.** This skill writes no data back. No web, no scraping, no external enrichment. Exclusively `mcp__alluvo__*` tools.

---

## Prerequisites

- Name or ID of the target company (Company, type `0-3`) **or** a contact (Contact, type `0-105`).
- alluvo MCP server is connected and the operator has read access to the relevant records.
- No further prior knowledge required — the skill resolves ambiguities via search.

---

## Steps

### 1. Resolve the target record

Search with `mcp__alluvo__search-model` for the name provided by the operator.

- For **companies**: `model_type: "0-3"` (Company)
- For **contacts**: `model_type: "0-105"` (Contact)
- If multiple results are returned, show the operator a short selection list (name + city + industry if available) and ask for confirmation before proceeding.
- Do not make assumptions about schema fields — discover available fields from the record itself.

### 2. Fetch master data

Call `mcp__alluvo__get-model` for the resolved record.

**For a company (0-3):**
- Core data: name, website, industry/sector, size, address/location.
- Linked contacts (key people): Contacts have **no `company_id` filter** (the link is an
  association). Use `mcp__alluvo__query-model` on **PortalMembership (`0-430`)** with
  filter `company_id`, including the linked contact — or `mcp__alluvo__get-model-graph`
  on the company to walk the association. `0-430` is one row per (company, contact) and
  **is** the Ansprechpartner-Verknüpfung itself, so it lists every linked contact — with or
  without portal login. (`CompanyContactPerson` / `0-361` no longer exists; calls against it
  fail.) Request `archived_at` here too and keep archived rows out of "who are the key people":
  the customer archives a contact when that person is gone, and unlike their own Kontakte list
  your query still returns them.
- Associated departments (`0-107`) if present. An Abteilung the client has **archived** is
  still returned and `archived_at` is not a default display column, so request it
  (`fields: ["name", "code", "archived_at"]`) and mark the archived ones as retired rather
  than listing them as active stations.

**For a contact (0-105):**
- Core data: name, position, email, phone, linked company.
- Then fetch the linked company's master data (as above) to add business context.

### 3. Activity history (Timeline)

Call `mcp__alluvo__get-timeline` for the resolved model.

**A company timeline does not roll up its contacts.** An activity appears on a company's
timeline only when it is associated with that company itself — a call, note or email logged
solely on a Contact never surfaces there. When researching a **company**, therefore also call
`get-timeline` on each key contact (`subject_type: "0-105"`) and merge the entries, marking
which subject each came from. This matters most for Träger / multi-site structures, where the
entire relationship runs through one shared contact person and the company timeline can come
back empty despite active engagement.

Timeline bodies are **cleaned previews**: HTML is stripped, email entries additionally lose
quoted threads and signatures, and the text is capped at ~200 characters. Anything cut is
marked "… [truncated — N more characters. Fetch the full record with `get-model`.]". When an
entry actually matters for the dossier, fetch it with `get-model` using the entry's
`record_id` — never summarise from a truncated preview.

- Show the **last 10 entries** in reverse chronological order (newest first).
- Relevant types: Calls, Notes, Meetings, Emails.
- Extract per entry: date, type, author, key takeaway (max. 1–2 sentences).
- Note when **last contact** occurred and who initiated it.

**A timeline is not a change log.** `get-timeline` returns logged activities only — it never
shows a plain attribute change (an edit form, a board drag, a bulk edit, an import). When the
dossier hinges on *who set a field and when* — the owner, the status, a lifecycle stage —
call `mcp__alluvo__get-field-history` with `model_type` + `record_id` (optionally `field` to
scope to one attribute, `limit` 1–50, default 20 events, newest first). It reports old → new,
the timestamp, and the actor: a named user, a machine source labelled `(system)` (import, mcp,
api, agent, …), or `⚠️ UNATTRIBUTED` — no user and no recognised source. Report an
unattributed write as exactly that: an unverified bulk write, not a decision someone made.
Read-only, same `view` permission as `get-model`; no events simply means nothing changed or
the model isn't audited.

### 4. Check open Opportunities

Search with `mcp__alluvo__query-model` for open Personalbedarfe and placement opportunities:

- **EmployeeStaffingOpportunity** (`0-126`): filter on `company_id` of the target company. Relevant fields: score, status, `forecasted_revenue`, linked position/role, `recommended_contact_id`.
- **ContactStaffingOpportunity** (`0-403`): filter on `contact_id` of the target contact (for contact research). Relevant fields: score, status, stage.

List only open/active records; skip closed ones.

### 5. Check contracts

Search with `mcp__alluvo__query-model` for existing or running contracts:

- **FrameworkContract** (`0-30`): filter on `company_id`. Fields: status, stage, period, Rahmenkonditionen (where available).
- **AssignmentContract** (`0-31`): filter on `company_id`. Fields: status, stage, assigned employee, deployment period.

Distinguish between active, running, and expired contracts.

**Trace a Rahmenvertrag up to its master agreement.** Request `framework_agreement_group_id`
explicitly in `fields` — it is `hiddenByDefault`, so it is absent otherwise. A value means
this house's Rahmenvertrag was spawned from a group-level **Rahmenvereinbarung**
(FrameworkAgreementGroup `0-423`, read-only): `get-model` it for `name`, validity window and
`framework_contracts_count`, or `search-model` `0-30` filtered on that
`framework_agreement_group_id` to list every sibling house on the same document. That reframes
the dossier — you are not talking to one client but to one house of a Träger. `is_null` means a
standalone contract with no master agreement.

### 6. Synthesise the dossier

Bring all collected information together into a structured dossier (see **Output** below). Keep it concise — an operator should be able to skim it in under two minutes.

---

## Output

The dossier contains the following sections:

**Quick Take**
One sentence: who is this, why are they relevant, what is the urgent next step?

**Company profile**
Name, industry, location, size (if known), website. For contact research: brief profile of the contact + linked company.

**Key contacts**
List of key people with name, position, and last contact date. If an EmployeeStaffingOpportunity contains a `recommended_contact_id`, highlight that contact.

**Activity history (recent contacts)**
Date | Type | Author | Key takeaway — maximum 5–8 entries. Gaps (e.g. no contact for >90 days) must be explicitly named.

**Open opportunities**
Tabular overview: Opportunity type | Score | Stage | Forecasted Revenue | Next action (if recorded).

**Contracts**
Overview of active and running contracts: Type | Status | Stage | Period.

**Recommended next step**
A concrete recommendation based on the data — e.g. "No contact for 6 months, open Opportunity with score 82 — prioritise a call" or "Active Rahmenvertrag, no running assignment — ask about Personalbedarf."

---

## Related skills

After completing the research, these skills may be useful:

- `→ call-prep` — call preparation for the next conversation based on this dossier.
- `→ enroll-outreach` — enrol the contact in an Outreach sequence if no active dialogue is running.
- `→ profilvertrieb` — market employee profiles to this company if a matching Opportunity exists.
- `→ log-company-signal` — log a new signal (e.g. job posting, conversation note) against the company.
