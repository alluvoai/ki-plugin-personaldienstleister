---
name: prospect-companies
description: Find and prepare qualified target companies for an employee — via geo-radius, ICP segment, and market signals. Use this skill when the operator asks "wer kommt für Mitarbeiter X in Frage", "Zielfirmen finden", "Unternehmen in der Nähe von Köln suchen", "passende Firmen finden", "Leads qualifizieren", "find companies near employee", "prospect companies", "qualify leads for a candidate", or wants a shortlist of qualified targets for outreach. For the end-to-end pitch (compose/send/enroll), use profilvertrieb instead.
---

# Prospect Companies (Geo + ICP Lead Shortlist)

## Purpose
Identify matching companies within the radius of an employee's home location, qualify
them against the ICP, and hand over a prioritized lead list to the BDR.

> This skill is thin — it feeds inputs into the main acquisition flow via the MCP prompt
> `profilvertrieb-prompt`. Inputs are gathered and prepared here. For the full
> bench-to-placement job (match intelligence, email/sequence, sending), use
> `→ profilvertrieb`.
>
> Read-only except Step 6 (optional new-company creation) — that write previews first.

## Prerequisites
- Employee is verleihfrei (run `→ bench-check` first if needed).
- alluvo MCP tools (`mcp__alluvo__*`) available. No shell access, no scraping.

## Steps

### 1. Gather inputs
Clarify with the operator:
- **Which employee?** (name or ID — `0-2`)
- **Home location / postal code** (used for the radius search)
- **Radius** (default: 30 km; for Pflegekräfte often 20 km)
- **Target segment** (Krankenhaus, Kita, Altenheim, Industrie …) — load from a saved ICP
  via `query-model` / `search-model` on IdealCustomerProfile (`0-270`) if available
  (see `→ define-icp`)

### 2. Load the employee profile
Call `get-profile` with `resource: "profile"`, `model_type: "0-2"` and the employee's
`model_id`. Relevant
fields: position, qualifications, certifications, home location, language skills.

### 3. Find companies in the radius — one geo call, paged
`search-model` on Company (`0-3`) with **`lat`/`lon`/`radius_km`** (the employee's home
location from Step 2) **combined with `filter_groups`**. This now filters **every** record
inside the radius with normal pagination and `sort_by` — so you can do "all hospitals within
50 km matching the segment, sorted by lead score, page by page" in a single call. Each row is
still annotated with `distance_km`.

```
search-model model_type:"0-3"
  lat:<home_lat> lon:<home_lon> radius_km:30
  filter_groups:[{conditions:[
    {field:"lead_score",operator:"gte",value:0}
  ]}]                                # + companySegments / staleness filters (Step 4)
  sort_by:"lead_score" sort_dir:"desc"
  page:1 per_page:25
```

Narrow to the ICP with the `companySegments` / `sectors` filters rather than a free-text
location string. **Do not** search by location-name terms for radius work — that returns
name matches, not everything in the geography. (Pure geo with *no* `filter_groups` keeps the
old "nearest-N" contract; add filters the moment you want the full radius paged.)

> **`sectors` / `companySegments` are relation filters — bare name, ids, four operators.**
> Write the **bare relation name** as the field (`sectors`, *not* `sectors.id`) and pass
> **Sector (`0-70`) / CompanySegment (`0-198`) ids**, never names — resolve the names to ids
> first (`query-model`, or reuse the ids already stored on the ICP → `define-icp`):
> ```
> {field:"sectors",operator:"in",value:[<sector_id>, …]}
> {field:"companySegments",operator:"eq",value:<segment_id>}
> ```
> Only `eq` / `in` / `neq` / `not_in` match a bare relation by id. `eq`/`in` = "has **at least
> one** matching entry"; `neq`/`not_in` = "has **none**" — so a company with no sector at all
> also passes a `neq`; read it as "not tagged with X", not as "tagged with something else".
> For a text or range match on a related record's attribute use the **dotted path**
> (`{field:"sectors.name",operator:"like",value:"…"}`) — a comparison operator against the
> bare relation name **fails the call**, it is not silently skipped. `is_null` / `is_not_null`
> against the bare name work as presence checks ("has no segment at all").

For deeper attribute filtering, `query-model` on Company now also accepts `companySegments`
and `sectors` as **includes**, so you can read a company's segment/sector inline.

### 4. Qualify leads
For each found company, check (via `get-model`):
- Does the industry match the ICP?
- Are there active or past outreach activities?
- When was the last contact? (Timeline entries on the Company)
- Open tasks / next steps present?

> **Staleness / "3 Monate nichts gehört" filter — exclude on BOTH date fields.** Company
> (`0-3`) now exposes two filterable + selectable timestamps with **different** meaning:
> - `last_contacted_at` = last **outbound** contact *by us*.
> - `last_activity_at` = last **non-outbound** engagement (*them* engaging with us).
>
> A cold-call/"no contact in X months" pool must be cold on **both** — recent inbound
> interest is just as disqualifying as a recent outbound touch. Require each cutoff as
> `lt <cutoff>` **OR** `is_null` (a never-touched company is a valid cold lead):
> ```
> filter_groups:[{conditions:[
>   {field:"last_contacted_at",operator:"lt",value:"<cutoff>"},   # or is_null
>   {field:"last_activity_at", operator:"lt",value:"<cutoff>"}    # or is_null
> ]}]
> ```
> Fold these straight into the Step 3 geo call.

Companies not yet in alluvo: flag as new company leads (stub) — creation happens via
`manage-model` in the confirm step, not automatically.

> **Before greenlighting a `new` lead, check for a sibling/duplicate.** A `new` record can
> be a duplicate of one already in an `open_deal` (same name root / parent-child / shared
> address) — qualifying it would cold-pitch into a live deal. Search the name root/address
> and surface a duplicate warning; route to `→ merge-duplicate-companies` if found. (See
> `→ profilvertrieb` Step 4.)
>
> **Outreach by email needs a contact.** A qualified company with no contact has no
> addressee. Note whether each lead has a usable decision-maker contact (Contact `0-105` /
> PortalMembership `0-430` filtered by `company_id`); flag the ones that still need contact
> enrichment.
>
> **Fachliche Eignung (#980).** If an `EmployeeStaffingOpportunity` (0-126) already exists for
> this employee↔company pair, honour its top-level `specialty_fit`: **drop `conflict` leads**
> (the facility's clinical focus doesn't match the employee's specializations — e.g. an
> adult-ICU nurse vs. a dedicated children's clinic) and never qualify them for outreach. For
> the leads you do hand over, only assert suitability for a department the employee's
> specializations actually cover; otherwise keep it general. The downstream pitch must not
> claim a clinical fit the employee can't deliver. (See `→ profilvertrieb` Step 3.)

### 5. Hand off to the Profilvertrieb prompt
Pass the full context (employee ID, home location, radius, segment, qualified company
IDs) to `profilvertrieb-prompt`. That prompt takes over further outreach planning and
sequence recommendations.

### 6. Create new companies (optional, after confirmation)
If the operator provides new leads from external sources (trade fair catalogue,
referral): `manage-model` for Company — first `confirmed: false` for preview, then
`confirmed: true`. If a real market trigger is known (job posting, expansion, new
leadership), log it with the **`log-signal` record action on the company**
(`manage-record-action`, `model_type: "0-3"`, `action: "log-signal"`, preview →
confirm) using a **valid type** (`hiring`, `expansion`, `funding`, `product_launch`,
`partnership`, `leadership_change` — there is no "prospect" signal type); otherwise
record the origin as a note. See `→ log-company-signal`.

## Output
- Employee profile summary (name · ID · position · home location)
- Qualified leads: per company — name · ID · location · ICP match rationale ·
  last contact
- Recommendation: which leads can go directly into an outreach sequence (`enroll-outreach`)
- Note on new leads that still need to be created
- Next action: `→ enroll-outreach` for top matches

## Related skills
- `→ profilvertrieb` — the end-to-end job: match intelligence, qualification, email or sequence.
- `→ enroll-outreach` — enroll the qualified leads in an outreach sequence.
- `→ define-icp` — create or update the ICP this shortlist is qualified against.
- `→ merge-duplicate-companies` — when the duplicate/sibling check flags a record.
