# MCP Recipes

Concrete `alluvo` MCP tool usage for each workflow step. Model types used here:
`Contact 0-105`, `Email 0-121`, `Note 0-200`, `Meeting 0-201`, `Call 0-202`,
`Company 0-3`, `Employee 0-2`, `Candidate 0-81`.

If a tool's exact parameter shape is uncertain, confirm it live with `get-model-schema`
(for a model's fields/filters) before relying on it. Tool param names can evolve; the
intent below is stable.

## Selecting candidates

Goal: Contacts that **have engagements** (activity) AND are **missing enrichable fields**.

### Field availability gotcha (important)
The Contact list/query context only exposes a SUBSET of columns as filterable/selectable.
**Filterable & selectable enrichment fields:** `phone`, `mobile`, `title`, `position`.
**Detail-only (readable via `get-model`, NOT filterable/selectable in query):**
`salutation`, `linkedin_url`, `xing_url`, `website_url`, `preferred_language`, `first_name`,
`last_name`, `gender`. So filter the *batch* on the listable gaps, then read the rest per-contact
with `get-model`.

Also note: there is **no `company_id` filter** on contacts (they link via associations). **Do NOT
use `company is_not_empty` as the B2B proxy** — `company` is a free-text scalar that is empty for
most contacts even when they're linked to a real Company record (it badly undercounts: ~16 vs the
true ~3,300). The correct non-candidate filter is **`contact_type in ["client_contact","business_contact"]`**.
(A minority of genuine B2B contacts have `contact_type` null — widen with `contact_type neq "candidate"`
if you want to include them, but that also pulls in untyped applicants, so prefer the explicit `in` list.)

### Working filter (this is the "has engagement + missing fields" query)
`"has engagement"` = `last_activity_at is_not_null`. Groups are OR'd, conditions within a group
AND'd — so put the engagement + B2B conditions in EVERY group and one gap per group:

```jsonc
query-model  model_type:"0-105"
  fields: ["id","full_name","email","phone","mobile","title","position","company","contact_type","last_activity_at"]
  filter_groups: [
    {"conditions":[{"field":"last_activity_at","operator":"is_not_null"},{"field":"company","operator":"is_not_empty"},{"field":"title","operator":"is_empty"},{"field":"position","operator":"is_empty"}]},
    {"conditions":[{"field":"last_activity_at","operator":"is_not_null"},{"field":"company","operator":"is_not_empty"},{"field":"mobile","operator":"is_empty"},{"field":"phone","operator":"is_empty"}]}
  ]
  sort_by:"last_activity_at"  sort_dir:"desc"  limit:15
```

Drop the `company is_not_empty` condition to widen to applicants too (much larger universe — on
BNS prod, ~7k contacts vs ~16 B2B). Prefer B2B first: applicants rarely have rich signatures.
Use `count-model` with the same `filter_groups` to size the universe before pulling rows.

Starting from an Employee/Candidate instead? Resolve `contact_id` (read the Employee `0-2` /
Candidate `0-81` record) and operate on that Contact `0-105`. The reverse also works as a
filter: `contact_id` is a filterable column on Employee `0-2` and Candidate `0-81`, so
`query-model` with `{"field":"contact_id","operator":"eq","value":<contactId>}` finds the
Employee/Candidate behind a Contact directly — no email matching needed.

## Pulling evidence

For each candidate Contact:

1. `get-timeline` with `subject_type: "0-105", subject_id: <contactId>` (the parameters this
   tool declares; `model_type`/`model_id`/`record_id` are now accepted as synonyms and fill
   them, but name the declared ones). Returns the merged feed (emails, calls,
   meetings, notes). Each entry now also carries a `record_id` ("ID: 0-121#<id> — fetch full
   record with get-model") and, for calls, an `ai_summary` — pull the full record straight from
   the timeline entry instead of re-deriving the id via a separate email search.
   **The timeline body is a cleaned preview, not the source text.** Email entries are
   HTML-stripped *and* have quoted threads, signatures and disclaimers removed, then capped at
   ~200 characters with an explicit `… [truncated — N more characters. Fetch the full record
   with `get-model`.]` marker. So the signature you are hunting for is **never** in the
   timeline entry — use the timeline only to find the right email `record_id`, then read the
   raw body via `get-model` (step 3). Never mine a signature out of a timeline preview.
2. **Signatures live in INBOUND emails only.** Outbound emails (from your own staff) and
   call/meeting logs carry no contact signature — skip them.
   - **Email→contact link:** `query-model` on Contact (`0-105`) and Company (`0-3`) now support
     `include: {emails: {...}, calls: {...}, activityNotes: {...}}` directly — you can pull a
     contact plus its linked emails/calls/notes in one call instead of a separate `from_email`
     match. The older `from_email`-matching approach below still works as a fallback (e.g. when
     you only have an email address and no contact id yet).
   - **Calls** (`0-202`) are a phone source but there are tens of thousands (mostly recruiting) — do
     NOT page them for discovery. Use them per-contact: `get-timeline subject_type "0-105"` →
     Call entries often read "Call back <name> +49…" → a `mobile`/`phone` for that contact.
   Fallback: find a contact's inbound emails by address match:
   ```
   query-model  model_type:"0-121"
     fields:["id","subject","from_email","direction","created_at"]
     filter_groups:[{"conditions":[{"field":"from_email","operator":"contains_token","value":"<contact-or-domain>"}]}]
     sort_by:"created_at" sort_dir:"desc" limit:5
   ```
   The email field is **`from_email`** (not from_address). Filter by the contact's email or its
   domain; `direction = "inbound"` are the ones with their signature.
3. `get-model  model_type:"0-121" id:<emailId>` → read **`Body Html`** (the signature block, with
   role line, phones, website, LinkedIn/Xing, address). Strip the quoted reply below the
   `Von:/From:` divider — anything after it is the prior (often your own) message + signature.
   Fetch the Email record **directly** like this — do NOT read email bodies off a Contact's
   `get-model` detail: activity relations there (emails/calls/notes/…) are compacted by default
   to a count + one-line previews (pass `full_activities: true` only if you really need the
   full list inline; the direct 0-121 fetch stays the cheaper, correct path here).
4. `get-model  model_type:"0-105" id:<contactId>` → read the **detail-only** current values
   (`salutation`, `linkedin_url`, `xing_url`, `website_url`, `preferred_language`, `first_name`,
   `gender`) so you never overwrite a populated one and can spot data bugs (e.g. salutation parked
   in `first_name`).
5. Hand the collected text to `references/extraction-patterns.md` for parsing.

## Writing changes

After approval, per contact (batch all approved fields into ONE update call):

```
manage-model
  action:      update            # confirm the exact action keyword via the tool schema
  model_type:  "0-105"
  id:          <contactId>
  data: {
    mobile:        "+49 171 5551234",
    title:         "Pflegedienstleitung",
    linkedin_url:  "https://www.linkedin.com/in/sklein"
    # ...only the approved, non-conflicting fields
  }
```

- This goes through the audited Eloquent save path. The MCP middleware tags it `source:mcp` and
  records the operator as causer → the field-history sheet shows "<operator> · via MCP (manage-model)".
- Do NOT include `last_activity_at` / `first_activity_at` / `next_activity_at` — read-only,
  auto-maintained.
- Verify each write (re-read the field or trust the tool's success payload) and report per contact.

## Report-only suggestions (no column to write)

"Preferred contact channel" has no Contact column. If you want to persist it, use
`manage-custom-field` to define/set a custom field; otherwise just surface it in the report.
`manage-custom-field` `create`/`update`/`archive` are two-stage — a `confirmed: false`
preview then `confirmed: true` to apply — so budget two calls per field change.

## Re-auth note

Any tool returning "MCP server requires re-authorization (token expired)" means the connection is
down — stop and ask the user to re-auth via `/mcp` → alluvo → authorize (confirm the **production**
org). Never substitute tinker writes for `manage-model` — they lose operator attribution.
