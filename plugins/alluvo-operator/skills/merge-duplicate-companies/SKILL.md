---
name: merge-duplicate-companies
description: Find, preview, and merge duplicate company or contact records (Dubletten). Use when the operator says "Dubletten bereinigen", "doppelte Firmen zusammenführen", "doppelte Kontakte zusammenführen", "Kontakt-Dublette", "merge duplicate companies", "merge duplicate contacts", "find duplicate records", "Standorte unter Muttergesellschaft gruppieren", or wants to clean up duplicate or fragmented company or contact records in alluvo — including the follow-up to a POSSIBLE DUPLICATE warning shown when a record was created.
---

# Merge Duplicate Companies (Dubletten bereinigen)

## Purpose
Identify duplicate company records, merge them, and — for genuine branch offices —
correctly group them as locations under a parent company. The same tool and the same
preview→confirm flow also merge duplicate **contacts** (`0-105`); the parent-grouping part
(step 4) is company-only. MCP-native only; no shell access.

> All write steps are two-stage: preview merge → explicit confirmation.

## Prerequisites
- alluvo MCP tools (`mcp__alluvo__*`) available.
- Suspected duplicates are known (name, location) or an automatic search is desired.

## Steps

### 1. Find suspected duplicates
**Option A — automatic:** Call `manage-duplicates` with `action: "find"` for Company (`0-3`)
or Contact (`0-105`) — resolve `model_type` via `list-model-types`. It applies the model's
built-in detection rules (Company: name, email, phone, website; Contact: email,
alternative_emails, phone, mobile, full name) and returns weighted candidate groups.

> **On Contact, `find` now folds German umlauts in the name gate.** Every Contact rule
> except the name-only one requires the two records' names to match as well (a shared
> `info@` inbox must not group two different people). That name comparison folds umlauts
> and diacritics the same way search does (`ö`=`oe`, `ü`=`ue`, `ä`=`ae`, `ß`=`ss`), so
> "Göbel" and "Goebel" satisfy it together. Two records with the **same email** but a
> differing umlaut spelling used to fall out of the group entirely — they no longer do.
> Expect `find` to return **more** groups on Contact than it used to; that is the fix, not
> noise. Company detection is unchanged (its rules set no name gate).

**Option A′ — one field, any model type:** `action: "find-by-field"` with `field`
(e.g. `website`, `email`, `phone`) and optional `min_count` groups records of **any** model
type by a shared value. Its normalization is per field (URLs strip protocol/www, emails
lowercase, phones strip formatting) and does **not** fold umlauts — a `find-by-field` on a
name field still treats "Göbel" and "Goebel" as two values. Use it for the sweep that finds
locations sharing one website (→ step 4), not for person-name duplicates.

**Option B — targeted:** `search-model` with the company name or a fragment of it.
Review the result list for duplicates. Search folds German umlauts and diacritics on both
the indexed and the query side (`ö`=`oe`, `ü`=`ue`, `ä`=`ae`, `ß`=`ss`, plus generic accent
stripping), so "Göbel" and "Goebel" find each other and a spelling variant is no longer a
reason a Dublette stays hidden. That is folding, not fuzzy matching — a typo, an
abbreviation or a differing legal form still needs its own query.

> **The same tool merges contacts, not just companies.** `manage-duplicates` `find`,
> `preview-merge` and `merge` accept Company (`0-3`) **and** Contact (`0-105`); those two are
> the only mergeable model types, and any other is rejected with the allowed list. Everything
> below applies unchanged to a Contact pair, except `keep_einsatzbetriebe`, which is
> Company-only and ignored for Contact merges. One way an operator lands here: a
> `manage-model` create of a Contact/Employee/Candidate answered with a
> `⚠️ **POSSIBLE DUPLICATE**` block — or a `bulk-manage-model` batch answered with the
> aggregated `⚠️ **POSSIBLE DUPLICATES**` summary, which names the flagged rows by their
> `[index]` and lists each row's candidates. Either block is a warning, not a rejection —
> the new record(s) exist, so the follow-up is a merge (or a decision that they are two real
> people who share a name), never a retry of the create. An Employee/Candidate create warns
> on a shared name even when no date of birth was given, so a name-only match is a weak
> signal: read both records before merging. See `→ triage-data-quality`.

### 2. Evaluate each candidate pair

> **Option C — a Contact arrives here flagged.** A Contact can carry an open
> **"Possible Duplicate Contact"** issue (`severity: "medium"`, `remediation_kind: "manual"`,
> identifier `App\Issues\DataQuality\Contact\PossibleDuplicateContact`). It is raised when an
> identity field (`email`, `phone`, `mobile`, `first_name`, `last_name`) flips from **empty to
> set** on an already-saved Contact — an enrichment agent, an operator edit, an MCP write —
> and by the nightly sweep. The matching contact(s) are named in the issue's `description`;
> start from those instead of running `find`. The finding is advisory and never blocked the
> write that caused it, and it does not reliably clear itself after the merge, so resolve or
> dismiss it explicitly once this skill is done — see `→ triage-data-quality`, step 3e.

> **Where a client company's contact duplicates often come from.** When an employee has hours
> signed on their phone, they pick the confirming person by typing a name; not finding them,
> they add a new contact. Until iOS autocorrect was switched off in that search field a typed
> surname could be silently rewritten, the search found nothing, and a contact that already
> existed was created a second time. The tell-tale shape is a near-duplicate surname on a client
> company, often with no email and no HubSpot reference. The cause is fixed going forward; the
> records already created are an ordinary merge. One thing to preserve when choosing the
> survivor: the duplicate probably carries the company membership labelled `timesheet_approver`
> and an Approver portal grant, because on-site signing writes both — check the survivor still
> has them afterwards (`→ approve-stundenfreigabe`).
>
> **The picker's suggestion list is per employee, so duplicates keep arriving from new faces.**
> Before typing, an employee only sees people *they themselves* have had sign or created at that
> client — never the company's contacts, and never the one an operator tagged. Someone new on
> the ward therefore starts from an empty list and has to search by name to avoid re-creating a
> contact that exists. That is the reflex to teach when you hand a cleaned-up client back; the
> label and the portal role do nothing for findability until the employee types.

For each candidate pair call `get-model` on both records and compare:
- Same trade address / postal code?
- Same contact persons (Contact IDs)?
- Same HubSpot entry (external reference)?
- Different branches or divisions of the same group?

**Decision:**
- **True duplicate** → Merge (Step 3)
- **Different branch offices** → Parent assignment (Step 4)

**When the two records disagree on a field, ask who wrote it.** `get-field-history`
(`model_type` + `record_id`, optional `field` to scope to one attribute, optional `limit`
1–50, default 20 events, newest first) returns old → new per change with the actor: a named
user, a machine source labelled `(system)` (import, mcp, api, …), or `⚠️ UNATTRIBUTED` — no
user and no recognised source. A field a colleague deliberately maintained outranks one an
import baked in, and an unattributed write is evidence that **nobody** reviewed the value —
not that it is correct. `get-timeline` cannot answer this; it returns activities only, never
attribute changes. Read-only, same `view` permission as `get-model`.

### 3. Merge duplicates

Decide which record to keep (`keep_id`, recommended: the older / more complete one — and, on
a conflict, the one whose values are attributable to a person rather than to an import) and
which to remove (`remove_id`, merged into `keep_id` then deleted).

> **"More complete" is not the same as "more useful" — count relationships, not columns.**
> The direction is the operator's call, and the sparse record is often the one to keep: prefer
> the side with the calls, tickets, tasks and notes hanging off it, an active workflow, and
> fields a human typed. In the production case that prompted the possible-duplicate check
> (step 2, Option C), the right survivor was a **phone-only** Contact from an anonymous
> inbound call — it carried the calls, the tickets, an open task and a hand-written
> availability profile — over a chat-lead record that merely had a name and an email filled
> in. Relationships survive either direction (they are re-pointed onto `keep_id`), so what the
> direction actually decides is which record's **id and URL** live on, and which side's
> conflicting or `not_carried` column values are the ones discarded — plus the fact that the
> removed record is deleted. Present both records to the operator and let them choose.

#### 3a. Preview
`manage-duplicates` with `action: "preview-merge"`, `keep_id`, `remove_id`. Shows:
- **Columns filled from duplicate** — which fields the kept record gains from the removed one
- **Relationships re-pointed** — linked Contacts, activities, and notes that will be reassigned
- **Values that will not survive this merge** — the loss report; read it before confirming

The preview is complete: a value that disappears in the merge is named here. A merge carries
every column of the table except a small technical and policy set, so fields that used to
vanish silently (address formality, preferred language, consent flags, the availability
profile) now survive. Each loss line reads
`column: keeping "<kept>", discarding "<discarded>" (<reason>)` with one of two reasons:

- **`conflict`** — both records hold a value on a carried column, they differ, and there is
  nowhere else to put the removed record's value, so it is dropped. This **blocks the merge**
  (see 3c).
- **`not_carried`** — a policy-excluded column (provenance, verification, a Company's `slug`)
  held a value on the removed record. Reported only, never blocks. A differing `record_source`
  is the normal case, not a reason to hesitate — and on a Company merge a differing `slug` is
  *always* listed, since two records never share one. Nothing about a merge changes where the
  kept company lives; the URL of the kept record stays as it is.

**Not every differing value is a loss.** Three mechanisms resolve a difference before it
becomes a `conflict` line — read the preview, don't assume:

- **Overflow into an empty sibling.** On a **Contact**, a differing `phone` moves into `mobile`
  when the kept record's `mobile` is empty — a second reachable number is kept, not discarded.
  It then appears under *Columns filled from duplicate* as `mobile`, and the merge is not
  gated. Only when the kept record already has a `mobile` does `phone` become a real
  `conflict`. Company has no such pair, so this applies to Contact merges only.
- **Best value wins on recency columns.** `last_activity_at` / `last_contacted_at` keep the
  **most recent** of the two, `first_activity_at` / `first_contacted_at` the **earliest**.
  These never appear as a loss line, and no post-merge repair of contact dates is needed —
  merging a stale record with a freshly-contacted duplicate keeps the fresh date.
- **Absorbed into a list.** A merged-away Contact `email` is kept in `alternative_emails`, a
  merged-away Company `name` in `alternative_names`, so both still resolve/find the record.

`preview-merge` never refuses on data loss — it always reports.

#### A Contact merge carries contract references over — it is not blocked by them
A duplicate Contact that is the **Empfänger** of a Rahmen- or Einsatzvertrag, or the
**Ansprechpartner** of an Einsatz, merges normally. Those references move onto the kept
Contact *before* the duplicate is deleted, so the contract keeps its recipient and the
deletion guard finds nothing left to block. This is the case a merge is the right tool for —
say so plainly instead of sending the operator off to re-point recipients by hand first.

Two consequences worth naming when you report the result:

- **The primary recipient can change.** When **both** sides were recipients of the *same*
  contract, only one recipient row survives, and if the row that vanished held the primary
  flag the contract picks the remaining recipient with the lowest sort order as primary. That
  may be a **third person**, not the kept Contact. The primary recipient is whose name an
  unsigned AÜV prints as customer signer (`→ manage-contract-lifecycle`), so check the
  affected contracts afterwards and set `primary_recipient_contact_id` if the operator wants
  somebody else.
- **Never offer "just delete the duplicate" as the shortcut.** A bare `delete-model` on a
  Contact (`0-105`) is still refused while a live contract names the person — that guard is
  unchanged — and a delete would throw the record's history away instead of folding it into
  the survivor. Merge is both the working path and the correct one.

#### Blocked at 3a: both Contacts carry an Employee and/or a Candidate
A Contact pair where **both** sides have a linked Employee, a linked Candidate, or both,
cannot merge directly — but it is no longer a dead end for either role. `preview-merge` and
`merge` return a guided work plan *instead of* the normal preview (so no loss report appears
in this case): an `# Employee Merge Preflight`, a `# Candidate Merge Preflight`, or — when
both roles block the pair — both plans joined by a `---` separator. Each plan shows:

- **Role-level columns that would move** onto the kept record — only ones it is missing
  (Candidate side: headline, summary, CV analysis metadata, UTM attribution, …).
- **Relations that would re-point** — counted on the duplicate. On the Employee side this is
  now **every table that points at the duplicate**, derived from the schema (~60 candidates:
  timesheets, time entries, absences, salaries, payslips, documents, bank accounts, tax
  profiles, shifts, invoices, reimbursements, company cars, driving-licence checks, tasks, …)
  instead of the five hand-written relations it used to show, and each line is keyed by the
  **table name** (`timesheets`, `employee_vehicle`) rather than a label. Read the lines the
  plan actually prints — do not look up fixed keys such as `staffing_experiences` or
  `assignment_contracts`, and do not paraphrase the list from memory. Candidate side is
  unchanged: applications, tasks, comments, the CV upload.
- **Unique-constraint collisions** (e.g. `employee_number`) — handled by trashing the
  duplicate first so the value can move.
- **Open decisions — never auto-resolved.** Employee: a column both records set to
  *different* values, and EmploymentPeriod rows whose windows overlap. Candidate: a
  differing `status`, and both records holding a CV.

Work it in this order:

1. Read the plan from `preview-merge` on the Contact pair. **That is the only place it is
   shown** — `manage-record-action` with `confirmed: false` merely echoes the payload it would
   submit and does not run the action, so it prints no preflight.
2. Present the open decisions to the operator and resolve each by hand: pick the surviving
   value (`manage-model` on the kept Employee/Candidate, `confirmed: false` →
   `confirmed: true`), reconcile the overlapping employment periods, or decide which CV to
   keep. Step 3 refuses while any is still open.
3. Run the mechanical half on the **kept** role record via `manage-record-action`
   `operation: "execute"`:
   - Employee (`0-2`): `record_id: <kept Employee id>`, `action: "merge_employee"`,
     `data: { source_employee_id: <duplicate Employee id> }`.
   - Candidate (`0-81`): `record_id: <kept Candidate id>`, `action: "merge_candidate"`,
     `data: { source_candidate_id: <duplicate Candidate id> }`.
   Two switches gate it, and the one inside `data` wins **only on the top-level
   `confirmed: true` branch**: the tool fills its top-level `confirmed` into `data.confirmed`
   only when that key is **absent**, and a top-level `confirmed: false` forces `data.confirmed`
   to `false` whatever you sent, so it can never merge. So call with top-level
   `confirmed: true` **and** `data.confirmed: false` first — the action takes its own
   write-free branch and writes nothing. Read the heading to tell the two runs apart: a
   preview comes back as `# Action Preview (nothing written): merge_employee` (resp.
   `merge_candidate`), an actual merge as `# Action Executed`. For **`merge_employee`** the
   preview carries the plan under `Response Data`: `columns_moved`, `relations_repointed`
   (one line per table with its row count), `needs_acknowledgement` (the subset the gate is
   about), `unique_collisions` and `open_decisions` — that is what you show the operator.
   **`merge_candidate` has no such payload**: its preview only proves the call is
   well-formed, so for candidates the plan still comes from `preview-merge` on the Contact
   pair (step 1). Then repeat with `data.confirmed: true` to execute. Leaving `confirmed` out of `data` merges immediately,
   and a top-level `confirmed: false` never invokes the action at all (just the generic
   tool-level echo).
   **`merge_employee` costs a second acknowledgement when the duplicate carries weight.**
   When the duplicate holds payroll, working-time or legal rows — `absence_periods`,
   `bank_accounts`, `compensation_components`, `employee_documents`, `employment_periods`,
   `invoices`, `payslips`, `reimbursements`, `salaries`, `shift_assignments`,
   `sick_leave_requests`, `tax_profiles`, `time_entries`, `timesheets`, `vacation_requests` —
   the confirmed run refuses unless `data.acknowledge_relations: true` is sent with it, and
   the refusal names each of those tables with its row count. That refusal is the gate
   working, not an error. Show the operator the counts from step 1's preflight (or from the
   refusal itself), say plainly that those records are being folded into the surviving
   employment, and only send `acknowledge_relations: true` once they have agreed — setting it
   pre-emptively on the first confirmed call to skip the refusal defeats the gate. A
   duplicate carrying none of those tables merges on `data.confirmed: true` alone, and
   `merge_candidate` has no such flag.
   The confirmed run still refuses while any open decision is unresolved. It fills the
   missing columns, re-points the relations, and trashes the duplicate role record. The
   operator needs delete rights on that duplicate, not just update rights on the kept
   record. When both roles block the pair, run both merge actions — either order — before
   moving on.
4. Re-run `manage-duplicates` `merge` on the Contact pair — with the duplicate role
   record(s) gone it now goes through the normal path (3a–3c), data-loss gate included.

Never soft-delete a Candidate (or Employee) to unblock a Contact merge — that destroys real
application or employment history; `merge_candidate` / `merge_employee` exist precisely so
the history is re-pointed instead. In `bulk-merge`, a role-blocked pair is skipped rather
than blocking the other pairs, with a reason naming whichever role(s) block it and the merge
action(s) to run — re-run `preview-merge` on that pair to see the full plan.

#### 3b. Request confirmation
Present the preview in full, including every loss line. Ask explicitly:
"Should I merge these two records now? The removed record will no longer be
independently visible afterwards." If the preview lists any `conflict`, name the affected
columns and both values in the question — that is the operator's decision to make, not yours.

#### 3c. Execute merge
`manage-duplicates` with `action: "merge"`, the same `keep_id`, `remove_id`. Returns the
kept record ID, plus the same loss report for what was actually discarded.

**A refusal is expected, not an error.** If any `conflict` loss exists, the merge is refused
with "Merge refused — it would discard data." and the full loss block. That is the gate doing
its job — do not report it as a failure and do not retry unchanged. Instead:

1. Read the `conflict` lines and decide, per column, which value is right (step 2's
   `get-field-history` answers who wrote each one).
2. Copy anything worth keeping onto the `keep_id` record with `manage-model`
   (`confirmed: false` → `confirmed: true`). Once the kept record holds the better value,
   that column is no longer in conflict.
3. Re-run the merge with `confirm_data_loss: true` to accept the remaining discards.

Only set `confirm_data_loss: true` after the operator has seen the loss block and agreed.
Passing it reflexively to make the error go away silently destroys the values the gate
exists to protect.

### 4. Group branch offices (no merge)
When the records are genuine locations (e.g. "Marienhospital Gelsenkirchen" and
"Marienhospital Köln" of the same hospital group):

1. Identify or create the parent company in alluvo (`manage-model`,
   `confirmed: false` → `confirmed: true`).
2. Call `manage-association` for each branch: branch Company → parent Company.
   Preview (`confirmed: false`) → confirmation → execute (`confirmed: true`).
3. Clean up branch names if needed (`manage-model`, same preview-confirm flow).

### 5. Quality check
After the merge / grouping:
- `get-model` on the kept record: all Contacts, activities, and notes present?
- `count-model` as a sanity check: duplicate count for this name reduced?

## Output
- For working duplicates in the web app instead: the in-app surface is the Data
  Quality Dashboard's Duplicates tab (`dashboard_url` from `get-issues-overview`,
  plus `?tab=duplicates`) — the old standalone Duplicate Records settings page now
  redirects there.
- List of found duplicate pairs / clusters with assessment (merge vs. grouping)
- Per merge: kept record name · ID · data carried over · any values discarded (from the
  loss report), and for a `conflict` whether it was resolved by copying onto the kept record
  or accepted via `confirm_data_loss`
- Per grouping: parent company name · ID · assigned branch offices
- Note on fields requiring manual review (e.g. different contacts with the same name
  that were not automatically merged)

## Related skills
- `→ triage-data-quality` — the broader data-quality routine that surfaces duplicate issues.
- `→ enrich-contacts-from-activities` — fix sparse contacts revealed during the merge review.
- `→ approve-stundenfreigabe` — the on-site signer picker that produces many client-contact
  duplicates, and what the surviving contact must keep (`timesheet_approver`, Approver grant).
- `→ prospect-companies` / `→ profilvertrieb` — resume outreach qualification once the
  duplicate is resolved (a `new` record may have been a sibling of an `open_deal`).
