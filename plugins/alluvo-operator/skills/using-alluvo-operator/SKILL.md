---
name: using-alluvo-operator
description: Entry point and navigator for the alluvo Operator plugin. Shows which guided workflows (skills) are available and routes to the right one. Use when the operator asks "was kannst du", "wie fange ich an", "hilf mir", "womit kannst du helfen", "überblick", "welche workflows gibt es", "what can you do", "where do I start", greets without a concrete task, or seems unsure which skill fits. Also the reference for cross-cutting alluvo tool behaviour that belongs to no single workflow — including page access and permission sets ("gib X Zugriff auf Y", "warum sieht X den Teamkalender nicht", Berechtigung, permission set, "give someone access to a page") and access to a Wissensdatenbank ("wer darf die Wissensdatenbank sehen", "Wissensdatenbank freigeben", "knowledge base members").
---

# alluvo Operator — Navigator

## Purpose
The starting point. This skill makes no changes to data — it maps the operator's
request to one of the guided tasks (skills) and routes there. Use it when it is
unclear which skill fits, or when the operator wants an overview.

> Read-only / orientation only. Writes nothing. Points to the matching skill,
> which in turn shows a preview before every write operation.

## Prerequisites
Requires an active **alluvo MCP connection** (`mcp__alluvo__*`). All downstream
skills run inside the operator's tenant and respect their permissions.

## How to use
1. **Clarify the request.** If the operator just greets or asks "what can you do?",
   show the catalog below (by category) and ask for the concrete goal.
2. **Route to the matching skill.** For a concrete request, name the matching skill
   and start it directly (rather than rebuilding the workflow here).
3. **Resolve ambiguity.** If more than one skill fits, briefly name the options and
   the typical sequence (see quick decision guide).

## Resolving a model type from operator wording (`list-model-types`)

Cross-cutting — applies wherever a skill needs a `model_type`.

- **`list-model-types` has an "Also known as" column.** Alongside ID, Label and Slug it
  lists each type's aliases — the German vocabulary an operator actually says, mapped onto
  the English model type: `Dienstplan`/`Schichtplan` → SchedulePeriod, `Stundenzettel`/
  `Tätigkeitsnachweis` → Timesheet, `Rahmenvertrag`/`AÜV` → FrameworkContract,
  `Konkretisierung`/`Einsatzvertrag` → AssignmentContract, `Einsatzmitteilung` → Assignment,
  `Beleg` → ReimbursementReceipt, `Reisekosten` → Reimbursement, `Personalfragebogen` →
  Employee, `Ansprechpartner` → Contact, `Kunde`/`Auftraggeber` → Company.
- **Read the type off that column instead of guessing from the English label.** When the
  operator names a document or list in German, the alias is the mapping — do not infer a
  type from a label that merely sounds similar, and do not hardcode an ID from memory.
- **Matching is locale-agnostic.** Every locale's aliases are unioned, so an English term
  resolves in a German session and vice versa. You never have to switch vocabulary to hit it.
- **The column is sparse.** Only some types declare aliases; the rest print `—`. A dash says
  nothing about whether the type is the right one — fall back to Label and Slug there.
- **These are type-level aliases, not record nicknames.** They ship with the product and are
  not operator-editable; a specific record's alternative names are a separate thing.
- **IDs did not change.** The IDs skills already cite (`0-2` Employee, `0-3` Company,
  `0-105` Contact, …) are unchanged — the alias column is additional, not a replacement.
- **Every model type is listed now — with an access status, not by omission.**
  `list-model-types` returns all of them, each marked `available`, `read_only`,
  `requires_permission`, `requires_feature` or `not_available`, plus a short reason. So
  **"it isn't in the list" is no longer a valid conclusion that a type doesn't exist** —
  find the row and read its status. `not_available` is architectural (true for everyone);
  `requires_permission` / `requires_feature` are about this operator's role and this
  tenant's plan right now, which is the answer to give them instead of "not supported".

## Org structure: Niederlassung, Bereich, Kostenstelle, Team (`0-73` / `0-75` / `0-72` / `0-74`)

Cross-cutting — these four are the tenant's own internal structure, not client data, and all
four are now readable **and** writable over `manage-model` (`create` / `update`, two-stage:
`confirmed: false` preview → operator yes → `confirmed: true`). Earlier guidance that a
Niederlassung has to be created in the web app, or that a `branch_id` can be written but never
resolved, is obsolete — `search-model` on `0-73` works.

- **The chain is Branch → BusinessUnit → CostCenter.** A CostCenter hangs off
  `business_unit_id`, not off a branch directly. Resolve or create the level above before the
  level below.
- **`Team.branch_id` is required; `BusinessUnit.branch_id` is nullable.** The asymmetry is
  deliberate — a Bereich is allowed to exist without a Niederlassung. Never invent a branch to
  satisfy a BusinessUnit create.
- **`code` is required and tenant-unique on BusinessUnit and CostCenter.** A create without
  `code` is rejected, and a duplicate `code` is rejected before it reaches the database. Branch
  and Team have no `code`.
- **A Niederlassung's address IS writable over MCP now** — two paths, both real. Either pass a
  nested `address` object to `manage-model` `create` / `update` on `0-73` (`recipient_name`,
  `care_of`, `street_name`, `street_number`, `address_supplement`, `po_box`, `zip`, `city`,
  `subdivision_code`, `country_code`), or set it afterwards with `manage-address`
  `action: "set"`, `model_type: "0-73"`, `purpose: "branch"`. `city` becomes **required** as soon
  as any other address field is present; omitting `address` entirely on `update` leaves the
  branch's current address untouched. Earlier guidance to send the operator to *Einstellungen →
  Niederlassungen* for the street address is obsolete. A `branch`-purpose address is never
  geocoded — it is not matching-relevant.
- **`owner_id` defaults to you when omitted** — Branch and Team stamp the acting user as owner on
  create, they are never left unowned. Pass `owner_id` explicitly (resolve the User via
  `search-model` on `0-1`) whenever the Niederlassung or Team belongs to someone else.

## Addresses (`manage-address`) — the one write path

Cross-cutting — applies inside every skill below. **`manage-location` no longer exists, and
Location (`0-95`) is no longer exposed over MCP at all**: `manage-model`, `get-model`,
`query-model`, `search-model`, `count-model` and `manage-record-action` on `0-95` all answer
*"Model type '0-95' (Location) is not available via the generic model tools … this type has no
MCP surface"*. That error carries no routing hint — when you see it, the answer is
`manage-address`. Addresses are their own record type now (**Address, `0-446`**), owned by
exactly one record for exactly one purpose at a time, and historized.

**Owners and their allowed `purpose` values** — an unsupported pair is rejected naming the
owner's allowed list:

| `model_type` | Owner | Allowed `purpose` |
|---|---|---|
| `0-3` | Company | `headquarter`, `postal`, `billing` |
| `0-341` | ClientSite (Einsatzbetrieb) | `site` |
| `0-105` | Contact | `home`, `second_residence`, `postal`, `work` |
| `0-73` | Branch (Niederlassung) | `branch` |
| `0-160` | CompanyJobPosting | `site` |

- **Employees and Candidates own no address.** `model_type: "0-2"` is rejected outright with a
  pointer to the linked **Contact** — identity-root, same rule as every other identity field.
  Resolve `contact_id` and pass `0-105`.
- **Four actions.** `set` = create-or-replace the current address for owner+purpose, closing the
  old row and inserting a new one so the history survives — this is a genuine *move*. `correct` =
  fix the current row in place (typo), no history event, no `valid_from` change. `list` = current
  row plus full history as a Markdown table (also the read path — `purpose` is an optional
  filter). `end` = close the current validity, leaving the owner without a current address for
  that purpose. Choosing `set` where `correct` was meant piles up fake move history; choosing
  `correct` where the customer really moved erases the old seat. Ask which it is when unclear.
- **`set` only supersedes forward in time.** A `valid_from` earlier than the current row's own
  `valid_from` is rejected, naming the earliest date it would accept — use `correct` for a
  same-period fix.
- **`city` (or `po_box`, or `address_line`) is required**, `country_code` defaults to `"DE"`.
  Purposes use underscores: `second_residence`, never `second-residence`, and there are no
  `purpose_slug` hyphenated values (`work-site`, `billing-address`, `branch-office`) any more.
- **The Bundesland is derived, not guessed.** `subdivision_code` is stored ISO 3166-2
  (`"DE-NW"`); leave it empty for a German address and supply a correct five-digit **`zip`**
  instead — it is derived from that, and the zip also drives geocoding and matching. For an
  Austrian or Swiss address there is no postcode mapping, so pass `country_code` (`"AT"` /
  `"CH"`) **and** `subdivision_code`, which accepts the spelled-out Kanton/Bundesland (`"Wien"`,
  `"Zürich"`, `"Genf"`) and stores the ISO form.
- **Only three owner+purpose pairs are geocoded:** Contact `home`, Company `headquarter`,
  ClientSite / CompanyJobPosting `site`. Everything else (every `billing`, `postal`, `branch`,
  `work`, `second_residence`) is marked ineligible on purpose and never gets coordinates — do
  not report that as a defect, and do not expect geo matching from those purposes.

## Reading relational data (`query-model`)

Cross-cutting — applies inside every skill below.

- **A `query-model` warning is a finding, not noise.** Read the warnings back rather
  than reporting only the rows. `Include "recipients": 3 further row(s) were omitted
  because the linked Contact record is deleted (soft-deleted)` means the list you got
  is **not** the whole picture: a deleted contact still occupies the link, and a
  short list that looks healthy may be missing exactly the row the question was about.
- **A dropped filter condition is reported, never silently ignored.** A condition whose
  operator the column cannot take is skipped, and every reader says so: `count-model` /
  `search-model` append a `⚠️ … filter condition(s) were skipped` block, and
  `query-model` warns `Filter condition on '<field>' (operator '<op>') was NOT applied:
  <reason>`. Any of these means the result is **broader** than what was asked — fix the
  operator (`get-model-schema` with context `list` shows the valid operators per field)
  and re-run rather than trusting the count or the rows.
- **Includes are limited per parent record.** Each relation returns at most `limit`
  rows (default 10) **for each** root record. Where a completeness claim rests on it
  ("this contract has exactly one recipient", "this contact belongs to no company"),
  set `limit` explicitly and check the returned count against it — or read the single
  record with `get-model` instead of inferring from a list query.
- **Pivot columns have to be asked for.** On a many-to-many include, extra columns
  carried by the link row itself (`is_primary`, …) come back only with `"pivot": true`
  or `"pivot": ["is_primary"]` in that relation's include spec, under a `pivot` key on
  each related row. Requested on a relation that is not many-to-many it is ignored
  with a warning.
- **A wrong name in `fields` no longer fails the call — it comes back as a note or a
  warning.** `search-model` and `query-model` (root `fields` and every `include[].fields`)
  first rewrite the names a curated alias map knows: on a Vertrag `start_date`/`end_date`
  are read as `valid_from`/`valid_until` and `contract_number` as `identifier`, on an
  Abwesenheit as `starts_at`/`ends_at`, `personnel_number` as `employee_number`,
  `contact_name` as `full_name`. Every rewrite prints an
  ``ℹ️ Note: interpreted selected field `x` as `y` `` line. Whatever stays unknown is
  **dropped from the projection** and reported as
  `⚠️ Unknown field(s) requested: [...] — omitted from the result.` with the valid field list.
- **So an absent column is not an empty value.** Read that note/warning block before
  concluding anything from a column that is not in the rows — "no end date recorded" may
  only mean you asked for a name this model does not have. Correct the name and re-run
  rather than reporting the gap to the operator.
- **Two shapes still hard-fail.** None of the requested names exist on the model (`None of
  the requested fields exist on this model.`), or the unknown names are **relation** names —
  a relation is not a column, so read the whole record with `get-model` instead of narrowing
  the projection.
- **`search-model` no longer rejects a field just because it is not a table column.** A field
  that `get-model-schema` (context `list`) documents but that the record's list view does not
  show — it lives on the detail view only — used to come back as `Unknown field(s) requested`
  even though `filter_groups` accepted the very same name. Naming it in `fields` now returns
  its value. The Kontakt (`0-105`) consent columns are the case you will meet:
  `whatsapp_opt_in_at`, `whatsapp_opt_in_source`, `whatsapp_opt_in_reason`,
  `whatsapp_opt_out_at`, `whatsapp_opt_out_reason`, `whatsapp_undeliverable_at`,
  `whatsapp_undeliverable_reason` are readable this way, so "may we message this person on
  WhatsApp" is answerable from a list read instead of one `get-model` per contact. They stay
  **not writable** through `manage-model` — see `→ enrich-contacts-from-activities`.
- **`get-model-schema` (context `list`) stays the cheaper path**, not a precondition. Call it
  once per model_type when you are about to build `fields` or `filter_groups`, rather than
  defensively before every read — but never keep hand-maintained field lists in a skill just
  to work around the old failure.

## Addressing a record across tools (`id` / `model_type` synonyms)

Cross-cutting — applies to every tool that takes a record id.

- **The tool family uses four names for "the record's id" and three for "its type"**, and
  which one a given tool wants is not guessable: `get-model` takes `id`, `get-field-history`
  and `manage-workflow` take `record_id`, `get-profile` / `manage-media` / `manage-apps` take
  `model_id`, `get-timeline` / `manage-activity` take `subject_id`.
- **Sending the wrong one of those names no longer rejects the call.** A tool that declares
  `id` also accepts `record_id` / `model_id` / `subject_id`; one that declares
  `subject_id` / `subject_type` also accepts `record_id` / `model_id` / `model_type`. It is
  pure renaming: a synonym is read only when the tool does not declare that name itself, and
  only fills a parameter left empty — no value is ever reinterpreted.
- **Still name the parameter the tool declares.** The synonym is a safety net for handing an
  id straight from one tool's output to the next, not a licence to stop reading a tool's
  schema.

## Reading a person's name out of a tool result

Cross-cutting — applies wherever a skill prints, compares or re-uses a person's name.

- **What a tool returns as a person's name is the tenant's display format, not
  "Vorname Nachname".** Employee, Contact, User, Candidate and CompanyContact resolve their
  title through `display_name`, which renders the tenant setting `name_display_format`:
  `FirstLast` → "Anna Müller", `LastFirst` → "Müller, Anna", `LastFirstNoComma` →
  "Müller Anna", `FirstLastInitial` → "Anna M.". That is what `get-model`, `search-model`,
  `query-model` and `bulk-manage-model` put in a relation label or a search hit, what
  `manage-task`, `get-timeline`, `get-field-history` and `manage-apps`
  print as the subject/record label, and what `manage-association` shows for a linked person.
- **The raw name is still in the same payload, under `full_name`.** Nothing was taken away —
  read `full_name` whenever the canonical name is what matters (quoting a name into a document
  or an export, handing it to another tool, comparing two records), and read the label for
  what it is: how this tenant wants a person's name shown to a human.
- **Never parse the label into first/last name, and never diff it against what the operator
  typed.** On a tenant set to `LastFirst`, "Müller, Anna" and "Anna Müller" are the same
  person — a name that "does not match" is then an artefact of the setting, not a data
  problem. When you need the parts, read `first_name` / `last_name`; on Employee and Candidate
  they live on the linked **Kontakt**, not on the record itself.
- **`display_name` is an accessor, not a column.** Never filter or sort on it — `search-model`
  rejects computed/display-only fields with `INVALID_FILTER_FIELD`, the same way it rejects
  `full_name`. Free-text search is unaffected: it runs against the underlying name columns
  (umlaut folding included), so searching a person by name still works.
- **Documents are deliberately unchanged.** Contracts, PDFs and payroll/DATEV exports print
  the full name regardless of the setting, so a label reading "Müller, Anna" in a tool result
  says nothing about what the AÜV will print (`→ manage-contract-lifecycle`).
- **The format is one tenant-wide setting**, readable and writable via `manage-settings`,
  group `brand_identity`, field `name_display_format` (`"FirstLast"` | `"LastFirst"` |
  `"LastFirstNoComma"` | `"FirstLastInitial"` — there is no `"LastOnly"`). Changing it moves
  every person label in the app at once, so treat it as a tenant decision, never as a fix for
  one list.

## Tagging a record (`tags`)

Cross-cutting. **Tags** are free-form labels drawn from **one tenant-wide vocabulary**
(`Tag`, `0-443`) shared by every taggable record. The field behaves identically everywhere:
a flat list of **names** (never ids), **full replacement** — passing `tags` replaces the whole
set, omitting it leaves the set untouched, `[]` clears it — and a name that does not exist yet
is **created on the spot**, so there is no "create the tag first" step. Reads return `tags`
plus a `tags_colors` companion map (name → colour) for display.

**Taggable model types:** Company `0-3`, Contact `0-105`, Employee `0-2`, Candidate `0-81`,
StaffingDemand `0-415`, Task `0-5`, Ticket `0-300`, KnowledgeBase `0-180`, KnowledgeBasePage
`0-181`, NewsArticle `0-187`, Workflow `0-365`, Agent `0-400`. On any other model type `tags`
is simply not a field — there a custom field (`manage-custom-field`) is still the answer.

### A person has ONE set of tags, not one per role record

Employee and Candidate do **not** carry their own tags — theirs live on the linked **Kontakt**.
Tagging an employee writes onto that contact; an Employee and a Candidate sharing one contact
see the same list, and tagging either one tags the person. So never present employee tags and
contact tags as two separate things, and never tell an operator to "also tag the contact" —
that is the same write twice.

### Writing tags

- **Company (`0-3`), Contact (`0-105`), Task (`0-5`), StaffingDemand (`0-415`), KnowledgeBase
  (`0-180`), KnowledgeBasePage (`0-181`), NewsArticle (`0-187`)** — `manage-model` `update`
  with `tags: ["…"]`. Two-stage like every generic write: `confirmed: false` preview → show the
  operator the resulting full list → `confirmed: true`.
- **Employee (`0-2`) and Candidate (`0-81`)** — `manage-model` `update` with `tags` works on
  either, and the write lands on the person's **Kontakt**, because that is where a person's
  tags live. Tagging via Contact (`0-105`) directly is the same write with the same result.
  Whichever you pick, the employee, the candidate and the contact all read back one identical
  list — so never do both, and never tell an operator to "also tag the contact".
- **Agent (`0-400`)** — the write path depends on the agent type; see `build-automation-agent`.
- **Ticket (`0-300`) and Workflow (`0-365`)** — taggable in the product but **not writable over
  MCP**: neither type is generically manageable and no dedicated tool exposes `tags`. Read and
  filter them, and point the operator at the UI for the change itself.

Because the write is a full replacement, **read the current list first and send it back
extended** — `get-model` on the record — or you silently strip every other tag. Names collapse
case- and whitespace-insensitively (`Vertrieb` and `vertrieb ` are one tag) and the first
spelling wins as the display name.

### Reading and filtering by tag

`tags` is a *relation*, not a column, so it does not appear in a plain column listing —
`get-model-schema` does advertise it. Every taggable type is filterable by tag at the **top
level** of `query-model` / `search-model`: a `tags` relationship filter with a sub-condition on
`name` or `color` (e.g. every employee tagged "Nachtschicht"). Nested one relationship deep it
is not offered.

### Managing the vocabulary itself

Rename, recolour, delete: the generic model tools on `model_type: "0-443"`. Writable fields are
`name` (required) and `color` — one of `gray`, `blue`, `indigo`, `purple`, `success`, `warning`,
`danger`; `slug` is derived from `name` on save and is **not** writable. Gated by the `tags.*`
permissions, whereas merely *attaching* a tag is gated by the target record's own update
permission. **A rename or a delete hits every record carrying that tag, tenant-wide** — say so
in the preview. When the operator means "this one record shouldn't have that tag", remove it
from that record's own `tags` list; do not delete the tag.

### Tag changes are auditable

A tag change is recorded in the record's own change history as a **`tagged`** event with the
before/after list, so "who put that label on this record, and when" is answerable —
`get-field-history` with `field: "tags"`. For a person the entry sits on the **Kontakt** the
tags were written to; asking the employee for `tags` history points you there.

## Discovering an action before you run it (`manage-record-action` `operation: "list"`)

Cross-cutting — applies to every skill below that looks an action up before executing it.

- **`list` has two shapes and `record_id` is the switch.** *With* `record_id` you get the
  record's own action bar: `**Available:** Yes/No` and an `**Unavailable reason:**` when it is
  No. *Without* it you get the **static catalog** for the model type — which actions exist,
  their exact names, `**MCP-exposed:**`, description, label, and whether they take a reason
  field or a form. The catalog says so itself (`**Note:** Availability is per-record`), so
  never read "can I run this right now" off it; that answer only exists against a record.
- **The catalog needs no record and reads no tenant row.** It is the cheap way to learn an
  action's exact name and whether it is callable at all, on any MCP-reachable `model_type`,
  before you go hunting for a record to try it on.
- **The per-record `list` names the form's fields; the catalog only says a form exists.** With
  a `record_id`, an action that takes a form prints a **`Form fields:`** block — one line per
  field with its name, type, `(required)` where it is, and its label
  (`` - `reason` (textarea) (required): Begründung / Rechtsgrundlage ``). Without a
  `record_id` the same action shows only `**Has form:** Yes`. So read the parameters off the
  per-record `list` **before** executing; never call an action blind to discover them from
  the validation error it comes back with, and never tell the operator a form's inputs are
  undocumented. The block lists what the form *declares* — it is not a substitute for the
  `confirmed: false` preview, which is still what shows what the action will actually do.
- **A degradation line is not an error and not a missing capability.** One entry that cannot
  be described collapses to a single line instead of taking the response down with it:

  ```
  ### `view-profile-pdf`
  - **MCP-exposed:** No
  - _Details unavailable without a record — pass `record_id` for this action._   ← catalog

  ## Action: `some-action`
  - _Could not be described for this record (reported); the action itself is unaffected._  ← per record
  ```

  Both mean "this entry could not be rendered here", **not** "the action does not exist",
  "the action is unavailable", or "the tool is broken". The action's real name is the one
  printed above the line and the rest of the response is intact. In the catalog the right
  next call is `list` **with** a `record_id`; per record, re-read the record or run
  `execute` with `confirmed: false` and let the preview answer. Never report the action to
  the operator as gone or blocked on the strength of one of these lines.
- **The line that really does mean "you cannot run this" is `**MCP-exposed:** No`.** Only
  `#[McpExposed]` actions are callable through this tool; an unexposed one is something you
  tell the operator to click in the app. That is a different fact from `**Available:** No`,
  which is a state or permission gate on an otherwise callable action and always comes with
  a reason.
- **Read the `Unavailable reason:` — it says *which* gate closed, and they need opposite
  answers.** The four are fixed strings: `This action is not available in the record's current
  state.` (wrong status — the record has to move first, or has already moved past it),
  `You do not have permission to perform this action.` (route it to someone with the right),
  `This action is not available while impersonating another user.`, and the catch-all
  `This action is currently not available.` (DE respectively: "Diese Aktion ist im aktuellen
  Status des Datensatzes nicht verfügbar.", "Dir fehlt die Berechtigung für diese Aktion.",
  "Diese Aktion ist im Stellvertretermodus nicht verfügbar.", "Diese Aktion ist derzeit nicht
  verfügbar."). Never report a state block as a missing permission, or the operator goes
  hunting for rights they already have. When `execute` hits the same gate it repeats the reason
  and appends the record's own **`Current record status: <status>`** — quote that status back
  instead of retrying.
- **A catalog label is the action's *declared* label.** An action whose label is computed
  from the record — a pause/activate toggle, say — shows its generic (occasionally blank)
  declared label in the catalog. Quote labels to the operator from the per-record `list`,
  and never infer a record's state from a catalog label.

## Retiring a record instead of deleting it (`archive` / `unarchive`)

Cross-cutting — `manage-record-action` carries two generic, MCP-exposed actions, **`archive`**
and **`unarchive`**, on the model types whose resource registers them. `list` without a
`record_id` is how you check a given `model_type`. Today the ones an operator meets daily are
**`CompanyDepartment` (`0-107`, Abteilung)** and **`PortalMembership` (`0-430`)**;
`FeedbackQuestion` has them too.

- **Archiving is reversible and destroys nothing.** It sets `archived_at`; the record stays
  fully readable, keeps its history and its relations, and `unarchive` clears the flag again.
  It is not a delete and never a stand-in for one.
- **The one exception: on `PortalMembership` (`0-430`), `archive` also revokes portal access**
  — it forces `status` to `disabled` alongside `archived_at`, so it is not the pure visibility
  change the generic action description promises. And `unarchive` is **not** symmetric: it puts
  the row back on the list and leaves access disabled. Never describe the pair as undo/redo
  there — `→ approve-stundenfreigabe` for what it takes to restore a login afterwards. It is
  also **not** the way to take access away on its own: `0-430` carries a dedicated
  `revoke-portal-access` (below), which drops the role grants and leaves the person on the
  customer's Kontakte list. Archive only when the operator means "aus der Liste nehmen" too.
- **The two are mutually exclusive.** `archive` disappears from `list` once the record is
  archived (only `unarchive` shows), and vice-versa. Two-stage as always: `confirmed: false`
  preview → operator yes → `confirmed: true`.
- **`archived_at` is not writable.** It is in no `update` schema, so `manage-model` and
  `bulk-manage-model` silently drop it. The action is the only path, in either direction.
- **Archived records are NOT hidden from MCP reads.** There is no global scope: `search-model`,
  `query-model`, `count-model` and `get-model` return them like any other record, and
  `archived_at` is not one of the default display columns — so a plain search gives you no
  warning at all. Ask for it (`fields: [… , "archived_at"]`) or filter on it (`is_null` = in
  active use, `is_not_null` = archived) before you present a hit as current or write it onto
  anything.
- **On `0-107` and `0-430` the operator's screen hides them and your read does not.** Those two
  lists drop archived rows by default in the UI (the "Archivierte anzeigen" toggle brings them
  back); the MCP tools have no such default and no `with_archived` parameter. So a plain count
  can legitimately come out higher than the number in front of the operator. When you report a
  count or a list for either type, exclude archived rows yourself (filter `archived_at`
  `is_null`) or say which population you counted — do not let the two numbers disagree silently.
- **It is the answer when a delete is refused.** A record other rows still point at cannot be
  deleted — `delete-model` comes back with the referential blockers (for a department: "N
  assignments, N assignment contracts, …"). That is a reference count, **not** a missing
  permission; do not report it as one. Offer archiving instead of pushing the delete.

## The `confirmed` switch on `manage-record-action`

Cross-cutting — applies to **every** record action, whatever the skill.

- **The top-level `confirmed` decides preview vs. write. Nothing else does.** Top-level
  `confirmed: false` (or omitted) is *always* a write-free preview. Some actions carry a
  second `confirmed` **inside `data`** (their own two-stage flow); on a top-level `false`
  call that key is forced to `false` no matter what you sent — `## Data to submit` echoes
  `confirmed: false` and the response says the value was ignored. `data.confirmed` is only
  honoured on the top-level `confirmed: true` branch, where an explicit `data.confirmed: false`
  still yields the action's write-free preview and an absent key inherits the top-level `true`
  and **writes**.
- **So: to execute, send top-level `confirmed: true`.** A `data: { confirmed: true }` under a
  top-level `false` does nothing — it used to write under a `# Preview:` heading, and that is
  the behaviour that changed. If an operator reports "I confirmed and nothing happened", this
  is the first thing to check.
- **Read the heading, then the payload.** A plain top-level `confirmed: false` call is headed
  `# Preview: Execute Action …`. The `data.confirmed: false` route is headed
  `# Action Preview (nothing written): <action>`; only a real write is headed
  `# Action Executed`. `preview_only` in the **Response Data** says the same thing in the
  payload — `true` = nothing was written. Never report a write off the banner alone.

## Previewing an action that sends mail (`manage-record-action`)

Cross-cutting — applies to every mail-sending action below (Personalfragebogen and
Profil-Anforderung, Vertragsversand and Auftragsbestätigung, Portal-Einladung,
Mitarbeiter-Einladung, Ticket-Weiterleitung).

- The `confirmed: false` preview of an effect marked `sends_mail` prints **`subject`**,
  **`to`** and a **`body (markdown)`** block. Subject and recipients are the complete,
  literal values — quote them verbatim and confirm the recipient off the preview.
- The body is a **markdown rendering** of the notification, **cut off at 1.200
  characters** with an explicit `… truncated, N more characters of mail body._` marker.
  When that marker is present, do not tell the operator the mail contains nothing
  further, and never paraphrase the mail as if you had seen all of it.
- The preview shows no layout, styling, links-as-rendered or footer. Never describe what
  the recipient's mail will *look* like from it.
- Nothing about **what is sent** changed — this is how the preview is displayed. It is
  still a preview: mail goes out only on `confirmed: true`, after an explicit operator yes.

## Reading a settings group before you change it (`manage-settings`)

`manage-settings` has **three** actions — `get`, `describe`, `update` — and its per-field
documentation is **no longer in the tool description**. Until you call `describe`, you have
not seen the field names, types, defaults or the business rules behind them for that group.

- **`describe` is the docs, `get` is the tenant's data.** `describe` returns the group's
  documented fields (types, defaults, the reasoning behind them) and reads nothing from the
  tenant — it needs no settings permission. `get` returns the current values.
- **`group` is optional — but only for `describe`.** `manage-settings(action: "describe")`
  with no group lists which groups have long-form docs and which don't (a group with no prose
  is still a real group; `get` and `update` work on it). For `get` and `update` the tool
  errors out and names the valid groups when `group` is missing.
- **Always `describe` (or `get`) the group before an `update`.** Several fields are **paired**
  — changing one without its partner leaves the product contradicting itself
  (`candidate_flow_prompts.candidate_requirements` vs. `soft_requirements` is the documented
  example) — and that warning now lives in `describe` output, not in the always-loaded tool
  description. Do not guess a field name from memory.
- **An unknown group is an error, not an empty result**, on every action: it comes back
  naming the full list of valid groups. Read that list rather than retrying variants.
- **`confirmed` gates exactly one group.** `candidate_flow_prompts` previews and writes
  nothing without `confirmed: true`; for every other group it is ignored and `update` writes
  immediately — so the operator's yes has to happen *before* the call.

```
manage-settings(action: "describe")                        # which groups are documented
manage-settings(action: "describe", group: "timesheet")    # that group's fields + rules
manage-settings(action: "get", group: "timesheet")         # the tenant's current values
```

### The `slack` group — companion kill switch and per-channel priming

The Slack **companion** is the `@alluvo` bot an operator mentions inside a Slack channel or
thread. Its two tenant-wide settings live on `manage-settings`, group `slack`, and **MCP is the
only editor** — `channel_instructions` has no settings page at all, so this call is the whole
product surface for it.

- **`describe` has nothing to say about this group** — it has no long-form docs yet. That does
  not make it an unknown group: `get` and `update` work normally. Use
  `manage-settings(action: "get", group: "slack")` as the "read before you write" step here.
- **`companion_enabled`** (bool, default `true`) — the per-tenant kill switch. The Slack connect
  flow also writes it, and a **global** switch gates on top of it, so `true` here means "this
  tenant permits the companion", not "the companion is guaranteed to answer".
- **`channel_instructions`** (list, max 100 entries) — standing instructions for one channel.
  Each entry is `{ "channel_id": "C123…", "channel_name": "abwesenheiten", "instructions": "…" }`:
  `channel_id` is **required** (max 64 chars) and is what the match runs on, `instructions` is
  **required** (max 2000 chars), and `channel_name` is optional and **display only** — a
  workspace can rename the channel without invalidating the entry.
- **`update` replaces the entire list.** There is no add/remove verb. `get` the current value,
  append or edit the one entry, and send the **full** list back — writing a single-entry array
  silently deletes every other channel's priming.
- **What the text does:** the matching entry is injected into the static *"Anweisungen für
  diesen Channel"* block above the thread history of every companion run in that channel, on top
  of the channel name/topic the bot already reads from Slack. Use it for fixed conventions
  ("Krankmeldungen hier immer als Abwesenheit erfassen"), not for one-off asks. The first entry
  whose `channel_id` matches wins; a duplicate id is dead weight.
- **No `confirmed` gate on this group** — `update` writes immediately. Get the operator's yes,
  and read back the resulting text to them, *before* the call.
- **The companion is not this session.** It runs on its own budget: each read tool result is cut
  off at 12 000 characters (only the workflow-guidance text is exempt, being indivisible) and the
  agent loop stops after 8 steps. So a long Dienstplan or record listing legitimately comes back
  truncated in Slack — that is the cap, not a bug. Tell the operator to narrow the ask in Slack,
  or to run the listing here instead. Never promise the companion a full export.

```
manage-settings(action: "get", group: "slack")             # read the current list first
manage-settings(action: "update", group: "slack", fields: {
  "channel_instructions": [
    { "channel_id": "C0123ABCD", "channel_name": "abwesenheiten",
      "instructions": "Krankmeldungen immer als Abwesenheit auf den Mitarbeiter erfassen." },
    { "channel_id": "C0456EFGH", "channel_name": "disposition",
      "instructions": "Bei Personalbedarf zuerst die Bench prüfen, keine Verträge anlegen." }
  ]
})
```

## Answering "why can this user not see page X" (`manage-permission-set`, `resource: "access"`)

Cross-cutting — a page is gated **twice**, by the sidebar link and by the route, and neither
key is guessable from the page name. `manage-permission-set` has a third resource, **`access`**,
that derives the mapping from the product itself: `explain` reads the gate chain, `grant`
closes the gap. Never hand-map a page to a permission key from memory or from a list written
into a skill — the derived answer moves when a page moves, a written one drifts silently.

- **Name the page, not the key.** `surface` takes the operator's own wording: `"Teamkalender"`,
  `"team calendar"`, `"/team-calendar"`. German **and** English sidebar labels, the URL path and
  the route name are all indexed, so the German phrasing resolves even though the MCP session
  runs in English.
- **`explain` is read-only.** It prints the path, the route, the sidebar gate, the page gate and
  the closing `A user needs ALL of: …` line. Pass `user_id` (a User — `model_type "0-1"`,
  resolve it with `search-model`) and it additionally marks every required key ✅ granted or
  ❌ missing for that person. That is the answer to "warum sieht Melissa den Teamkalender nicht".
- **An ambiguous page name returns candidates, not a guess.** When the top two matches score
  close together — "Kalender" legitimately hits the team calendar, the Dienstplan and the
  booking calendar — the tool lists them and stops. Put that list to the operator and let them
  pick; never take the first row. Granting the wrong page's permission is a silent over-grant,
  not a retryable mistake.
- **`grant` edits a ROLE, so it is rarely a change for one person.** It writes the missing keys
  into the user's one editable (non-system) permission set. The preview states how many
  **other** users hold that set — read that line back to the operator verbatim before anyone
  confirms. To affect only this person: `duplicate` the set, `assign` the copy to them, then
  grant on the copy.
- **Two-stage as always.** `grant` previews without `confirmed: true` and writes only with it,
  after an explicit operator yes. Do not auto-confirm it because the request sounded like an
  instruction.
- **The proposed scope mirrors the set's own dominant scope**, clamped to what the permission
  offers, falling back to the narrowest granting scope — it never silently reaches for `all`.
  That is deliberate: a branch-scoped set that quietly gained an `all`-scoped permission
  becomes a cross-branch role, which is an AÜG data-isolation problem, not a UX detail. Quote
  the proposed scope per key off the preview instead of describing the grant as "read access".
- **`grant` refuses rather than improvising**, each time with the reason and the next step: the
  user holds no permission set at all (assign one first), only system sets (duplicate and
  assign the copy), or more than one editable set (the operator says which carries the grant —
  the tool lists them plus the exact `resource: "set", action: "update"` payload). A required
  key missing from the tenant's permission catalog is an error too, and nothing is written.
- **"Applied" does not mean "visible".** Effective permissions ship with the page payload, so
  the user may have to reload before the page appears. `explain` says the same thing when
  someone already holds every key but reports the page as unreachable — check for a stale
  session before hunting for a further gate.
- **`describe-permissions` prints the assignable key now**, e.g. `employees.view`, where it used
  to print the display label ("View"), and appends an `unlocks: <pages>` note per key. Take the
  key from that listing straight into a `permissions` payload; for the other direction, page →
  key, use `resource: "access", action: "explain"`.
- **A scope key needs `scope`, not just `enabled: true`.** In a hand-written `resource: "set"`
  `create`/`update` `permissions` payload, `{ "enabled": true }` with **no** `scope` key is now
  rejected for every key `describe-permissions` marks `(scope)` — the error names the key and the
  accepted values: `all` > `team` > `branch` > `own`, or `none` to deny. Only `(toggle)` keys take
  `enabled` on its own. That shape used to be accepted and answered "Permission set updated."
  while persisting a grant the resolver then treated as denied, so a payload that appeared to work
  before never actually granted anything — re-send it with the scope you meant. To deny, pass
  `enabled: false` or `scope: "none"`; both land as denied.
- **The preview does not catch a missing scope — the confirmed write does.** Without
  `confirmed: true`, `create`/`update` only counts the permission changes; the scope check runs at
  write time. The call is transactional, so one rejected key rolls back the whole batch *and* a
  rename in the same `update` — nothing is half-applied. Fix the payload and resend the entire
  call, then verify with `action: "get"`.
- **Super administrators only** — every action on this tool, including the read-only ones. If
  the operator is not a Super Admin, that *is* the answer: route the request to someone who is,
  rather than retrying or reaching for another tool.

```
manage-permission-set(resource: "access", action: "explain", surface: "Teamkalender")
manage-permission-set(resource: "access", action: "explain", surface: "Teamkalender", user_id: 42)
manage-permission-set(resource: "access", action: "grant",   surface: "Teamkalender", user_id: 42)
manage-permission-set(resource: "access", action: "grant",   surface: "Teamkalender", user_id: 42, confirmed: true)
```

## Who may read a Wissensdatenbank (`list_members` / `add_member` / `remove_member`)

Cross-cutting — access to a **Wissensdatenbank** (`KnowledgeBase`, `0-180`) is a two-layer rule:
a blanket permission scope, and below it a **member ACL** on the individual knowledge base.
Three `manage-record-action` actions on `0-180` address that ACL: **`list_members`**,
**`add_member`**, **`remove_member`**.

- **`is_public` is not how you give one audience access.** It is writable via `manage-model`
  `update` on `0-180`, but it is all-or-nothing: switching it on shows the knowledge base to
  **every** user who can open the Wissensdatenbank area at all. When the operator means "Team
  Pflege soll das lesen können", add a member — never flip `is_public` as a shortcut.
- **`list_members` is read-only and answers on the first call.** No form, no confirmation, it
  writes nothing. The *unconfirmed* `operation: "execute"` call already returns the full roster
  under the response's `## Action Preview` heading, so the tool's generic closing line "Call
  again with `confirmed: true` to execute" is boilerplate here, not a second step. Each row
  carries `memberable_type`, `memberable_id`, the `name` behind that id, and the member's
  knowledge-base `role`.
- **Read `count`, not the number of rows.** The rendered list is capped at 20 entries while
  `count` stays the true total — on a large knowledge base, reporting the visible rows as the
  whole roster understates who has access.
- **A row with `name: null` is a dangling membership** — the user or Berechtigungsgruppe behind
  that id no longer exists. It grants nobody anything; offer to remove it rather than hiding it.
- **A member is a (`memberable_type`, `memberable_id`) pair, never the membership row's own id.**
  `memberable_type` is `"user"` or `"role"`. Both write actions address the member by that same
  pair, so run `list_members` first and quote the exact pair back into the write.
- **Two different "roles" travel in one payload.** `memberable_type: "role"` means a
  **Berechtigungsgruppe** (permission set); the separate `role` field on `add_member` is the
  knowledge-base role — `viewer` (the default), `editor` or `admin`. Name which one you mean in
  the preview, or the operator confirms something other than what they asked for.
- **Resolving the id.** A User: `search-model` on `model_type: "0-1"`. A Berechtigungsgruppe has
  **no model type** — its id comes from `list_members` on a knowledge base that already grants
  it, from *Einstellungen → Berechtigungsgruppen* in the app, or from `manage-permission-set`
  `resource: "set"`, `action: "list"` (super administrators only — see the section above). Never
  guess a group id: a *nonexistent* id is rejected, but a *wrong* id is a silent over-grant.
- **The preview only checks the shape of the payload.** `memberable_type` must be `user` or
  `role` and `memberable_id` an integer ≥ 1 — but whether that id points at a real record is
  checked at **write** time, so "gibt es diesen Nutzer überhaupt" surfaces on the confirmed call,
  not on the preview. Verify the id with `search-model` / `list_members` beforehand.
- **`add_member` on someone who is already a member updates their role** instead of adding a
  second row. So "mach Melissa zur Editorin" is the same call as adding her — and an operator
  who asked to "add" a person that is already a viewer is about to change their role. Say that
  in the preview.
- **`remove_member` fails loudly on a pair that is not a member** rather than reporting success.
  Read that error as "the id was wrong", not as "already removed" — the audience the operator
  meant still has access. It is flagged destructive, so its preview also carries the generic
  "cannot be undone" warning; re-granting is a fresh `add_member`.
- **Two-stage as always**, and all three actions are gated by **`knowledge_bases.manage_members`**
  — not by edit rights on the knowledge base, and `list_members` included, because the roster IS
  the ACL. If `operation: "list"` reports the three as unavailable, that missing permission is
  the answer: route it through `manage-permission-set`, never work around it via `is_public`.

```
manage-record-action(operation: "list",    model_type: "0-180", record_id: 7)
manage-record-action(operation: "execute", model_type: "0-180", record_id: 7, action: "list_members")
manage-record-action(operation: "execute", model_type: "0-180", record_id: 7, action: "add_member",
                     data: {"memberable_type": "user", "memberable_id": 42, "role": "viewer"})
manage-record-action(operation: "execute", model_type: "0-180", record_id: 7, action: "add_member",
                     data: {"memberable_type": "user", "memberable_id": 42, "role": "viewer"}, confirmed: true)
manage-record-action(operation: "execute", model_type: "0-180", record_id: 7, action: "remove_member",
                     data: {"memberable_type": "role", "memberable_id": 3}, confirmed: true)
```

## Fetching docs on demand (`describe`, `get-tool-guidance`, `get-workflow-guidance`, `fetch_options`)

The MCP server keeps its always-loaded tool descriptions short and moves the long-form
detail behind explicit calls. Four places to look, none of them loaded until asked:

- **`action: "describe"` on the tool itself** — the per-action / per-resource parameter
  catalogue. Available on `manage-settings`, `manage-assignment-contract`,
  `manage-framework-contract`, `manage-workflow`, `manage-association`, `manage-ticket`,
  `manage-1on1-email`, `manage-meta-ads`, `query-meta-ads` and `manage-checklist`. For
  these tools the field lists are **no longer in the description** — if a skill's own
  notes don't cover the field you need, `describe` before you write, don't guess.
  On `manage-assignment-contract` the unit is a **`topic`**, not a resource — `stage-machine`,
  `multi-einsatz`, `imports`, `field-derivation`, `framework-linkage`, `surcharges`,
  `work-tasks`, `pricing-and-hours` (omit `topic` to list them). Rules that used to sit in
  that tool's description now live there, including the standalone-AÜV §5/ClientSite
  `industry_classification` requirement (`framework-linkage`), the `sync_surcharges` row shape
  and its percent-is-a-fraction scale (`surcharges`), and what `hours_arrangement`/`hours`
  mean per action (`pricing-and-hours`) — so read it from `describe`, not from the
  description. On this tool the per-parameter schema descriptions are one-liners that end in
  the matching `describe(topic: …)`; their brevity is a pointer, not a sign that a rule was
  removed.
- **`get-tool-guidance(tool_names: […])`** — long-form usage guidance for *other* tools:
  worked examples, when to ask the operator to disambiguate instead of guessing, and how
  tools compose. Seeded for `manage-model`, `search-model`, `query-model`,
  `manage-record-action`, `manage-association` and `bulk-manage-model`. Max 10 names per
  call; an unknown name comes back with the closest matches. Use it before a high-stakes
  or ambiguous call — not as a routine warm-up.
- **`get-workflow-guidance(workflow: "<slug>")`** — the sibling of `get-tool-guidance` for
  whole multi-step **workflows** instead of single tools: record resolution order, required
  fields, confirmation gates, legal duties. Call it with **no arguments** for the catalogue of
  workflows this organization has (locked ones included, with the Tarif that unlocks them), and
  check that catalogue before concluding a job has no workflow. A long workflow comes back as an
  overview plus an index of section slugs — fetch one with `section: "<slug>"` when you reach it,
  and never carry out a step whose section you have not loaded. A workflow outside the
  organization's plan answers `MODULE_LOCKED`: relay that message to the operator and stop.
  Call it **before** starting the work, not once you are stuck, and follow what it returns
  rather than improvising the flow.
- **`get-model-schema(fetch_options: […])`** — opt into extra sections: `"description"`
  (what the model is, identity-delegation notes), `"read_guidance"` / `"write_guidance"`
  (known per-model gotchas), `"default_fields"` (a shortlist for `search-model`'s
  `fields`). Omit it and the response is exactly what it always was.

The rule stays what it was: fields not in the `update` schema are silently dropped, so
confirm the schema rather than trusting memory — these three just make that cheap.

## A tool is missing, or answers `MODULE_LOCKED` (Module & Tarife)

alluvo is sold in **Module** — Basis, Vertrieb, Recruiting, Disposition & Verträge,
Personal & Zeit, Lohn, Faktura, Service & Inbox, KI & Automatisierung, Fuhrpark — and
each tenant holds a Tarif (Free, Starter, Professional, Enterprise) per module. The MCP
server loads its tools, prompts and resources **per tenant**: anything owned by an app
the tenant has not unlocked is absent from the tool list altogether. A tool named in a
skill can therefore legitimately not exist in this tenant — that is a Tarif boundary,
not an outage and not a bug.

- Calling such a name anyway returns a JSON-RPC error whose message begins with
  **`MODULE_LOCKED:`** and whose `error.data.code` is `MODULE_LOCKED`. The message is
  German by design and already names the tool, its module, the required Tarif, the
  tenant's current Tarif and a link to start the Testphase — **relay it to the operator
  as it is**. Do not rephrase it, do not retry the call, do not guess a different tool.
- A misspelled or genuinely unknown name still comes back as the plain "not found".
  Only a real catalogue entry this tenant may not use answers `MODULE_LOCKED`.
- To check the boundary instead of hitting it: `manage-apps` `action: "modules"`
  (read-only, never writes) lists every module with the tenant's Tarif, whether it is
  running as a Testphase and when that ends, and the apps it owns. `get-tool-guidance`
  additionally appends a **"Your Modules"** table — Tarif per module plus which of its
  apps are currently locked. Both tools are core, so both are always available.
- Never route around a locked module. Name the module, state the Tarif the message asks
  for, mention the Testphase, and offer whatever part of the job the tenant's own tools
  can still do.

Which module owns the gated tools the catalog below uses:

| Module | Tools |
|---|---|
| Disposition & Verträge | `manage-shift-schedule`, `client-portal-insights`, `checkout-session`, `get-booking-availability`, `manage-booking-availability` |
| Vertrieb | `manage-outreach-enrollment`, `manage-campaign-landing-page` |
| Recruiting | `manage-meta-ads`, `query-meta-ads`, `get-profile` |
| Service & Inbox | `manage-ticket`, `get-attachment` |
| KI & Automatisierung | `manage-workflow`, `manage-automation-agent`, `manage-agent-prompt`, `manage-ai-preferences` |

Tools owned by an app on the **Basis** module (`get-issues-overview`,
`manage-duplicates`, `query-analytics`, `manage-analytics-goal`, `get-news-readership`)
are never Tarif-locked, but they can still be absent when the app itself is switched off
for the tenant — `manage-apps` `action: "list"` shows that state. Everything else the
catalog uses is core and always loads.

## Catalog (jobs-to-be-done)

Three entries below are marked **guidance served by the assistant** — `bench-check`,
`profilvertrieb` and `manage-contract-lifecycle` ship only their trigger phrases; the steps come
from `get-workflow-guidance` (see "Fetching docs on demand"). Activating one of them, or being
routed to it from another skill, means calling that tool with the skill's name first. The
guidance is served live, so it is current with the deploy and follows the organization's plan.

### Management (overview & coordination)
- `head-of-sales` — Sales overview, forecast, pipeline review, BDR coordination.
- `head-of-disposition` — Utilization, expiring assignments, open Bedarfe, Disponent coordination.

### Sales & client acquisition (BDR)
- `profilvertrieb` — Bench → placement: find companies and actively pitch profiles.
  *(guidance served by the assistant — `get-workflow-guidance`)*
- `prospect-companies` — Find and qualify target companies for an employee.
- `enroll-outreach` — Enroll qualified companies in Outreach sequences.
- `define-icp` — Define Ideal Customer Profiles per segment.
- `log-company-signal` — Record hiring / expansion / funding Signals.
- `account-research` — Internal dossier on a company/contact from alluvo data.
- `call-prep` — Prepare for an appointment/call using CRM history.
- `call-summary` — Debrief a call: note/call + tasks + follow-up email.

### My day
- `daily-briefing` — Daily overview: appointments, tasks, replies, priorities.

### Disposition & placement
- `bench-check` — Who is verleihfrei (now / soon), sorted by urgency.
  *(guidance served by the assistant — `get-workflow-guidance`)*
- `match-bench-to-clients` — Match Bench to clients with Rahmenvertrag, draft Einsatzverträge.
- `onboard-new-employee` — Completeness check + nearby opportunities + acquisition tasks;
  also the digitale Personalfragebogen (Gastlink verschicken, eingereichte Stammdaten
  übernehmen) and the Fuhrpark data behind the `vehicle` requirement (Fahrzeug,
  Kilometerstand inkl. Kilometerstand-Anfrage an den Fahrer (Tacho-Foto optional, per
  Tenant-Einstellung `fleet.require_mileage_photo` erzwingbar), Tankkarte,
  Prüfungen und Werkstatt-Services (`0-69`, Frist nach Datum ODER Kilometern),
  Leasing-/Miet-/Kaufdaten, Fahrzeugzuweisung als Zeitraum-Datensatz `0-432`,
  Schadensmeldung inkl. Versicherungs-/Abschluss-Actions).
- `build-dienstplan` — Create/adjust shifts with ArbZG guardrails; publishing a month out of
  Entwurf (`manage-shift-schedule` `publish`, step 7); also the Umbesetzung
  (move an Einsatz or single Schichten to another employee) and, where the tenant requires
  approval for employee shift changes, releasing or discarding the Vorschlag an employee parked
  on a live Dienstplan (step 6b-a — not the same thing as `approve-stundenfreigabe`).
- `record-absence` — Record Krankmeldung / vacation / AU.
- `approve-stundenfreigabe` — Review and approve Stundenfreigaben. Also the reimbursement side:
  reviewing Spesen/Auslagen (`0-20`) and filing a Beleg **for** an employee (`submit_beleg` on
  `0-2`, Base64 over MCP) — that one opens a Draft Auslage the extraction fills in afterwards —
  plus the **Sammel-Reisekostenabrechnung** downstream of approval (`generate-period-statements`,
  the one index action on `0-20`), and the **upload/extraction queue** behind all of those
  (`0-29`, read-only: a stuck or failed upload, the `content_sha256` duplicate check, and the
  `discard_upload` action).

### Contracts & demand
- `intake-personalbedarf` — Fully capture a client's Personalbedarf.
- `manage-contract-lifecycle` — Rahmenvertrag + Einsatzvertrag from creation to sign-off, and
  ending them: "Vertrag beenden" / "Einsatz beenden" (dated), Storno, verloren. Also the
  tenant's own invoicing bank accounts ("auf welches Konto zahlt der Kunde") — the account
  records are MCP-writable, picking one on a contract is web-app-only.
  *(guidance served by the assistant — `get-workflow-guidance`)*

### Data & CRM
- `triage-data-quality` — Review and batch-triage Datenqualität issues; also the
  Rollenkatalog (Rollen ohne Gruppe/Level/Fachweiterbildung — unklassifizierte Rollen
  kosten Kandidaten im Matching).
- `merge-duplicate-companies` — Find, review, and merge Dubletten (Firmen **und** Kontakte —
  the only two mergeable record types), including the follow-up to a POSSIBLE DUPLICATE
  warning shown when a person was created.
- `enrich-contacts-from-activities` — Enrich contacts from emails/calls/signatures. Also
  records a WhatsApp-Einwilligung given outside alluvo (`record-whatsapp-consent`).
- `clean-inbox` — Triage a shared company inbox: close with evidence, task the rest.
  Also its settings: Weiterleitungsziele, Geschäftszeiten, following/unfollowing the
  inbox's arrival notifications plus the per-type channel preferences behind them
  (in-app / E-Mail / Push / Slack), and the Vapi phone assistant's own instructions
  (what it says to callers, plus the re-sync after a Geschäftszeiten change).
  Also **opening** a conversation from alluvo (`manage-ticket` `create`): an email to an
  existing Kontakt out of an inbox, or a message to a Mitarbeiter in their Self-Service-App
  (in-app + Push, no mail).

### Marketing & recruiting ads
- `manage-meta-ads` — Meta (Facebook/Instagram) recruiting campaigns: create/audit
  campaigns, creatives, lead forms, conversion events, performance (CPL). Also the
  **lead→Candidate/Contact mapping** that decides whether a submitted lead becomes a
  record at all (leads without an active mapping are stored as `skipped` and can be
  reprocessed later).

### Automation
- `build-automation-agent` — build/adjust an AI automation agent: either scheduled (a
  periodic report delivered by email or task) or **deployed on an Inbox** so it reacts to
  inbound tickets (Posteingang-Agenten: deploy/undeploy, step whitelist, caps) — no login
  needed either way. What an agent may do is its `capabilities` map (`execute` = runs as a
  tool unsupervised, `propose` = approval-gated step on an inbox run; `describe-tools` lists
  every key — `enabled_tools` is the retired predecessor). Also the home of **what the agents are told**: the system `blocks`
  selection (Markenstimme, ICP, Standort der Agentur, …), tenant-authored **Bausteine**
  (`InstructionBlock`, `0-442` — create, attach, order), and the tenant-owned sections of the
  Bewerber-WhatsApp-Agent's prompt (eight sections; `manage-settings`, group
  `candidate_flow_prompts`, whose `update` needs `confirmed: true`). The prompt layers of
  **conversational and task** agents belong to a second tool, `manage-agent-prompt`
  (`get` renders the composed prompt section by section; writes on a conversational agent
  return a prompt diff unless `confirmed: true`) — same skill. Both agent tools see
  **tenant-owned** Bausteine only; an operator's **personal instruction** on one agent
  (`manage-ai-preferences` — `get` / `set` / `list`, optional `agent`, default
  `activity-takeover`) is a separate, private layer they deliberately cannot touch. `Agent` (`0-400`) is readable
  over `query-model`/`get-model`/`search-model` and `manage-model` `update` writes exactly
  three fields — `name`, `display_name`, `tags`; everything about behaviour, structure or
  lifecycle is refused there with a pointer to the owning tool, and `create` is refused
  outright. `AgentRun` (`0-441`) stays read-only. Agents can also carry **Tags** from a
  tenant-wide vocabulary (`Tag`, `0-443` — full read+write via the generic model tools;
  attach with `manage-agent-prompt`'s `set-tags` on a conversational or task agent, with
  `manage-automation-agent`'s `tags` on an automation agent, or via `manage-model` `update`
  — each a full replacement by name that creates unknown ones). An agent is one of
  **twelve** taggable record types — see *Tagging a record* above for the full list and
  the rules that apply to all of them.

## Quick decision guide
- "How is sales going? / Forecast / Pipeline review" → `head-of-sales`.
- "How is utilization? / Team view Dispo" → `head-of-disposition`.
- "What's on today?" → `daily-briefing`.
- "Who has no assignment?" → `bench-check` → then `match-bench-to-clients` or `profilvertrieb`.
- "Before a call" → `account-research` → `call-prep`; afterwards `call-summary`.
- "New employee" → `onboard-new-employee`.
- "Stammdaten anfordern / Personalfragebogen schicken / digitalen Personalfragebogen senden /
  Fragebogen ist ausgefüllt, Stammdaten übernehmen" → `onboard-new-employee` (step 2a) — the
  `request-employee-master-data` action on Employee/Candidate/Contact, then
  `apply-employee-master-data` on the submission (`0-429`), **not** a manual data-entry
  walkthrough. Two things to say up front: sending again to someone who already finished
  starts a *new, empty* questionnaire rather than resending the old link, and the submitted
  answers never come over MCP — only status and *which* fields were answered
  (`filled_keys`: key names, never values).
- "Mitarbeiter kann sich nicht anmelden / bekommt keinen Code / Passwort vergessen" →
  `onboard-new-employee` (step 5). **Employee login, not the Kundenportal** — don't confuse it
  with the PortalMembership case further down. Login is OTP by default for every account; there
  is no per-user switch that can suppress the code, so the only invite-shaped cause is "has no
  linked user account yet". A **password is self-service** — the employee sets or resets one
  themselves from the branded login ("Passwort setzen") or *Einstellungen → Passwort*, each
  gated by a fresh emailed code. Never promise an operator-side password reset, and never write
  to a User's authentication fields.
- "Client reported a Bedarf" → `intake-personalbedarf` → `manage-contract-lifecycle`.
- "Wer hat die Einsatzmitteilung noch nicht bestätigt / offene Lesebestätigungen" →
  `head-of-disposition` (the work list); the rules behind it live in `manage-contract-lifecycle`.
- "Win new companies" → `define-icp` → `prospect-companies` → `enroll-outreach`.
- "Clean up CRM / data" → `triage-data-quality`, `merge-duplicate-companies`, `enrich-contacts-from-activities`.
- "Wer darf die Wissensdatenbank sehen / gib Team X Zugriff auf die Wissensdatenbank /
  jemandem den Zugriff wieder entziehen" → the knowledge-base member section above
  (`manage-record-action` on `0-180`: `list_members`, then `add_member` / `remove_member`,
  both two-stage). Read the roster first — the write actions address a member by the
  (`memberable_type`, `memberable_id`) pair that `list_members` prints. Never answer this by
  switching `is_public` on: that opens the Wissensdatenbank to everyone, not to the one team
  the operator named. For a *page* the user cannot reach at all, it is the permission question
  instead → `manage-permission-set` `resource: "access"`.
- "Darf ich den per WhatsApp anschreiben / WhatsApp-Einwilligung erfassen" →
  `enrich-contacts-from-activities`. Reading the answer is a `search-model` on the Kontakt
  (`0-105`) naming the `whatsapp_*` fields; recording a consent given outside alluvo is the
  `record-whatsapp-consent` action, and it is refused outright once the person has opted out.
- "Schwerpunkte / Fachbereiche pflegen" splits by side: a **person's** No-Go ("Frau X macht keine
  Palliativpflege", "No-Go hinterlegen") → `onboard-new-employee` — it is stored on their Contact
  (`0-105`), never on the Employee; the **Abteilung's** Schwerpunkte and the `FocusArea` (`0-369`)
  catalogue itself → `intake-personalbedarf`. A No-Go only hides someone in the **Kundenportal**;
  Matching, Dienstplan and AÜV are unaffected by design (`→ match-bench-to-clients`).
- "Rollenkatalog / Rollen-Hierarchie pflegen (Gruppe + Level + Fachweiterbildung), Rollen ohne Level oder Fachweiterbildung finden" → `triage-data-quality`.
- "Einen Mitarbeiter oder Kunden proaktiv anschreiben / ein Gespräch eröffnen" → the channel
  decides the skill. Mitarbeiter in der App (in-app + Push, kein Mailversand) →
  `onboard-new-employee` (step 7) for a Rückfrage during onboarding, otherwise `clean-inbox`;
  an existing **Kontakt** by email out of an inbox → `clean-inbox`. Both are
  `manage-ticket` `action: "create"` (`mode: "employee_app"` / `"email"`, preview → `confirm`)
  and open a real ticket the answer comes back into. **Acquisition mail is not this:** a
  sequence → `enroll-outreach`, a single pitch with profile block and tracking →
  `profilvertrieb` (`manage-1on1-email`).
- "Clean up / triage the inbox" → `clean-inbox`; same skill for "Geschäftszeiten der Inbox
  ändern" / "Weiterleitungsziel hinzufügen" / "Inbox folgen bzw. stummschalten" / "Ticket in
  eine andere Inbox verschieben" (`manage-ticket` `move_to_inbox` — a misrouted ticket is
  moved, not closed and recreated).
- "Ticket löschen / als Spam melden / den Newsletter-Absender loswerden" → `clean-inbox`
  (`manage-ticket` `delete` / `bulk_delete`, optionally `mark_as_spam: true`). On a Gmail
  inbox the mailbox follows the ticket: a delete trashes the thread, `mark_as_spam` reports
  it **instead of** trashing, and closing a ticket archives it. Neither `delete` nor
  `bulk_delete` previews — the operator confirms first.
- "Buchungslink anlegen / Terminlink verschicken / meinen Kalender-Link teilen / Buchungslink
  aktivieren bzw. deaktivieren / Buchungsseite auf der Kundenwebsite einbinden" → `clean-inbox`
  (`MeetingBookingLink`, `0-444` — full read+write over the generic model tools, plus the four
  record actions `copy-booking-link`, `copy-booking-embed-snippet`, `activate-booking-link`,
  `deactivate-booking-link`). A link belongs to **one host**: a non-admin may only create one
  for themselves, and `user_id` cannot be changed afterwards — handing a link over is a new
  link, not an edit.
- "Mein Buchungslink zeigt keine freien Termine / der Kunde kann nichts buchen" → `clean-inbox`.
  Four states leave an *active* link unbookable, and none of them switch it off: the host's
  Google-Verknüpfung is gone or unreadable, the host's account is deactivated, or the host's
  availability carries the away toggle (that last one renders an empty calendar, which reads as
  "ausgebucht"). Check those before touching the link's own settings — activating a link at all
  requires a live Google calendar for the host, so "geht nicht" there is a calendar problem,
  never a retry.
- "Wer hat gebucht, aber nicht bestätigt / offene Reservierungen / unbestätigte Termine aus dem
  Buchungslink" → `clean-inbox` (`MeetingBookingRequest`, `0-445`, **read-only** — written only
  by the booking service, so `manage-model` refuses create/update). `query-model` with
  `confirmed_at is_null` plus `expires_at gt <jetzt>`. An expired reservation is pruned by a
  scheduled job, so an empty result means "gerade keine offenen", never "es hat niemand gebucht".
- "Ändern, was der Telefonassistent am Telefon sagt / Anweisungen für den Telefon-Assistenten /
  Telefonassistent neu synchronisieren / was steht aktuell drin?" → `clean-inbox` (the
  `update-vapi-instructions` action on the inbox's phone channel — its unconfirmed call is
  also the read path for the current instructions), **not** `build-automation-agent`.
- "Shift planning / absence / hours" → `build-dienstplan`, `record-absence`, `approve-stundenfreigabe`.
- "Mitarbeiter sieht keine Stundenfreigabe / Altdaten aus dem Vorsystem ausblenden /
  Go-Live-Datum eines Mitarbeiters" → `approve-stundenfreigabe` (what the cutoff does);
  `onboard-new-employee` when setting it as part of a migration wave. Beim Go-Live gilt
  inzwischen ein Unterschied: **Abrechnungszeiträume vor dem Go-Live werden gar nicht mehr
  angelegt** (auch deine `0-426`-Zahl sieht sie nicht mehr — Stunden davor lagen im Vorsystem),
  während Einsatzmitteilungen und AUs weiterhin nur *ausgeblendet* sind. "AU überfällig, aber
  der Mitarbeiter sieht in der App nichts zum Hochladen" → `record-absence` (pre-go-live
  AUs are invisible to the employee, visible to you).
- "Der Zeitraum fehlt komplett / die Woche gibt es im Backend gar nicht / da klafft eine Lücke
  in den Wochen" → `approve-stundenfreigabe`. Ein Zeitraum entsteht nur mit einem **freigebbaren
  Tag** — eine wirksame Schicht, für die niemand krankgemeldet ist, oder ein abgeschlossener
  Zeiteintrag — und nur innerhalb des Einsatzes und ab
  dem Go-Live. **"Kein Zeitraum" ist eine gültige Antwort ("nichts abzurechnen"), kein
  Datenfehler**, und ein toter Einsatz (storniert, nie unterschrieben) meldet dadurch keine
  Wochen mehr. Nie "den Zeitraum neu anlegen" zusagen: er ist abgeleitet und entsteht von selbst,
  sobald eine Schicht oder eine Zeit darin liegt. Ein Zeitraum, der *bestand* und leer wurde, liegt
  im Papierkorb — siehe den eigenen Punkt weiter unten.
- "**Kunde** sieht keine Dienstpläne / findet die Stundenfreigabe nicht im Kundenportal / 404
  im Portal" → `approve-stundenfreigabe`. Two separate gates live there: the surface is
  activated per company (the 404 is *not* a missing role), and portal access itself needs an
  invitation. Check the company activation before touching anyone's roles — and read who
  actually has access off **PortalMembership (`0-430`)** (`status` + `portal_roles_label`)
  rather than off the Kontakte list, which shows every linked contact including those with no
  login. `0-430`
  filters directly on `company_id`, `contact_id`, `status` and `grants.role`, so "wer hat bei
  Firma X Zugang" and "wer ist Administrator" are one query. For an activated
  client there is no second entry to find — the menu item is called
  **"Dienstpläne/Stundenfreigabe"** and that hub *is* the Freigabe-Oberfläche.
- "Kunde kann den Vertrag nicht unterschreiben / hat jemand anderen als Unterzeichner benannt /
  Rollenanfrage offen" → `manage-contract-lifecycle`. Naming a signer who holds no signing right
  raises a **PortalRoleRequest (`0-434`)** rather than a 403; it grants nothing until an
  administrator approves it, and approval also hands the contract over (the approved person
  becomes **primary** recipient and gets the signing mail, which changes the name the AÜV prints
  as customer signer). Read the queue with `query-model` on `0-434` (`status` = `pending`), decide
  it with `approve-portal-role-request` / `reject-portal-role-request` via `manage-record-action`.
  A customer *administrator* who names a signer decides on the spot, so there may be no pending
  request to find. `→ approve-stundenfreigabe` for how the granted role sits in the access model.
- "Ansprechpartner lässt sich nicht löschen / Kontakt-Dublette lässt sich nicht zusammenführen"
  → **two different answers, don't conflate them.** A *deletion* is still **refused on purpose**
  while a live contract names the person; the message lists every blocker (`RV #72`, `AÜV #685`,
  `Einsatz #2040`) — read them out instead of reporting a failed delete, assign a replacement on
  each named record, then repeat (`→ manage-contract-lifecycle` for the recipient writes). A
  *merge*, however, is **not** blocked by those references: it moves the Empfänger rows and the
  Einsatz-Ansprechpartner onto the surviving Contact before deleting the duplicate. If the two
  records are the same person, merge instead of re-pointing by hand — that is the case a merge
  exists for (`→ merge-duplicate-companies`; note the primary recipient may be promoted to
  somebody else afterwards). A contract that already lost its recipient (only possible before
  2026-08) can neither be sent nor signed and prints a different signer — that is the
  `dangling_contract_recipient` finding, `→ triage-data-quality`.
- "Kontakt als Ansprechpartner im Portal listen / von der Ansprechpartner-Liste nehmen / 'im
  Portal freischalten'" → `approve-stundenfreigabe`. **There is no listing step any more** —
  the portal's Kontakte list shows every contact linked to the company, and the actions
  `list-as-portal-contact-person` / `unlist-as-portal-contact-person` no longer exist. Listing
  someone is therefore the plain association write (`manage-association` attach/detach,
  Contact `0-105` ↔ Company `0-3`, label `Ansprechpartner`), which creates or deletes the
  membership (`0-430`). **The link is not access** — it grants no login and no role. If the
  operator actually means "soll sich anmelden können", that is `send-portal-invitation` /
  `assign-portal-roles` instead — ask which one they mean before writing.
- "Portalzugang entziehen / der soll sich nicht mehr anmelden können / Ansprechpartner
  offboarden / die alten Viewer-Zugänge aufräumen" → `approve-stundenfreigabe`. There is a
  dedicated action for this: **`revoke-portal-access` on PortalMembership (`0-430`)** via
  `manage-record-action`, no parameters, two-stage. It deletes the membership's **role grants
  only** — the contact, the membership and the person's role-less **placement** in the
  Organigramm survive — and it works for a contact who never signed in, which
  `assign-portal-roles` does not. Never improvise it as an empty `roles` list (that wipes the
  placement too) and do not reach for `archive` (that also takes the person off the customer's
  Kontakte list). It is **hidden** on a membership holding no role grant, and **unavailable**
  for the company's last active `administrator` — a guard that binds an internal operator here,
  unlike the `portal_access_active` switch. Whole cohorts go through `operation: "execute_bulk"`
  with up to 100 `record_ids`; its preview is the only place the per-row refusals show, so never
  skip straight to `confirmed: true`.
- "Ansprechpartner ist aus der Kontakte-Liste verschwunden / der Kunde findet ihn nicht mehr /
  'den haben wir archiviert'" → `approve-stundenfreigabe`. The customer can **archive** a
  membership themselves, which takes the person off their Kontakte list *and* disables their
  access. Your read still returns the row (see the archiving section above), so before telling
  anyone the contact does not exist, request `archived_at` on `0-430` — "archiviert" and "gibt
  es nicht" are different answers. Restoring is two steps, not one: `unarchive` returns them to
  the list, and the login has to be re-granted separately.
- "Ansprechpartner wurde eingeladen, bekommt aber keinen Anmeldecode / 'Code wurde gesendet',
  es kommt aber nichts an" → `approve-stundenfreigabe`. Usually a **deactivated** membership:
  a disabled one issues no code while the portal still shows the "Code gesendet" screen. Read
  `status` on **PortalMembership (`0-430`)**; re-running `send-portal-invitation` activates the
  membership as part of sending, so it re-enables *and* re-invites in one call — say so before
  running it on someone who was locked out on purpose.
- "Portal-Rolle lässt sich nicht vergeben / 'Ein Ansprechpartner hat genau eine Position' /
  'Diese Person ist bereits zugeordnet' / Rollenanfrage lässt sich nicht genehmigen" →
  `approve-stundenfreigabe`. Not a permission problem and not a bug: **a contact holds exactly one
  position per company** — company-wide, one Einsatzbetrieb, or some of its Abteilungen — and all
  their roles apply there. `send-portal-invitation` / `assign-portal-roles` therefore ask for the
  position once (`position_client_site_id` + optional `position_department_ids`) plus a flat
  `roles` list, so `position_conflict` is no longer reachable from them;
  `position_conflict_existing` still is elsewhere — it means you tried to *add* a role somewhere
  the person does not already sit (the `approve-portal-role-request` path,
  `→ manage-contract-lifecycle`). Read the current position off **`0-430`** (`portal_scope_label`)
  before rewriting, and remember the two role actions are a full replace — moving somebody means
  sending the new position plus **every** role they should keep, in one call. An Einsatzbetrieb
  with an empty `roles` list is a placement in the Organigramm, not access.
- "Kunde sieht Minusstunden / 'gemäß Zeiterfassung' stimmt nicht / Kunde sieht 0h im Portal" →
  `approve-stundenfreigabe` (the hub compares the whole tracked day, so a minus is a real
  shortfall — not a display artefact).
- "Mitarbeiter kann die Stunden nicht freigeben / 'Tage sind noch nicht abgeschlossen' /
  'Pausenzeit nachträglich geändert' / Tag abschließen bzw. Abschluss zurückziehen / Mitarbeiter
  kann einen erfassten Tag nicht mehr ändern" → `approve-stundenfreigabe` (both release-blocking
  reasons and the withdraw path). Auch "der Mitarbeiter hat den Tag nie abgeschlossen / Tag
  stellvertretend abschließen" gehört dorthin: `close_tracked_day_for_employee` auf `0-427` ist
  seit Kurzem eine **per MCP ausführbare** Aktion, mit denselben § 4- und Abweichungs-Prüfungen
  wie in der Mitarbeiter-App. Das **Zurückziehen** eines Abschlusses bleibt dagegen
  Mitarbeiter-App — nie zusagen, dass du das rückgängig machen kannst — und ist auch dort gesperrt,
  sobald ein Operator den Tag in der Stundenkontrolle freigegeben hat oder der Zeitraum die offenen
  Status verlassen hat (`PendingEmployee`, Klärung, freigegeben, abgerechnet). Same skill for "die
  Schicht läuft noch / der heutige Tag lässt
  sich nicht freigeben" — a day the employee has **closed** is releasable even before its planned
  end, so that is a Tagesabschluss question, not a "warte bis Feierabend" one. But
  "Slack-Meldung/Aufgabe, **wenn** ein Mitarbeiter den Tag abschließt bzw. bei einem
  Pausenverstoß" → `build-automation-agent` (workflow trigger on `0-422`).
- Check the *period* before either of those, though: "Läuft noch — noch nichts zu tun" /
  "ab wann kann der Mitarbeiter freigeben" / "bis wann muss er freigeben" →
  `approve-stundenfreigabe`. A still-running Zeitraum is shown as not-yet-releasable on purpose,
  so it is neither a Tagesabschluss nor a Go-Live nor a Freischaltungsproblem. Same skill for the
  greyed-out preview below it — "Danach: <Zeitraum>" / "Kommt als Nächstes" / "Freigabe ab TT.MM."
  / "der Zeitraum lässt sich nicht anklicken": a projection of the next period, no Frist, no
  Aufgabe, nichts zu tun.
- "Wo sehe ich die Stundennachweise / den unterschriebenen Tätigkeitsnachweis / den Zeitraum im
  Backend" → `approve-stundenfreigabe`. There is an operator-facing **Stundennachweise** list (HR &
  Payroll, next to Stundenklärung). `0-426` (Zeitraum), `0-427` (Tag) and `0-435` (Freigabe) are
  MCP-**readable**; `0-428` (Korrektur) and `0-436` (Tages-Snapshot) are not. Nothing about a
  Zeitraum is writable through `manage-model` — never promise to update one; the only writes on a
  Zeitraum are `approve_by_operator` and `revoke_approval`, via `manage-record-action` (below), and
  the only write on a Freigabe (`0-435`) is `correct_signer`. A missing menu entry
  is the `timesheets.view` permission, not a rollout gap.
- "Notiz an den Stundennachweis / Vermerk am Zeitraum / wo halte ich fest, was mit dem Kunden
  besprochen wurde" → `approve-stundenfreigabe`. A **note** now attaches to the Zeitraum itself:
  `manage-activity` with `activity_type: note` and `subject_type: "0-426"` (two-stage, gated on
  `view` of the record), readable back via `get-timeline` on the same subject. Do **not** fall back
  to the linked Kontakt for a remark that belongs to the period — that detour is obsolete. Notes are
  the only activity type that widened: `call` and `meeting` remain on `0-105` / `0-3` / `0-30` /
  `0-31`. The note subject list is derived from the models that carry notes, so other record types
  join it without a plugin change — `list-model-types` confirms an id, and a rejected `subject_type`
  lists the accepted ones.
- "Der Kunde hat nur einen Teil der Woche gezeichnet / wer hat unterschrieben / der Kunde hat zu
  früh unterschrieben / Freigabe zurücknehmen" → `approve-stundenfreigabe`. Eine Kundenfreigabe ist
  ein **Vorgang** (`0-435`), kein Häkchen am Zeitraum: ein Zeitraum kann mehrere tragen, nur die
  freigegebenen **Tage** sind gesperrt (pro Einsatz), eine noch laufende Schicht ist nicht
  freigebbar, und Fristablauf überschreibt keine menschliche Unterschrift mehr. Rund um die
  Kundenfreigabe ist `revoke_release` auf `0-427` die per MCP ausführbare Schreib-Aktion für **einen
  Tag** (Pflichtbegründung, nur solange der Zeitraum `open` ist); `0-427` trägt
  daneben `close_tracked_day_for_employee` für den fehlenden Tagesabschluss (siehe oben).
- "Der falsche Ansprechpartner steht unter der Unterschrift / der Mitarbeiter hat auf dem Gerät den
  falschen Ansprechpartner ausgewählt / Unterzeichner korrigieren" → `approve-stundenfreigabe`.
  Das ist **keine** Rücknahme: `correct_signer` auf der Freigabe (`0-435`, per
  `manage-record-action`, Pflichtbegründung) verschiebt nur die Zuordnung auf einen Kontakt
  **desselben Entleihers** und lässt Unterschrift, Zeitpunkt, Kanal und die gezeichneten Tage
  unangetastet; den Tätigkeitsnachweis rendert die Aktion selbst neu. Nicht verfügbar bei einer
  Fristablauf-Freigabe (`auto_approved`) — dort hat niemand unterschrieben. Wurde dagegen die
  falsche Person überhaupt um eine Unterschrift gebeten, ist es `revoke_release` bzw.
  `revoke_approval`.
- "Der Kunde unterschreibt nicht / wir haben die Stunden telefonisch abgestimmt / können wir selbst
  freigeben" bzw. "die falsche Person hat unterschrieben / die Woche war zu früh freigegeben /
  Freigabe des Zeitraums zurücknehmen" → `approve-stundenfreigabe`. Der **Zeitraum** (`0-426`) trägt
  zwei operator-eigene Aktionen, beide über `manage-record-action`, beide zweistufig:
  **`approve_by_operator`** ("Ohne Kunden freigeben", nur `open`, jeder Tag muss
  abgeschlossen sein — sonst nennt die Absage die blockierenden Tage; `client_note` steht auf dem
  Tätigkeitsnachweis, `internal_note` nie) und **`revoke_approval`** ("Freigabe zurücknehmen", nur
  `Approved`, Pflichtbegründung, zurück nach `open` mit neuer Frist — `submitted_to_client_at`
  bleibt dabei stehen). Zwei Fallen: die
  deutsche Bezeichnung "Freigabe zurücknehmen" tragen `revoke_approval` (Woche, `Approved`) **und**
  `revoke_release` (Tag, offene Woche) — nachfragen, welche gemeint ist; und `approve_by_operator`
  landet **nicht immer** auf `Approved` — weicht die vereinbarte von der erfassten Zeit ab, geht der
  Zeitraum nach `PendingEmployee`, also den Status zurücklesen, bevor man "freigegeben" meldet. Eine
  Freigabe durch den Verleiher ist ausdrücklich **keine** Kundenbestätigung (Kanal
  `operator_release`; der Tätigkeitsnachweis hält direkt **unter der Unterschriftenzeile** fest,
  dass keine Bestätigung des Entleihers vorliegt — nicht mehr in einem Absatz über den
  Unterschriften) — nie als "der Kunde hat freigegeben" berichten.
- "Der Zeitraum wird nicht fertig / ein offener Tag am Ende blockiert alles / kein
  Tätigkeitsnachweis, obwohl der Kunde unterschrieben hat / offene Tage in die Folgeperiode
  schieben / die unterschriebenen Tage sollen jetzt schon abgerechnet werden" →
  `approve-stundenfreigabe`. Der Zeitraum trägt dafür die Aktion
  **`push_open_days_to_next_period`** ("Offene Tage in die Folgeperiode schieben"): sie verschiebt
  die Grenze zwischen beiden Perioden, danach ist die verkürzte Periode vollständig freigegeben und
  läuft durch dieselbe Kaskade wie eine Schlussunterschrift. Sie ist **nicht MCP-ausführbar** — nur
  erklären und an den Datensatz verweisen. Sie erscheint, solange der Zeitraum **offen** ist, sobald
  **ein** Tag freigegeben ist und die offenen Tage zusammenhängend am Periodenende liegen — **auch
  mitten in der laufenden Periode**; das frühere „erst wenn der letzte Dienst der Periode vorbei
  ist"-Gate ist weg, nie mehr auf das Wochenende vertrösten. Die Folgeperiode blockiert nicht mehr:
  sie entscheidet nur, ob die Tage in sie hineinwandern oder eine eigene Periode bilden.

- "Welche Status hat ein Stundennachweis / warum findet mein Filter auf `pending_client` nichts" →
  `approve-stundenfreigabe`. `TimesheetStatus` (`0-426`) kennt **fünf** Werte: `open` (Offen),
  `pending_employee` (Wartet auf Mitarbeiter), `mediation` (In Klärung), `approved` (Freigegeben),
  `invoiced` (Abgerechnet).
  `closed` ("Ohne Einsatz") ist wieder weg, ebenso `upcoming`, `pending_client`, `disputed`,
  `escalated`, `mediating` und
  `draft` — ein `query-model` darauf liefert eine leere Menge, keine Fehlermeldung.
  `open` deckt **zwei** Situationen ab ("noch nichts vorgelegt" und "beim Kunden, Frist läuft"); die
  Unterscheidung steht im Stempel **`submitted_to_client_at`**, nicht im Status. Daneben stehen drei
  abgeleitete Lesarten: die materialisierte **`lifecycle_phase`** (`upcoming` ▸ `in_approval` ▸
  `approved` ▸ `invoiced` — vier Stationen; `upcoming` ist eine Phase, nie ein Status), die nie
  gespeicherte
  **Wartepartei** (`client` / `time_tracking` / `employee` / `mediation` / `nobody` — ein `open`
  Zeitraum ohne freigebbaren Tag wartet auf die **Zeiterfassung**, nicht auf den Kunden) und der
  **Freigabefortschritt** (`none` / `partial` / `complete`). Nach einer Teilfreigabe kann die
  Wartepartei "Kunde (teilweise)" sein.
- "Der Zeitraum ist weg / warum finde ich die Woche nicht in der Liste" →
  `approve-stundenfreigabe`. **Der Zeitraum ist nicht geschlossen, er ist gelöscht — und er kommt
  von selbst zurück.** Sobald kein
  einziger Tag des Zeitraums von irgendwem freigegeben werden kann — alle Schichten weg, oder
  **jeder** geplante Tag durch eine gemeldete Krankmeldung gedeckt (`→ record-absence`) — wird er
  gar nicht erst angelegt, und ein bestehender wird **in den Papierkorb verschoben** (soft-deleted).
  Damit ist er aus Liste, Board, Warteschlangen, Fristen und Kundenportal gleichzeitig heraus.
  Auffindbar mit `search-model` auf `0-426` und `trashed: "only"`. Der Weg zurück ist **derselbe
  Datensatz**: eine Schicht wieder einplanen oder die Krankmeldung ablehnen, dann stellt alluvo ihn
  mit Id, Tagen und Historie wieder her — nie "Zeitraum wiederherstellen" (`delete-model` mit
  `action: "restore"`) als Lösung anbieten. Nie an `soll_minutes
  = 0` erkennen: ein komplett krankgeschriebener Zeitraum **behält sein Soll** (23,10 h Soll gegen
  0,00 h Ist ist genau dieser Fall). Ein Zeitraum mit Bestätigung, Freigabe,
  bereits vom Kunden signiertem Tag oder offener Korrektur wird **nie** gelöscht, ebenso keiner, der
  nicht mehr `open` ist.
- "Auf dem Tätigkeitsnachweis ist das Unterschriftsfeld leer / da steht ein Name in Schreibschrift
  / hat der Kunde überhaupt unterschrieben" → `approve-stundenfreigabe`. Eine Freigabe **mit Namen,
  aber ohne gespeichertes Handzeichen** druckt den Namen kursiv an der Stelle des Strichs plus eine
  Zeile, die sagt, was dahintersteht ("Digital im Kundenportal freigegeben", "Freigegeben per
  Fristablauf — keine Unterschrift", bei einer Freigabe durch den Verleiher "Eine Bestätigung des
  Entleihers liegt hierzu nicht vor.", sonst neutral "Freigabe erfasst ohne gespeicherte
  Unterschrift"). Das leere Kästchen über einem gedruckten Namen gibt es nicht mehr. Die neutrale
  Zeile niemals zu einer Kanal-Aussage "korrigieren" — der Nachweis ist Beleg nach § 11 AÜG.
- "Der Tätigkeitsnachweis ist zu lang / voller leerer Zeilen / leere Tage ausblenden" →
  `approve-stundenfreigabe`. One `time_tracking_hours_approval` setting
  (`taetigkeitsnachweis_show_empty_days`, per client company overridable), layout only —
  it moves no total and no Rechnung, and a day with a Bemerkung or a Lücke is kept regardless.
- "Der Kranktag / Urlaubstag fehlt auf dem Nachweis / der Kunde will einen lückenlosen Kalender"
  → `approve-stundenfreigabe`. Ein zweites `time_tracking_hours_approval`-Setting,
  `taetigkeitsnachweis_show_absence_days`, **Standard aus** — nicht den Default des
  Geschwister-Settings darüber übertragen. Ein Abwesenheitstag ohne erfasste Zeit wird also
  standardmäßig gar nicht gedruckt: der Entleiher bestätigt die bei ihm geleisteten Stunden, und
  „Krank" auf seinem Dokument verrät ihm etwas über die Gesundheit der Mitarbeiterin. Pro
  Kundenunternehmen überschreibbar; ein Tag mit erfassten Stunden bleibt immer, Layout only.
- "Was steht auf dem Tätigkeitsnachweis / warum steht da 'Krank' / warum ist die Abw.-Spalte leer /
  wo ist der Einsatzzeitraum hin / wo ist die KW hin / wo finde ich die AÜV-Nummer" →
  `approve-stundenfreigabe`. Rows are grouped per KW with einer Summe je Woche (die KW steht an
  den Gruppenköpfen, nicht mehr in der Metaliste), Soll kommt aus dem eingefrorenen Plan des Tages,
  Abw. entfällt auf einem `extra`-Tag, eine **gemeldete** Krankmeldung wird zu genau einem Wort
  ("Krank" — eingereicht zählt bereits, nicht erst genehmigt; der Kranktag ist dann auch keine
  Abweichung mehr, solange nichts erfasst wurde — sofern die Zeile überhaupt gedruckt wird, siehe
  `taetigkeitsnachweis_show_absence_days` oben). **Mitarbeitername und der dokumentierte Zeitraum
  stehen ausschließlich im laufenden Seitenkopf** (dazu der Dokumenttitel), nicht mehr im
  Metablock; "Einsatzzeitraum (Gesamt)" ist bewusst entfernt, die Vertragslaufzeit lässt sich dort
  nicht ablesen. Die **AÜV-Nummer steht umgekehrt im Metablock, nicht im Seitenkopf** — und der
  Metablock läuft **zweispaltig**: Mitarbeiter/in · Entleiher · Einsatzort links, Abteilung · AÜV
  rechts. Wer "unter Entleiher" sucht, findet die beiden rechts daneben, nicht darunter.
- "Soll-Spalte fehlt auf dem Nachweis / der Kunde soll die geplanten Zeiten sehen (oder gerade
  nicht)" → `approve-stundenfreigabe`. Ein `time_tracking_hours_approval`-Setting,
  `document_planned_disclosure`
  (`none` | `delta_only` | `full`, Default `delta_only`), pro Kundenunternehmen überschreibbar.
  Nur `full` druckt den Soll-Block neben Ist — und der hat **drei** Spalten (Zeit/Pause/Std.), nicht
  vier: Soll-Von und Soll-Bis teilen sich eine Zelle („06:00–14:12"), nur Ist trennt Von und Bis.
  Elf Spalten insgesamt, nicht zwölf. Layout only, keine Summe und keine Rechnung ändern sich.
  Vorsicht bei `none` — das Kundenportal zeigt beim Unterschreiben immer den vollen Vergleich.
- „Wann war die Pause / Pausenzeiten auf dem Tätigkeitsnachweis / warum steht da ‚korrigiert' bei
  der Pause" → `approve-stundenfreigabe`. Die Ist-Pause-Spalte druckt unter der Dauer das
  **erfasste Pausenfenster** (`09:51–10:21`, mehrere stapeln sich) — § 4 ArbZG-Nachweis auf dem
  Dokument, das der Entleiher unterschreibt, und zwar bei allen drei Disclosure-Werten. Nur wo die
  Fenster genau die gedruckte Dauer ergeben; sonst steht kursiv *„korrigiert"* statt der Zeiten
  (die vereinbarte Dauer wurde nachträglich geändert — nicht „keine Pause erfasst"). Ohne eigene
  Pausen-Zeiterfassung (Stoppuhr-Pause, manuelle Dauer) gibt es gar kein Fenster, das ist normal.
- "Mitarbeiter kann nicht einstempeln / 'Die Stoppuhr ist für dein Unternehmen nicht aktiviert' /
  Live-Timer fehlt in der App" → `approve-stundenfreigabe`. The timer is a tenant setting that is
  **off by default** and now refused server-side, not a bug and not a permission — the answers
  are manuelle Erfassung or den Dienstplan übernehmen. Ausstempeln/Pause stay possible.
- "Abrechnungszeitraum" splits by intent: **setting** it on a Rahmen-/Einsatzvertrag
  (`timesheet_period_scheme` — halbmonatlich, monatlich, Monatssegmente) →
  `manage-contract-lifecycle`; **understanding** why a Stundenfreigabe-Zeitraum is no longer a
  KW, or reading a `01.08.–07.08.2026 (KW 31/32)` label → `approve-stundenfreigabe`. Do not
  set the deprecated `billing_frequency` — the Zeitraum derives it.
- "Sammelabrechnung erzeugen / Sammel-Reisekostenabrechnung / Reisekosten an die Lohnbuchhaltung
  schicken / Reisekostenabrechnung für alle Mitarbeiter zum Stichtag" → `approve-stundenfreigabe`.
  Eine **Index-Action** auf `0-20` (`generate-period-statements`, daher
  `operation: "execute_index"`), asynchron, mandantenweise per Feature-Flag freigeschaltet und
  **standardmäßig aus** — fehlt sie in `operation: "list"`, ist das kein Beleg dafür, dass es sie
  nicht gibt. Ausgewählt wird nach **Leistungsdatum**, nicht nach Genehmigungs- oder Anlagedatum;
  ein zweiter Lauf mit demselben Stichtag ist gefahrlos.
- "Der hochgeladene Beleg/Dienstplan fehlt / der Upload hängt / Extraktion fehlgeschlagen /
  hat sie denselben Beleg zweimal hochgeladen / Upload verwerfen" → `approve-stundenfreigabe`.
  Die Upload-/Extraktions-Warteschlange ist Modelltyp `0-29` (**read-only** über
  `query-model`/`get-model` — `manage-model` create/update wird abgelehnt); die Rohdatei liest
  `get-attachment` mit `source: "extraction_upload_job"` und der **Job-ID** als
  `attachment_id`; der einzige Schreibweg ist die Record-Action `discard_upload` (zweistufig,
  destruktiv, bei `committed` nicht verfügbar). Ein Duplikat ist über `content_sha256`
  belegbar, ein **fehlendes** Duplikat nicht — dasselbe Bild zweimal fotografiert hat zwei
  Hashes.
- "Benachrichtigungen umstellen / keine E-Mails mehr bekommen / welche Kanäle bekomme ich"
  → `clean-inbox` (`get-` / `manage-notification-preferences`). For "hat der Kunde die
  Stundenfreigabe überhaupt bekommen" → `approve-stundenfreigabe`.
- "Warum wurde ich über diesen Termin nicht informiert / plötzlich steht ein Termin in
  meinem Kalender" → the notification type is `meeting.owner_assigned`, and its channels are
  set from `clean-inbox` like any other type. It fires when somebody **else** books a meeting
  onto the operator, or moves an existing one onto them — deliberately **not** when they
  booked it themselves, not for a meeting logged after the fact (only `Scheduled` ones), and
  not for AI-booked meetings, which `meeting.agent_booked` already covers. Check those
  suppression rules before treating a missing notification as a bug.
- "Umbesetzung / Schicht auf jemand anderen umbesetzen / employee drops out of a running Einsatz"
  → `build-dienstplan` (step 6c) — never cancel-and-recreate the shifts by hand.
- "Ein Mitarbeiter hat den freigegebenen Dienstplan geändert" → `build-dienstplan` (step 6b) for
  what happened and what the employee already got. But "Slack-Meldung/Aufgabe, **wenn** ein
  Mitarbeiter am freigegebenen Plan etwas ändert" → `build-automation-agent` (workflow trigger on
  `0-433`, condition `record_source equals external_panel`).
- "Der Mitarbeiter hat den Dienst von gestern geändert / 'Dienst entfällt' auf einem begonnenen
  Dienst / warum kann er das und ich nicht" → `build-dienstplan` (step 6, the lock box, and 6b).
  Since 2026-09-02 the employee corrects or cancels a single Schicht from the **Zeiterfassung** for
  as long as the **day is open** — kein Tagesabschluss von ihm, keine Kundenfreigabe — including a
  Schicht that has already started or lies in the past. Your `update-shift` / `remove-shift` keep
  the old calendar lock, so this is a real asymmetry: ask the employee to correct it in the app
  instead of promising a Dienstplan write that will 422. The whole-plan wizard is **not** part of
  this — it still refuses a started or past Schicht. Consequences for the day's Soll →
  `approve-stundenfreigabe`.
- "Die App lässt den Mitarbeiter seine Schicht nicht speichern / Sonntag wird abgelehnt /
  Ruhezeit blockiert in der Mitarbeiter-App / employee can't submit their Dienstplan"
  → `build-dienstplan` (step 6b). The employee path is deliberately **stricter** on ArbZG than
  yours: Sonntagsarbeit, > 48h/Woche and a rest gap under 11h block there unless an Ausnahme
  permits them, and the Einsatz's `max_hours` ceiling blocks too — but that ceiling only refuses a
  write that pushes the month **higher than it already stands**, so "überschreitet die gebuchten
  Stunden" on a month that was over anyway is no longer the whole story. Usually the fix is the
  missing Ausnahmekategorie on the **Einsatzbetrieb** — not entering the Schicht for them over MCP.
- "Die App verlangt eine Begründung / warum muss der Mitarbeiter seine Änderung begründen / wo
  sehe ich die Begründung" → `build-dienstplan` (step 6b, and 6b-a for a Vorschlag). A change to a
  Dienstplan that has left draft needs a stated reason; it is asked for **after** every compliance
  check, so that refusal means the plan itself was already fine. The reason rides the employee's
  § 11 digest per line — but the reason on a parked **Vorschlag** is displayed nowhere, so it has to
  be asked for.
- "Krankmeldung genehmigt — wer übernimmt die Schichten / welche Schichten sind jetzt unbesetzt /
  Schicht steht auf `replacement_needed` / Ersatz suchen" → `record-absence` (the `approve`
  response lists the affected Schichten and is the only place they come back), then
  `build-dienstplan` step 6c for the Umbesetzung. Where that list was never seen — a bulk
  approval discards it — the open `staffing` Issues on the Einsätze are the fallback
  (`triage-data-quality` 3f). Shift (`0-111`) itself is **not** queryable over MCP.
- "Slack-Meldung/Aufgabe, **wenn** eine Abwesenheit eingereicht / genehmigt / abgelehnt wird" →
  `build-automation-agent` (`trigger_event: "action_performed"` on `0-13`). AbsencePeriod is the
  only model where that trigger works; its six actions (`submit`, `approve`, `reject`,
  `request-revision`, `cancel`, `reset-to-draft`) are the legal keys, and the Slack footer then
  names the action (`Aktion „Genehmigen" ausgeführt von …`) instead of merely reporting a status
  change. For "nur Selbstmeldungen aus der App" add a condition `record_source equals
  external_panel` — see `record-absence`.
- "Fuhrpark / Dienstwagen / Fahrzeugdaten vervollständigen / Tankkarte anlegen /
  Kilometerstand nachtragen / Kilometerstand beim Fahrer anfragen / Leasing-Laufleistung" →
  `onboard-new-employee` (step 2d).
  Kilometerstände are always a **new reading** (`0-424`), never a write on the vehicle;
  asking the driver for one is the `request_mileage` **action** on the vehicle (`0-4`),
  never a hand-made `0-425` record, and any reading closes the open request automatically.
  Whether the Mitarbeiter-App **demands** a Tacho-Foto is the tenant setting
  `fleet.require_mileage_photo` (default **off**) — off, the app still offers the upload and
  stores a voluntary photo, it just does not block submitting; on, the driver cannot send
  the reading without one. So `source: employee` carries a Beleg only where the tenant
  switched it on, and the operator path is photo-optional in **both** states. The photo is
  web-form/app only, never settable over MCP.
  Schlüssel (`0-52`) and Versicherung (`0-63`) link via `vehicles: [<vehicle_id>]`.
- "HU / TÜV / AU / UVV eintragen / Inspektion erfassen / Ölwechsel / Klimaservice /
  welche Prüfungen sind fällig / Fahrzeug ist überfällig / Mängel aus der HU festhalten" →
  `onboard-new-employee` (step 2d), **VehicleInspection** (`0-69`). `type` has **two
  families**: statutory and date-only (`hu`, `au`, `sp_uvv` — these carry the
  `certificate_number`) and workshop services without a Plakette (`inspection_small`,
  `inspection_large`, `oil_change`, `air_conditioning`); a single "Inspektion" value no
  longer exists. `inspection_small` / `inspection_large` / `oil_change` are due by date
  **or** odometer — `next_due_mileage` is that second deadline, and a record's status is
  the **worse** of the two verdicts, so a vehicle can be overdue on kilometres with its
  date still ahead. Mängel belong in the `defects` field, not in `notes`. A blank `due_on`
  / `next_due_mileage` is derived from `performed_on` / `mileage_at_inspection` + the
  type's interval, `due_on` is stored as the last day of its month, and recording a
  **completed** inspection auto-creates the next open record of that type — two rows per
  type are expected, the latest one is the live Frist.
- "Fahrzeug zuweisen / Dienstwagen übergeben / Zuweisung aufheben / wer ist den Wagen wann
  gefahren" → `onboard-new-employee` (step 2d). A Fahrzeugzuweisung is a **record** on
  **EmployeeVehicle** (`0-432`), not an association: create it with `employee_id` +
  `vehicle_id` + `valid_from`, and **end** it by updating `valid_until` — never `detach`,
  which would delete the period instead of closing it. `manage-association` lists the
  periods read-only and refuses writes.
- "Schaden melden / Schadensmeldung aufnehmen / Unfall mit dem Dienstwagen / Schadensfall
  an die Versicherung / Schadensfall abschließen" → `onboard-new-employee` (step 2e).
  `report_damage` is an **action** on the vehicle (`0-4`) and lands a `submitted` report
  that notifies the Fuhrpark-Verantwortlichen — never create a `0-67` record by hand (that
  is a silent `draft`). The claim then runs `send_to_insurer` → `close` as actions on
  `0-67`; photos are web-form/app only.
- "Fuhrpark-Fristvorgabe / Standardfrist für Kilometerstand-Anfragen ändern / Foto beim
  Kilometerstand verpflichtend machen / Fahrer sollen den Tacho fotografieren / Foto-Pflicht
  abschalten / Hinweise zur Fahrzeugnutzung in der Mitarbeiter-App" → `manage-settings`,
  group `fleet` (`mileage_request_due_days`, `require_mileage_photo`, `usage_notes`) —
  documented in `onboard-new-employee` (step 2d). `require_mileage_photo` (bool, default
  `false`) is tenant-wide and gates **only** the driver's app submission — never the operator
  recording a reading herself. `usage_notes` replaces the whole list, so read before you write.
- "bAV eintragen / Versorgungsträger hinterlegen / betriebliche Altersvorsorge im
  Arbeitsvertrag / Ziffer 9.11 fehlt im Arbeitsvertrag" → `onboard-new-employee` (step 2g).
  `manage-settings`, group `contract`, field `pension_providers` — **tenant-wide, and MCP is
  the only way in**; there is no settings page for it, so never send the operator to the web
  app. The list is empty by default and Ziffer 9.11 stays omitted until it is filled, which
  is the correct rendering for a tenant that promises no bAV — never invent a provider.
- "Vorlaufzeit für eine Terminart setzen / Führerscheinkontrolle soll zwei Tage Vorlauf
  haben / Termin dieser Art nicht kurzfristig buchbar machen" → **not** `manage-settings` and
  **not** `manage-booking-availability`: the lead time for one *kind* of appointment lives on
  the **MeetingType** record (`0-348`), field `min_notice_minutes` (minutes, `null` = no
  override), written with a normal two-stage `manage-model` `update`. It **wins over** the
  host's own `min_notice_minutes` from `manage-booking-availability` whenever it is set — so
  "a Führerscheinkontrolle needs two days' notice" does not drag that checker's other
  appointments to two days too. `manage-booking-availability` stays the right tool for *a
  person's* general lead time.
  - Find the type by listing `0-348` (`query-model`) and reading the `slug` off the result —
    the Führerscheinkontrolle is the system type `driving-licence-check`. Only `category`
    (`system` / `custom`) and `is_active` are filterable; `slug` is not.
  - **System meeting types accept this one field.** They are otherwise immutable (slug,
    label, category are referenced by code), but `min_notice_minutes` and `is_active` are
    writable — any other field in the same `update` is refused for the whole call.
  - **The operator's own booking path ignores the lead time.** When a Führerscheinkontrolle
    is booked without an employee in scope — the dispatcher's booking panel — the notice
    window is bypassed, so slots inside it are shown and are bookable. The same slot is
    hidden from the employee in the Mitarbeiter-App. Never tell an operator a slot is "too
    soon to book" on the strength of the lead time; it binds the employee, not them.
- "Führerscheinkontroll-Termin absagen / gebuchten Kontrolltermin stornieren / der Mitarbeiter
  kann den Kontrolltermin nicht wahrnehmen / die Kontrolle wieder auf fällig setzen" →
  `manage-record-action` on the **Meeting** (`0-201`), action **`cancel`**. Two-stage as
  always: `confirmed: false` (or omitted) previews, `confirmed: true` executes.
  - **Not on the check record.** A `cancel_booking` action exists on the
    DrivingLicenceCheck, but `0-60` is **not on the MCP allowlist** — every generic tool,
    `manage-record-action` included, refuses it with *"not available via the generic model
    tools"*. Don't retry it under another tool; the meeting is the only door. (The same
    holds for `perform_check`, `clear_invalid` and `void_check` — those stay web-app-only,
    so a Kontrolle is *recorded* in the app, never over MCP.)
  - **Find the appointment first — it IS a Meeting.** Nothing on the check hands you the id
    over MCP. Read it off the employee's `get-timeline`, or `query-model` on `0-201` with
    `status: "scheduled"` plus the `meeting_type_id` of the system Terminart
    `driving-licence-check` (resolve it on `0-348`, see the Vorlaufzeit entry above).
    `owner_id`, `meeting_type_id`, `start_at`, `end_at`, `occurred_at`, `outcome` and
    `status` are the filterable fields — there is no filter by employee.
  - **What one cancel does**, all off the single outcome write, no follow-up calls from you:
    the checker's Google Calendar event is cancelled, the linked check drops back to
    **`due`** with `scheduled_at` cleared, and the standard cancelled-meeting follow-up call
    Task is created for the meeting's owner. A fresh slot can be booked straight after.
  - **Availability and permission.** Offered only while the meeting is still `scheduled` and
    not already cancelled. The right is **`meetings.edit`** — *not*
    `driving_licence_checks.edit`, so someone who may book a Kontrolle is not automatically
    someone who may call one off over MCP.
  - **To MOVE an appointment, book the new slot — never cancel first.** Rebooking attaches
    the new meeting before it cancels the old one, so the check stays `scheduled` the whole
    way through. Cancel-then-rebook drops it to `due` in between and leaves a follow-up task
    nobody asked for.
  - **Never delete the meeting.** It belongs to the Prüfprotokoll trail and every delete
    path is blocked outright; cancelling is the only sanctioned way to give an appointment up.
- "Wo ist die Einstellungsseite für Zeiterfassung / Stundenfreigabe / Fuhrpark /
  Führerscheinkontrollen / Kundenportal hin / App aktivieren" → the web-app settings pages
  moved under **Einstellungen → Apps** (one page per app, with per-app enable switches;
  integrations sit in the **Integrations-Hub**). The old URLs redirect. The values stay
  writable over `manage-settings`; the canonical group keys are now app-derived —
  `time_tracking`, `time_tracking_hours_approval` (Stundenfreigabe), `fleet`,
  `fleet_driving_licence_checks`, `client_portal`. The legacy keys `timesheet` and
  `driving_licence_checks` still work but are slated for removal — don't use them in new
  calls.
- "Slack-Bot @alluvo abschalten / dem Bot für einen Channel feste Anweisungen geben /
  warum antwortet @alluvo nicht / warum bricht der Slack-Bot die Liste ab" → `manage-settings`,
  group `slack` (`companion_enabled`, `channel_instructions`) — see *The `slack` group* above.
  There is **no settings page** for the per-channel instructions; MCP is the only way in, the
  `update` replaces the whole channel list, and the answer to a truncated Slack reply is the
  companion's own 12 000-Zeichen/8-Schritte-Budget, not a broken tool. Not
  `build-automation-agent` — that is the workflow action `send_slack_message`, a different
  Slack surface entirely.
- "Meta/Facebook/Instagram ads, Lead Ads, CPL" → `manage-meta-ads`.
- "Meta-Leads kommen an, werden aber keine Kandidaten / Lead-Zuordnung (Mapping) einrichten,
  übersprungene Leads nachverarbeiten / wer hat sich diese Woche über eine Anzeige beworben"
  → `manage-meta-ads` (the leads themselves are readable as `MetaLead`, `0-313`, `read_only`).
- "Slack-Meldung, wenn ein neuer Meta-Lead reinkommt" → `build-automation-agent` — a workflow
  on `0-313`, and **not** on `created`: the row is stored before Meta's payload is fetched, so
  the applicant's name is still empty at that point. That skill has the right trigger shape.
- "Automate a recurring report / schedule an AI agent" → `build-automation-agent`.
- "Agent auf einen Posteingang setzen / Posteingang-Agent einrichten / welche Agenten laufen
  auf welcher Inbox" → `build-automation-agent` (inbox deployments), **not** `clean-inbox`.
- "Baustein anlegen / an einen Agenten hängen / Reihenfolge der Bausteine ändern / welche
  Bausteine gibt es / Markenstimme oder ICP in den Agenten aufnehmen" → `build-automation-agent`
  (`describe-tools` for the block keys; `0-442` + `instruction_block_ids` for tenant Bausteine).
  That path covers **automation** agents; for a conversational or task agent the same skill
  uses `manage-agent-prompt` (`attach-baustein` / `detach-baustein` / `reorder-bausteine` —
  incremental, and a reorder never detaches). All of these are **tenant-Baustein-only**: a
  personal instruction's id reads as "not found" there — that is `manage-ai-preferences`.
- "Meine persönliche Anweisung für die KI / persönliche Anweisung eines Kollegen ändern /
  wer hat eigene Anweisungen hinterlegt / firmenweite Anweisung für die KI-Nachbearbeitung"
  → `build-automation-agent` (`manage-ai-preferences` — `get`/`set`/`list`, optional `agent`,
  default `activity-takeover`; empty string deletes; your own needs no permission, someone
  else's or `list` needs `settings.manage`). **Firmenweit** is instead a Baustein on the
  `activity-takeover` agent (`manage-agent-prompt`), not a `manage-settings` field.
- "Agent taggen / Tag an den Agenten hängen / Tag anlegen, umbenennen, löschen / welche Tags
  gibt es" → `build-automation-agent` (`tags` on `manage-automation-agent` for the attachment —
  names, full replacement, unknown names are created; `0-443` over the generic model tools for
  the vocabulary itself).
- "Mitarbeiter / Firma / Kontakt / Personalbedarf taggen / Tag dranhängen / alle mit Tag X
  finden" → *Tagging a record* above, then `manage-model` `update` with `tags` on that record
  (for a Mitarbeiter or Bewerber: on the **Kontakt**). Twelve model types are taggable; only
  outside that list is a custom field (`manage-custom-field`) still the answer.
- "Welche Agenten gibt es / zeig mir den Prompt des Agenten / was sagt der Talent-Hub-
  Assistent / Anweisungen eines Assistenten ändern / Agent aktivieren oder deaktivieren" →
  `build-automation-agent` (`manage-agent-prompt` — `list`, `get` for the composed prompt by
  section, `set-instructions`/`set-blocks`, `enable`/`disable`). Writes on a **conversational**
  agent are two-stage: without `confirmed: true` you get a composed-prompt diff and nothing is
  written. Task agents write in one stage. No `create`/`delete` — those agents come from
  migrations and the code registry.
- "Was der Bewerber-Agent auf WhatsApp sagt / Anforderungen an Bewerber ändern / Bewerber-Flow-
  Texte anpassen / wer der Agent ist / was er nicht verraten darf / auf den Standard
  zurücksetzen" → `build-automation-agent` (eight sections; `manage-settings` group
  `candidate_flow_prompts` — **`update` needs `confirmed: true`**, `null` = shipped default,
  never `""`; hard and soft requirements carry the same rules, numeric and qualitative, and
  change together; `agent_persona` is the prompt's first sentence and `hard_rules` the
  commercial no-go list). Via `manage-agent-prompt` `set-flow-section` instead when the
  operator asks about one agent — it previews the composed prompt and names the other agents
  the change moves. Same skill
  for "was ist der Baustein *Ausnahme für Leitungs-/Führungsrollen (archiviert)*" — an inactive
  archive block, not a live rule. "Standort der Agentur
  hinterlegen" → the same skill (`general` group, `company_city`/`company_state`).
  The rest of the agency's own address is on that same `general` group and is now readable and
  writable too — `company_address`, `company_address_line_2`, `company_zip`, `company_country`,
  `company_website`, `industry` (`industry` is the tenant's own classification, never a client
  company's). Only `company_city`/`company_state` feed the agent's `agency-location` block; the
  others are tenant master data for letters, contracts and Standortangaben. A **Niederlassung's**
  address is a different record — see the org-structure section above.
  Not the phone assistant — that stays `clean-inbox` (`update-vapi-instructions`).
- "Rückrufzeiten der KI-Nachbearbeitung ändern / ab wann wird erst am nächsten Werktag
  zurückgerufen / wer ist bei uns wofür zuständig, wenn in der Notiz kein Name fällt / die
  Aktionsvorschläge nach dem Gespräch passen nicht" → `build-automation-agent`
  (`manage-settings`, group `ai_takeover` — `callback_same_day_cutoff_hour`,
  `callback_retry_after_hours`, `task_routing_instructions`). These render the
  `callback-timing` / `task-routing` blocks of `call-action-classifier` and
  `inbound-email-classifier` and **are** its rules — the additive layers
  (`set-instructions`, a Baustein, a personal instruction) cannot override them, so writing
  callback hours or responsibilities there changes nothing. The group carries **no**
  free-text instruction field any more: `instruction_snippet` is gone, and the company-wide
  KI-Nachbearbeitungs-Anweisung is a Baustein on the `activity-takeover` agent. What the classifier proposes
  after a logged call: `→ call-summary`.

Always name the concrete skill and start it directly.
