---
name: call-prep
description: Prepare for a meeting or call — account snapshot, conversation history (Calls/Meetings/Notes via Timeline), open contracts/Opportunities, suggested agenda, and discovery questions, from your own alluvo data. Use this skill when the operator says "Termin vorbereiten", "Gespräch vorbereiten", "bereite den Call mit X vor", "Meeting-Vorbereitung", "prep for my call", "call prep", or "prepare for the meeting with".
---

# Call-Prep — Pre-Call Briefing

## Purpose

A complete pre-call briefing from the operator's alluvo data:
who is the counterpart, what happened last time, what is open, what agenda fits,
and which discovery questions will hit the mark.

> **READ-ONLY.** No web. No external APIs. Exclusively `mcp__alluvo__*` tools.
> This skill writes nothing to alluvo.

---

## Prerequisites

- Name or ID of the **company** and/or the **contact person**.
- Purpose of the meeting (first call, follow-up, renewal conversation, …).
- alluvo MCP tools (`mcp__alluvo__*`) connected and authorised.

If the company or contact is unclear, ask briefly before starting Step 1.

---

## Steps

### 1. Account snapshot — company (0-3)

Load the company record with `get-model` (model_type `0-3`).

Relevant fields:
- **Segment / industry** (e.g. Krankenhaus, Kita, industry)
- **Lead status** (Prospect, Kunde, Inaktiv)
- **Location(s)** — city/postcode for a regional conversation opener
- **Responsible Disponent / BDR** — who had the most recent contact?
- **Company-level notes** — special arrangements, agreements

If the ID is unknown: use `search-model` (model_type `0-3`) with the company name,
take the first result, and briefly confirm the match.

### 2. Contact person(s) (0-105)

Load the relevant contacts with `get-model` (model_type `0-105`).

Relevant fields:
- **Role / function** (Personalleiter, PDL, Einkauf, …)
- **Formality** (`address_formality`: formal = Sie, informal = Du) — the contact's default.
  Each operator can pin their own form on top of it, and that override wins for them, so
  report the field for what it is and don't correct a colleague's register from it
  (→ `enrich-contacts-from-activities` for `set-formality-override`).
- **Preferred contact language** (`preferred_language`)
- `recommended_contact_id` from a linked EmployeeStaffingOpportunity (0-126)
  may surface a second relevant contact — load on demand.

### 3. Conversation history — Timeline

Load **two** timelines and merge them:

1. The company's — `get-timeline` (subject_type `0-3`, subject_id = company ID).
2. Each contact person from step 2 — `get-timeline` (subject_type `0-105`, subject_id =
   contact ID).

The company timeline does **not** roll up its contacts: an activity logged solely on a Contact
never appears on the company's timeline. Skipping the contact-level call means walking into the
call blind to the last conversation — especially for Träger / multi-site customers where one
shared contact person carries the whole relationship.

Timeline bodies are cleaned, ~200-character previews (HTML stripped; emails also lose quoted
threads and signatures). A `… [truncated — N more characters …]` marker means there is more:
pull that entry in full with `get-model` on its `record_id` before you brief the operator on
what was agreed. Do not paraphrase a commitment out of a truncated preview.

Evaluate:
- **Last call / last meeting** — date, participants, key topics
- **Open items / commitments** from Notes or meeting records
- **Colleague involved** — who was last in the conversation? (for internal alignment)
- **Infer formality** — did Notes use "du" or "Sie"?
- **Sentiment** — positive, cautious, critical?

Time window: prioritise the last 90 days; include older entries only for first calls
or after a long gap.

### 4. Open contracts and opportunities

Load in parallel:

- **Rahmenverträge** (FrameworkContract 0-30) — `query-model` filtered by company:
  status (active, expired, in negotiation), period, positions/departments. Ask for
  `framework_agreement_group_id` in `fields` (it is `hiddenByDefault`): a value means the
  contract hangs off a group-level **Rahmenvereinbarung** (FrameworkAgreementGroup 0-423,
  read-only) signed with several houses at once — so terms and renewal are negotiated above
  this contact's head, and `search-model` on 0-30 filtered by that group id tells you which
  sibling houses are on it. Worth naming in the briefing.
- **Einsatzverträge** (AssignmentContract 0-31) — `query-model` filtered by company:
  running assignments, end dates within the next 60 days (renewal opportunity).
- **Personalbedarf / Opportunities** (EmployeeStaffingOpportunity 0-126) — `query-model`
  filtered by company: open requests, positions, desired start date.

If no contracts exist: note this explicitly — it is a discovery angle.

### 5. Compile the briefing

Build a structured briefing from the collected data (see Output).
Invent nothing — base everything on alluvo data. Name gaps as gaps.

---

## Output

The briefing contains the following sections:

**Account snapshot**
Company, segment, lead status, location, responsible colleague.

**Who I am meeting**
Contact(s), role, formality (Sie/Du), preferred language, last contact (date + channel).

**Context & background**
Summary of the most recent Calls/Meetings/Notes: topics, commitments, open items,
sentiment, colleagues involved.

**Open contracts and opportunities**
Active Rahmenverträge, running assignments with end date, open Personalbedarf.

**Suggested agenda** (3–5 points)
Tailored to the occasion (first call / follow-up / renewal) and the context.

**Discovery questions** (3–5 questions)
Concrete, context-specific questions — no generic sales clichés.
Examples by situation:
- "How has your demand for Pflegekräfte changed since our last conversation?"
- "Which positions are ending at the close of the quarter — are you planning renewals?"
- "What would need to change about our partnership for us to become your preferred provider?"

**Likely objections + responses**
Based on the history: 2–3 probable objections and brief counter-approaches.

**Internal note**
What the operator should record after the conversation (for `call-summary`).

---

## Related skills

Recommended skills after the conversation:

- `→ call-summary` — log the conversation record, commitments, and next steps in alluvo.
- `→ account-research` — deeper company dossier if strategic account development is planned.
- `→ manage-contract-lifecycle` — initiate a renewal or a new Rahmenvertrag.
