---
name: define-icp
description: Define, maintain, or retrieve Ideal Customer Profiles (ICP) for individual segments. Use this skill when the operator asks "wer ist unser Wunschkunde", "ICP für Krankenhäuser definieren", "welche Unternehmen passen zu uns", "define ideal customer profile", "qualify a lead against our ICP", or wants to document target decision-maker personas per segment.
---

# ICP Definition (Ideal Customer Profile)

## Purpose
Structure a target customer profile per segment (e.g. hospitals, Kitas, care homes,
industry), store it persistently, and make it retrievable for acquisition and
qualification decisions.

> Read-only until the save step. The save (`manage-model` on IdealCustomerProfile
> `0-270`) only happens after preview and confirmation.

## Prerequisites
Uses exclusively alluvo MCP tools (`mcp__alluvo__*`). No tokens, no shell.

## Steps

### 1. Clarify segment and goal
Ask the operator:
- **Segment** — e.g. "Hospitals > 200 beds, NRW"
- **Goal** — create a new profile, update an existing one, or just retrieve it?

### 2. Search for an existing ICP
ICPs are first-class records: **IdealCustomerProfile, model type `0-270`**. Call
`query-model` / `search-model` with `model_type: "0-270"` and the segment term.
Inspect the available fields with `get-model-schema` (contexts `list` / `create` /
`update`) before writing — never guess the schema.

### 3. Build the ICP profile card
Ask interactively for missing fields, or — when updating — show the current values.
Structure per segment:

| Field | Example |
|------|---------|
| **Segment** | Inpatient care, NRW |
| **Minimum size** | ≥ 80 beds / ≥ 15 staff |
| **Target positions** | Pflegefachkraft IK, OTA, Sterilisationsassistenz |
| **Decision-maker personas** | Pflegedienstleitung (PDL), HR manager |
| **Qualification criteria** | Own Rahmenvertrag (or AÜV-ready), open positions in last quarter |
| **Exclusion criteria** | Pure temp-agency brokerage, Kettenverbot constellations |
| **Conversation opener** | Equal-Pay proof, quality certificate, regional reference |
| **Typical objections** | Internal pool, Stammverleih, collective agreement binding |

### 4. Resolve sector and company segments before previewing
A create is **rejected** without both of these, so resolve them while the operator is
still in the conversation — never invent an id:
- **`sector_id`** — one Sector (`0-70`), required on create. Look it up with
  `query-model` `model_type: "0-70"`.
- **`company_segments`** — a **flat array of CompanySegment (`0-198`) ids**, required on
  create with **at least one** entry. List the tenant's segments with `query-model`
  `model_type: "0-198"` (they carry `label` / `key`) and map the operator's wording onto
  them. If nothing matches, ask rather than guessing — an id that doesn't exist fails
  the whole write.

Show the resolved sector and segments by **name** in the preview, not as bare ids.

### 5. Show preview
Present the complete profile card as plain text. Ask explicitly:
"Shall I save this profile now?"

### 6. Save (after confirmation)
- **New:** `manage-model` with `model_type: "0-270"` (`confirmed: false` → preview →
  `confirmed: true`), mapping the profile card onto the fields exposed by the
  `create` schema — `name` (unique per tenant), `sector_id` and `company_segments` are
  required; `job_titles`, `industry`, `location`, `company_size`, `revenue` and
  `age_range` take arrays, `interests`, `pain_points` and `other` free text. Fields not
  in the schema are silently dropped — put anything the schema doesn't cover into
  **`other`** (the catch-all free-text field) so it isn't lost.
- **Update:** retrieve the existing ICP by ID (`get-model` `0-270`), display the
  diff, then `manage-model` update (preview → confirm). `company_segments` is optional
  on update, but when sent it is a **full replace** — pass the complete list of segment
  ids to keep, omit the key to leave the segments untouched, `[]` to clear them. Sending
  only the one segment being added silently drops the rest.

## Output
- Profile card of the saved (or reviewed) ICP
- ID of the IdealCustomerProfile record (`0-270`)
- 1–2 suggested next steps (e.g. "→ `prospect-companies` for segment Pflege NRW")

## Related skills
- `→ prospect-companies` — qualify leads against this profile.
- `→ profilvertrieb` — the ICP feeds value framing for the pitch (Step 5 there).
- `→ enroll-outreach` — enroll matching companies in sequences.
- `→ log-company-signal` — prioritize signals by ICP relevance.
