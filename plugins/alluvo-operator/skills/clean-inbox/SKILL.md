---
name: clean-inbox
description: Triage and clean up a shared company inbox in alluvo (support tickets from Gmail/WhatsApp/Chat) — review each Vorgang, close only with evidence, create follow-up tasks on the Contact for anything unclear, and report product-level findings. Use when the operator says "Inbox aufräumen", "Tickets aufräumen", "Zero Inbox", "Inbox N durchgehen", "clean up the inbox", "triage tickets", "go through inbox N", or names a specific inbox to work through. Also covers moving a misrouted ticket to the right queue ("Ticket in andere Inbox verschieben", "Ticket in den richtigen Posteingang schieben", "move a ticket to another inbox", "das Ticket gehört in eine andere Inbox") and forwarding a ticket's original mail — to a known Contact ("Ticket weiterleiten", "an den Kontakt weiterleiten", "forward this ticket to <person>") or to a configured third-party address such as Fibu ("Rechnung an die Buchhaltung weiterleiten"). Also covers the inbox's own settings — forwarding targets and Geschäftszeiten ("Geschäftszeiten der Inbox ändern", "Öffnungszeiten setzen", "set the inbox business hours") — the booking Vorlaufzeit, per person or per Terminart ("Vorlaufzeit ändern", "Vorlaufzeit für Führerscheinkontrollen setzen", "Termine nicht so kurzfristig buchbar", "set the booking lead time", "minimum notice for a meeting type") — and the tenant's public Buchungslinks ("Buchungslink anlegen", "Terminlink erstellen", "meinen Kalender-Link teilen", "Buchungslink aktivieren", "Buchungslink deaktivieren", "Buchungslink auf der Kundenwebsite einbinden", "Einbettungscode für den Buchungslink", "mein Buchungslink zeigt keine Termine", "wer hat gebucht, aber nicht bestätigt", "offene Reservierungen", "create a booking link", "share my scheduling link", "embed the booking page", "unconfirmed bookings") — its notifications ("Inbox folgen", "Inbox stummschalten", "über neue Tickets informiert werden", "follow the inbox", "mute the inbox", "unfollow inbox"), and the Vapi phone assistant's own instructions ("Telefonassistent-Anweisungen ändern", "was der Telefonassistent am Telefon sagt", "Anweisungen für den Telefon-Assistenten", "change what the phone assistant says", "re-sync the phone assistant"). Also covers opening a conversation FROM alluvo — writing an existing Kontakt by email out of an inbox or messaging a Mitarbeiter in their Self-Service-App ("Mitarbeiter anschreiben", "Nachricht an den Mitarbeiter schicken", "Gespräch eröffnen", "einen Kontakt anschreiben", "neues Ticket erstellen", "message an employee in the app", "open a new conversation", "start a ticket ourselves"). Also covers deleting a ticket and reporting its sender as spam ("Ticket löschen", "als Spam melden", "Spam melden statt löschen", "Newsletter-Absender blockieren", "delete this ticket", "mark as spam", "report the sender") — including what that does to the Gmail thread (Papierkorb bzw. Spam) and what closing a ticket does to it (Archivierung). Scoped to shared operational inboxes (General, EmployeeSupport, CustomerSupport, TalentHub) — NOT for a private mailbox, and not a substitute for record writes.
---

# Clean Inbox (Company-Inbox aufräumen)

## Purpose

A shared company inbox is not a mailbox — it is a case registry (Vorgangsspeicher). Any
ticket can carry a payment obligation, a deadline, or a promise made to an employee. That
makes this fundamentally different from tidying a personal inbox: a real Vorgang is never
deleted, nothing gets archived in bulk, and when in doubt the skill asks instead of
deciding. Deleting is reserved for unmistakable junk — see "The Gmail mailbox mirrors the
ticket" below, which is also where you learn what closing does to the mail itself.
MCP-native only; no shell, no database access, no filesystem.

> All closing, deleting and bulk operations are reviewed with the operator before they run —
> see "Ask before you act" below for the exact checkpoint on `set_status`/`bulk_update`/
> `delete`/`bulk_delete`.

## The two rules that override everything else

**1. Never close without evidence.** Close a ticket only via `manage-ticket` `set_status`
(single) or `bulk_update` (cluster) with `status: "closed"`, which requires a
`close_reason_id` — look up the available reasons with `query-model` on `StatusReason`
filtered to `context: "ticket_status"` (and `applies_to: "closed"` for closing reasons; IDs
are tenant-specific, resolve them, don't guess) — and a `close_reason_note` that states the
concrete evidence **with numbers**: "Verfügbarkeit 7/2026 genehmigt (27 Tage), 16 Schichten
im Juli gearbeitet." Never "erledigt", "nicht mehr relevant", or any other bare label —
closing without evidence improves the ticket count and worsens the actual situation.

**2. Never fabricate operational data.** This skill never creates shifts, absences,
vacation, or reimbursements from ticket content — those are promises to employees and
customers, and belong through their own guarded workflows (`build-dienstplan`,
`record-absence`, the Stundenfreigabe/reimbursement flows), never as a side effect of
reading an email. When a ticket implies a gap in the data, the correct output is a **task
with a concrete finding**, not a write.

## Prerequisites

- alluvo MCP tools (`mcp__alluvo__*`) available; the operator has membership in the target
  inbox (`manage-ticket` scopes `list`/`get` to the authenticated user's inbox memberships).
- Know which inbox to work (name or ID), or ask the operator.
- `manage-ticket` and `get-attachment` belong to the **Service & Inbox** module. If the
  tenant has not unlocked it, neither tool is loaded and calling one answers
  `MODULE_LOCKED` — relay that German message verbatim (required Tarif + Testphase link);
  do not fall back to reading mail through other tools.

## Steps

### 1. Take stock

Call `manage-ticket` `action: "list"` with `inbox_id` and iterate `view` (`all_open`,
`unassigned`, `all_closed`, …) and `status`/`priority` filters to size the backlog — it
usually reaches further back than expected. The tool returns view counts alongside the
page of rows, so the counts alone already tell you the scale before you open a single
ticket. Use `created_after` / `created_before` (Y-m-d) to window the list — "last 7 days"
is one filtered call, not paging the whole inbox. Each row leads with the ticket's numeric
id (`#123`) alongside the `TKT-…` reference number — `get`/`set_status`/`assign`/
`bulk_update` (and `manage-task`'s `ticket_id`) all take the numeric id; the reference
number alone is not enough to act on a ticket. Use `search` (matches subject, reference
numbers like "TKT-…", and contact name/email) to spot sender-domain clusters, e.g.
searching a known newsletter domain to see how many rows it touches.

**Two reference formats exist side by side, permanently.** Newly created tickets draw a
sequential number — `TKT-000042`, six zero-padded digits. Every ticket created before that
switch kept its random form — `TKT-ZZXBOLCA`, eight letters/digits — and those were
deliberately not renumbered. So the backlog you triage contains both, and a reference is a
`TKT-` prefix followed by **six or more** letters/digits, nothing narrower. Take the
reference verbatim from the row and search on it; never reconstruct one from a pattern,
never treat the random form as legacy junk or the sequential form as a display bug, and
never infer a ticket's age from which format it carries.

**An inbox may have an AI agent deployed on it — and you cannot see its runs from here.** A
deployed automation agent (Posteingang-Agent) reacts to inbound messages and can already have
created tasks, notes, records or a staffing demand for the very tickets you are triaging. Those
run cards live in the app's ticket conversation; `manage-ticket` `action: "get"` does **not**
return them, so the run is invisible to you while its *effects* are not. Practical consequence:
don't assume an untouched ticket. `get`'s **Linked Tasks** block catches the effects that were
attached to the ticket itself (anything created with `manage-task`'s `ticket_id`, agent or
operator), so read it first; for the rest — a task filed only against the contact, a note, a
`StaffingDemand` — search open tasks for the reference number (the same coverage convention
step 2 relies on) and check the contact/company for records created in the ticket's timeframe.
Otherwise you file a duplicate on top of what the agent already did. If the operator says "the AI already handled that", verify against
the records, not the thread. To see or change which agents run on an inbox, use
`→ build-automation-agent` (`list-deployments`) — it is not configurable from this skill.

### 2. Cluster instead of ticket-by-ticket

Work clusters in this order — don't process the list top to bottom:

| Cluster | Approach |
|---|---|
| **Deadline-bound external senders** (insurance, social insurance, clients, workshops) | **First.** They don't remind, they escalate. |
| **Invoices** | Confirm the bookkeeping process with the operator (see "Forwarding invoices" below), then close with evidence once handled. |
| **Money owed to employees** (reimbursements, expenses) | Verify whether it's already recorded — reimbursements are queryable via `query-model` on `Reimbursement` (`0-20`), filtered by `employee_id`. Check `status`, not just existence: `draft`/`needs_revision` is not yet submitted, `submitted` awaits review, only `approved`/`paid` settles the claim. If not recorded → task, never a write. |
| **Absence / vacation / Dienstplan mentions** | Cross-check against the real records (`manage-employee-availability`, `query-model` on AbsencePeriod, or the Dienstplan itself) before concluding anything is missing. Discrepancy → task, never a direct write. A certificate attached to the mail (AU-Bescheinigung, Nachweis) can be filed to the employee's record — see step 3 — while the AbsencePeriod itself still goes through `→ record-absence`. |
| **Client demand mails (Personalbedarf)** | The *personal-mailbox* agent auto-captures demand only from 1:1 mailboxes, so for a shared inbox it created nothing. **But** a shared inbox can also have an automation agent deployed on it (see the note in step 1), and `create_staffing_requirement` is in the default step whitelist — so a `StaffingDemand` may already exist for this mail. Check before acting: `query-model` on StaffingDemand for the company/contact in the mail's timeframe. If none, route it through `intake-personalbedarf` with the operator (its own guarded preview flow), or task it; then close with the demand/task as evidence. |
| **Misrouted tickets** (landed in the wrong inbox — a Bewerbung in EmployeeSupport, an invoice in TalentHub) | Move them, don't close them: `manage-ticket` `action: "move_to_inbox"` (see "Misrouted tickets" below). Closing and asking the sender to write again loses the thread and the SLA clock. |
| **Newsletters / advertising** | Identify via sender-domain clusters (`search`), spot-check subjects, then `bulk_update` close with an appropriate reason. For **unsolicited** junk that will keep coming, `bulk_delete` with `mark_as_spam: true` is the stronger move — it reports the sender to Gmail so the next one never becomes a ticket at all. A newsletter the tenant once subscribed to is not spam: close it and let them unsubscribe. See "The Gmail mailbox mirrors the ticket". |
| **Outbound threads** (the operator's own sent mail) | Usually moot — close with the current state as evidence. |
| **Everything else** | One task per topic, listing every ticket reference number it covers. |

The goal is not "everything closed" — it's **no ticket without either evidence or a task**.
Before finishing, verify that every remaining open ticket's number appears in some task's
title or body.

**Resolving the ticket's person to an Employee:** a ticket carries a Contact, but the
operational records (availability, AbsencePeriod, Dienstplan) hang off the Employee.
`contact_id` is a filterable column on Employee (`0-2`) and Candidate (`0-81`), so
`query-model` filtered by the ticket contact's id resolves the record directly — don't
match by guessing email variants.

**Cross-checking absence/availability data — two traps that produce wrong findings:**
- An open-ended record (no end date) can silently drop out of a date-range filter. When
  filtering `query-model`/`search-model` by a date field, use an `is_null` condition for the
  open-ended case in the same filter group (or a second OR'd group) rather than only
  `gte`/`between` — otherwise "nothing found in range" can mean "the filter excluded it."
- `status` matters, not just existence: an `AbsencePeriod` or availability entry in
  `draft`/`submitted` is **not approved**. Reporting a draft vacation as "recorded" states
  something that isn't true yet.

### 3. Always evaluate attachments

**The subject line doesn't carry the content.** A ticket titled `Fwd: QRPC6E1.tmp.pdf` can
contain a complete Dienstplan; an empty subject is often the richest ticket, not the most
trivial one.

Use `manage-ticket` `action: "get"` (the thread comes back HTML-stripped and, for email,
with quoted history/signatures removed). Ahead of the thread it also prints the ticket's
**associations** — linked Contacts, Companies, **Vehicles**, **Tasks** and the linked
**WhatsApp campaign**, each with its numeric id. Read them before concluding anything is
missing: a vehicle the AI already linked off a "Fahrzeugrückgabe" mail, or a follow-up task
someone already filed, shows up here, so "there is no task for this" and "this ticket has no
vehicle" are answerable from `get` itself rather than by re-asking the sender. (Notes, calls
and meetings logged in the ticket's context are not repeated in that block — they are already
merged into the thread below it.) Every thread line shows its message's id
(`msg 123`) — pass it as `message_id` to get that one message's full, uncut body. That
works even when nothing was `[truncated]`: a `Fwd:` whose quoted content the cleaner
stripped entirely can leave an empty-looking overview, and the message id is the only way
back to the original text. Attachments are listed per
message (📎 lines) with an `attachment_id`; fetch the actual content with `get-attachment`
(`source: "ticket"`, `attachment_id`). Images come back viewable inline. PDFs come back as
extracted text, capped at ~30,000 characters with a visible truncation marker; a scanned
PDF with no text layer is instead rendered as up to its first 4 pages as images — the
default `mode: "auto"` handles both cases, so you rarely need the explicit `text` or
`base64` modes. Files over 5 MB are rejected with a clear error rather than truncated —
that's a real limit, not a retry case. Anything ambiguous (e.g. a photo of a handwritten,
multi-person family calendar) is genuine ambiguity, not an extraction problem — ask the
operator rather than guessing.

**An attachment that belongs in a personnel file can be filed there — reading it is no
longer the end of the line.** `manage-employee-document` accepts `from_attachment_id` (the
same numeric id from the 📎 line) together with `from_attachment_source: "ticket"`, and
copies the bytes server-side into the employee's document record. For a file that is
already in alluvo this is the *only* path that works: a ticket attachment has no publicly
fetchable URL for `file_url`, and `get-attachment` returns an image for you to look at, not
as a base64 string you could hand to `file_base64`. Use it when an employee mails in a
Nachweis, a certificate, an Impfausweis, or a signed form:

1. Resolve the ticket's Contact to the Employee first (`contact_id` on `0-2`, as above) —
   never file a document against a guessed person.
2. `manage-employee-document` `action: "list-types"` (optionally
   `applicable_to_employee_id: <employee>`, or `category`) for the valid `type_code`. Codes
   are tenant-specific; read them, don't guess.
3. `action: "create"` with `employee_id`, `type_code`, `from_attachment_id`,
   `from_attachment_source: "ticket"` (`"email"` for an attachment on a personal-inbox
   Email), plus whatever `valid_from` / `valid_until` / `issued_by` the document itself
   states. Omit `confirmed` for the preview — it names the attachment it will copy — show
   it to the operator, then repeat with `confirmed: true`.
4. `from_attachment_id`, `file_url` and `file_base64` are **mutually exclusive**; naming
   more than one fails with "Provide only one of from_attachment_id, file_url, or
   file_base64 — not several."
5. Access is checked against the parent ticket's inbox membership (or the Email's view
   permission), the same rule `get-attachment` applies — an attachment you can read is one
   you can file, and no other.

**A Vapi phone ticket already carries its own Call record — don't re-log it.** A ticket
created from an inbound call handled by the phone assistant is automatically linked (via
`ticket_activity`) to a `Call` activity on the ticket's Contact/Company: direction, outcome,
duration and the full transcript, visible through `get-timeline` on that contact/company,
not just as the ticket's `TicketMessage` text. Read that Call's transcript/`ai_summary` as
the source of truth for what was said — filing a Note with the same content during triage
would duplicate an entry the timeline already has.

**A phone or WhatsApp ticket's Contact is now matched across number formats.** A ticket
with no sender address (Vapi call, WhatsApp) resolves its Contact from the number alone,
and that lookup compares three shapes of it — the raw digits, the E.164 digits, and the
German national-format digits. An inbound `+4915785537909` therefore attaches to a Contact
whose column holds `015785537909`, and vice versa. It used to compare digits only, so a
caller already on file in the other format got a **fresh** Contact on every call. Two
consequences for triage: a phone ticket is more likely to arrive already attached to the
right person (check before creating anything), and the pairs the old behaviour left behind
are still there — a bare number-named Contact next to a real one is a Dublette to merge
(`→ merge-duplicate-companies`), not two people.

**A scan that never came through alluvo has a route too.** When the document is a file on
the operator's own machine — a Nachweis handed over on paper and scanned, a certificate
mailed to a private address — there is no `attachment_id` to copy, and `file_base64` is not
the answer: a 4 MB Personalakte PDF is ~5.5 MB of base64 through the conversation. Send it
through a temporary vault instead:

1. `manage-temp-vault` `action: "create"` (no `slots` — a plain vault; optional
   `ttl_minutes`, default 60). It returns a **browser upload link**.
2. Give the operator that link. **They** drop the file in from their own browser — this
   skill never reads local files and never shells out.
3. `manage-temp-vault` `action: "get"` with the `token` to read the uploaded file's public
   URL back. Take it verbatim; it is served from the app's configured public disk (S3 in
   production), so never construct or pattern-match the URL yourself.
4. `manage-employee-document` `action: "create"` with that URL as `file_url` (plus
   `employee_id`, `type_code`, and the validity metadata as above) — preview first, then
   `confirmed: true`. `file_url` must be reachable without authentication, which a vault URL
   is and a Google-Drive share link is not.
5. `manage-temp-vault` `action: "delete"` as soon as the document shows the copied file. A
   vault is transit, not storage: its files sit on a world-readable URL until the TTL elapses,
   and an AU-Bescheinigung or an ID scan must not be left to idle out.

The vault accepts **JPEG, PNG, WebP and PDF** up to 30 MB — a multi-page scan is fine. Only
file what the operator has actually seen: a blurred or partial scan is a follow-up task, not
a document in the personnel file.

This does **not** loosen rule 2. Filing stores the artifact the sender actually supplied; it
does not derive an absence, a Schicht, or a reimbursement from it. The operational record
still goes through its own guarded workflow (`→ record-absence`, `→ build-dienstplan`), and
a document that is blurred, partial, or ambiguous is still a task — not a filing.

### 4. Tasks instead of writes

For every gap, create a task **on the Contact** via `manage-task` `action: "create"`,
`taskable_type: "contacts"` — never guess the contact ID. Resolve it from the employee:
`get-model` on `model_type: "0-2"` (Employee) for the person's `id`, read `contact_id` off
the result. Link the task into the ticket thread with `ticket_id` so the context stays
attached.

> **Default to `manage-task` here.** `bulk-manage-model` (`model_type: "0-5"`) can create
> up to 50 tasks in one call with `attachments: [{type_id, id}, …]`, and `0-300` (Ticket)
> is a valid attachment type — so the thread link itself is reproducible. What is
> `manage-task`-only is `ticket_id`'s **cascade**: it also attaches the ticket's own
> primary Contact and Company to the task, without you resolving them. The other tradeoff
> is the confirm flow — `bulk-manage-model` has no `confirm_token`, so confirming means
> resending every task body in full, verbatim quotes included. Use `bulk-manage-model` when a
> triage run produces many short, similar tasks; keep `manage-task` for the long-bodied,
> ticket-bound ones this step normally writes.

- **Title**: person + concrete finding + ticket reference, e.g. ending in a
  `[from inbox]` marker so these tasks are recognizable later.
- **Body**, four parts:
  1. A verbatim quote from the message — it carries more than any summary.
  2. The current state with numbers: "20 of 21 days recorded, 23.07. is missing."
  3. What needs clarifying — phrased as a question, not an instruction.
  4. Why it matters — deadline, money, a promise — only if it isn't obvious.

  Weak: "check the Dienstplan" — forces a full re-investigation by whoever picks it up.

- **Stagger due dates.** Forty tasks all due today is a pile, not a plan. Group by urgency
  (deadline-bound today, this week, next week) and set a shared `due_at` per group in one
  `bulk-manage-model` call (`model_type: "0-5"`, one `operations` entry per task id), rather
  than leaving everything on the creation date. `manage-task`'s `bulk-update` action was
  retired — it now only does `create` and `update`, one task at a time. Careful with the
  datetime format on the bulk path: `bulk-manage-model` wants an ISO datetime **with an
  explicit offset** (`2026-07-22T09:00:00+02:00` or `...Z`). On `manage-task` itself, `due_at`
  (like `reminded_at`/`wait_until`) is interpreted in the tenant's timezone — "2026-07-22
  09:00" means 09:00 local, no UTC offset math. Only what genuinely must happen today — deadlines, money, an announced
  appointment — gets today's date.

Every `manage-task` `create`/`update` call previews first (`confirmed: false` implicit,
i.e. omit `confirmed` for the preview) — show the operator the preview before confirming.
Each preview returns a `confirm_token` (single-use, valid 10 minutes): confirm with just
`action`, `confirm_token`, and `confirmed: true` — no need to resend the full payload,
which matters here because task bodies carry verbatim quotes. A stale or already-used
token errors cleanly; re-preview and confirm again. Resending the full payload with
`confirmed: true` still works as a fallback.

### 5. Ask before you act — the checkpoint for closing

`manage-ticket` `set_status`, `bulk_update`, `move_to_inbox`, `delete` and `bulk_delete` have
**no** preview flag — unlike `reply`/`forward`/`create` (which preview unless you pass
`confirm: true`), those calls execute immediately. Before calling either with
`status: "closed"`, present the exact plan to the operator: which ticket(s), which
`close_reason_id` (by name, not raw ID), and the evidence text you'll use in
`close_reason_note` — and wait for their go-ahead. Treat that operator confirmation as the
missing preview step. This applies doubly to `bulk_update`: one wrong reason or note applies
to every ticket in the batch at once. `move_to_inbox` needs the same checkpoint (destination
inbox by name) — it is reversible by moving back, but every move leaves its own system note
in the thread.

`delete` / `bulk_delete` need the checkpoint most of all: they take no confirmation
parameter, they take no reason, and on a Gmail ticket they also write to the mailbox. Name
the tickets and say plainly whether the thread will be trashed or reported as spam before
you call.

**Closing is not the only out.** A ticket that is in the wrong queue gets moved (below); one
that belongs with a third party gets forwarded to a preset address, and one that concerns a
known Contact gets forwarded to them (`forward-ticket`, below). Reach for
`set_status: "closed"` when the matter itself is settled, not when it merely isn't yours.

### 6. Document findings beyond the individual ticket

Recurring data errors, tool gaps, or process breaks that surface during triage are worth
more than the ticket they were found in — flag them explicitly to the operator in the wrap-
up rather than letting them disappear into a closed ticket's note.

## The Gmail mailbox mirrors the ticket

A ticket's lifecycle now writes back into the Gmail mailbox behind its inbox. alluvo stays
the system of record; the mailbox is the mirror. Four writes, all of them reversible in
Gmail and all of them with an inverse here:

| What you do to the ticket | What happens to the Gmail thread |
|---|---|
| Close it (`set_status`/`bulk_update` `status: "closed"`, `reply`/`forward` with `close_after`, an approved agent `close_ticket`) | **Archived** — the INBOX label is dropped, the thread stays in All Mail. |
| Reopen it (any status change out of `closed`, including a customer replying) | **Un-archived** — INBOX goes back on. |
| Delete it (`delete` / `bulk_delete`) | Moved to Gmail's **Trash** — undoable for ~30 days. |
| Restore it (`delete-model` `model_type: "0-300"`, `action: "restore"`, or a new inbound reply reviving it) | Pulled back **out of Trash**. |

`mark_as_spam: true` on `delete` / `bulk_delete` replaces the trash write rather than adding
to it: the thread is reported as **Spam** — Gmail's "Report spam", which trains the account's
filter so the next mail from that sender need never become a ticket. Exactly one of the two
ever fires, because a trashed thread teaches the filter nothing. Spam is a signal, not a
guaranteed block, and it does not purge the mail immediately (Gmail clears Spam after ~30
days, same as Trash). The ticket itself is soft-deleted either way.

Four things to hold on to when you use any of this:

- **Gmail-backed tickets only.** A WhatsApp, web-chat or phone ticket, and any ticket whose
  thread id was never recorded, is closed or deleted exactly as before with no mailbox write
  at all. `delete` with `mark_as_spam` says so in its answer ("not reported — this ticket has
  no Gmail thread"); the ticket is still deleted.
- **The write is queued, not synchronous.** The tool answers as soon as the mailbox write is
  enqueued, so a Gmail outage can never fail a delete or a close that already succeeded. Do
  not read the mailbox back and report its state immediately after the call — you would be
  racing the queue. Say what was queued, not what Gmail currently shows.
- **The tenant can switch the mirroring off**, per half, under **Einstellungen → Posteingang
  → Kanäle → „Postfach spiegeln"**: one toggle for archive-on-close, one for
  trash-on-delete, both on by default. These are **not** reachable through `manage-settings`
  (its group list has no `inbox_sync` entry) — if an operator wants them changed, point them
  at that settings page rather than attempting a tool call.
- **Reporting spam ignores those toggles.** It is an explicit operator instruction, not
  automatic mirroring, so `mark_as_spam` still reports the thread even in a tenant that has
  turned trash-on-delete off. Never offer it as "the quiet option".

## What the customer actually sees — the subject is not `subject`

The outgoing subject line is composed **at send time** and is deliberately never written
back to the ticket. `manage-ticket` `get` and `list` show the stored `subject`, and the
`reply`/`forward` **preview also prints the stored `subject`** — so the preview is
accurate about recipient, channel and body, but it is **not** the subject the customer
receives. Two rewrites happen after the preview:

- **The reference is prefixed:** `[TKT-000042] <Betreff>`. Only on the four shared
  operational inboxes (General, EmployeeSupport, CustomerSupport, TalentHub) — a private or
  custom inbox and the 1:1 mail path carry no file number. A subject that already contains
  the reference (a reply to our own reply) is not prefixed twice. Forwards get it too:
  `[TKT-000042] Fwd: <Betreff>`.
- **A phone ticket's first email is retitled.** A Vapi ticket is stored as
  "Telefonanruf von +4915785537909" — useful in the inbox list, absurd to the person who
  called — so the **first** email on it goes out as "Ihre Anfrage bei \<Firma\>" instead.
  Only the first: once the thread exists, later replies use the stored subject, because
  changing it again would split the conversation in the customer's mail client.

When you tell the operator what the recipient will see, say the prefixed (and, on a first
phone-ticket mail, retitled) subject — not the line the preview printed. And never tell
them the stored subject changed: the ticket keeps reading "Telefonanruf von …" in the
list, which is intended.

**Inbound mails find their way back more often now.** If the Gmail thread id matches
nothing, the reference in the subject is used as a fallback — but only when it resolves to
a ticket in the **same inbox** *and* the sender address is one the ticket already knows
(its `contact_email`, or a linked Contact's `email` / `alternative_emails`). A customer who
composes a fresh mail instead of hitting reply therefore usually lands on the running
Vorgang rather than opening a second one. Split tickets on one topic still occur — an
address the ticket doesn't know yet, a stripped reference, a different inbox — because on
any doubt the system opens a new ticket rather than risk exposing one person's thread to
another. Treat a split pair as a real thing to reconcile during triage, not as background
noise, and check for an unknown-but-legitimate sender address on the Contact when you find
one.

## Opening a conversation yourself: `manage-ticket` `create`

Triage is reactive; the tool is not. `manage-ticket` `action: "create"` opens a **new**
ticket out of alluvo instead of acting on one that arrived — the only action that starts a
Vorgang. Two modes, both **preview → confirm** exactly like `reply`/`forward`: call without
`confirm`, read the preview back to the operator, and only then call again with
`confirm: true`.

- **`mode: "email"`** — sends a new email through an inbox's connected email channel and
  opens an email ticket for it. Requires `inbox_id`, `contact_id`, `subject`, `body`;
  `priority` optional (default `medium`). The recipient is **always an existing Contact** —
  free-text addresses are rejected, so resolve the person via `search-model` on `0-105` (or
  create the Contact first) and pass their `contact_id`. It fails with a named reason when
  the contact has no email on file, and when the inbox has no active email channel connected
  ("… connect a Gmail account under Einstellungen → Inbox") — that one already shows up in
  the preview, so you learn it before the operator says yes. The inbox must be one you can
  reach: with inbox memberships, only your own; a user with no membership at all may use any.
- **`mode: "employee_app"`** — starts a conversation with an employee inside their
  self-service app. Requires `employee_id`, `subject`, `body` (`priority` optional). **No
  email is sent** — the message lands under „Nachrichten" in the Mitarbeiter-App plus an
  in-app and a push notification. No `inbox_id` here: the ticket is opened in the tenant's
  configured Mitarbeiter-Support inbox automatically, which is the only place the app looks
  for it. It needs the employee to have a self-service account — without one the call fails
  with "has no self-service app account yet — invite them via the invite-user record action
  (`manage-record-action`) before opening a conversation" (`→ onboard-new-employee`, step 5,
  is the current path for that).

What you get afterwards is an ordinary Vorgang: you are creator **and** owner, status is
`waiting_on_user` (we wrote, the ball is with the recipient), and the recipient's answer
lands **back in this same ticket**. Every rule above then applies to it, including rule 1 for
closing it. In email mode the outgoing subject is composed at send time like any other reply,
so the `[TKT-…]` prefix rule from the section above applies unchanged (shared operational
inboxes only), and the preview shows the stored subject, not the sent one. The mail itself goes out asynchronously via the email queue.

**Only for a conversation you want tracked as a ticket.** Acquisition mail does not belong
here: a multi-step sequence → `→ enroll-outreach`, a single hand-crafted pitch with profile
blocks, template rendering and engagement tracking → `→ profilvertrieb` (`manage-1on1-email`).
Reach for `create` when the point is an **answer you need back** on a case the team must be
able to see — a question to an employee, a query to a client contact spun off an existing
ticket.

**Never open one unasked.** The confirmed call creates the ticket and sends in a single step
and a sent message can't be recalled, so naming recipient, subject and body to the operator
and getting a yes is the checkpoint — that is what the preview is for. `manage-ticket` is
deliberately **not** automation-safe, so no headless automation agent can open a conversation
with a person on its own; this action always has an operator behind it.

## Misrouted tickets: move to the right inbox

A ticket that landed in the wrong queue is not a ticket to close. `manage-ticket`
`action: "move_to_inbox"` with `ticket_id` and `inbox_id` (the **destination**) hands it to
the team that owns it, keeping the thread, the contact links and the reference number intact.

- **Find the destination id first.** `query-model` on `0-301` (Inbox) lists the tenant's
  inboxes with their ids — resolve the one the operator named, don't guess.
- **The destination may be any inbox in the tenant**, including ones the operator isn't a
  member of. That is deliberate: someone who staffs a single queue must still be able to hand
  a misrouted ticket to another team. It does **not** widen anything else — the ticket must
  still be reachable through its **current** inbox for you to act on it at all, exactly as
  with every other `manage-ticket` action.
- **Idempotent.** Moving a ticket to the inbox it is already in is a no-op.
- **It leaves a trace.** A system note ("moved from X to Y by Z") is written into the thread,
  so the handoff stays visible to whoever picks the ticket up.
- **SLA and followers are untouched.** The first-response and resolution deadlines were
  computed from the *original* inbox's policy and keep running unchanged — a move neither
  buys time nor shortens it, so never tell an operator that moving a breaching ticket resets
  its clock. Existing followers stay subscribed and members of the new inbox are **not**
  auto-subscribed; someone over there has to pick it up (or follow it) actively. Say that out
  loud when you move something urgent, otherwise a move is a quiet way to lose a ticket.
- **Not a substitute for assignment.** Moving changes the owning queue, not the owner —
  `assign` (with an `owner_id` that is a member of the ticket's inbox) is still what puts a
  named person on it.

Rule 1 still stands: the move is the resolution of "wrong queue", not evidence that the
matter is handled. Whatever the ticket is actually about stays open in the new inbox.

## Forwarding invoices

Invoices belong with bookkeeping. **Always confirm the process with the operator before the
first send** — a sent message can't be recalled, and a wrongly addressed receipt confuses
bookkeeping more than it helps. Confirm: the recipient, whether a cover note is needed, and
whether the original attachment should travel with it.

`manage-ticket` `action: "forward"` is the sanctioned path to move a ticket's original email
to a **third-party address** such as a bookkeeping mailbox. (Forwarding to someone the tenant
already knows as a Contact is a different action — `forward-ticket`, next section.) It uses
the same **preview → confirm** flow
as `reply`: call without `confirm: true` to get a preview (no message sent), then again with
`confirm: true` to send. Parameters:

- `to` — **required.** Must case-insensitively match one of the inbox's configured
  **forwarding targets** (`forward_targets`). Free-text recipients are rejected on the
  MCP surface. If the target you need isn't configured yet, add it first on the inbox
  record (see below) — never try to work around the target list.
- `note` — optional cover note included with the forwarded message.
- `include_attachments` — includes the original message's attachments; default `true` (so the
  invoice PDF travels with it unless you explicitly opt out).
- `close_after` — optionally close the ticket in the same step. As with any close, it requires
  `close_reason_id` (plus `close_reason_note` when that reason requires one). This is the
  usual finish for an invoice: forward to Fibu with `close_after`, reason "resolved", note
  referencing the forward — so the ticket carries its own evidence.

**Configuring forwarding targets** — the preset list is the `forward_targets` field on the
**Inbox record** (the MCP mirror of Einstellungen → Inbox → Weiterleitungsziele). There is no
dedicated tool for it; read it with `get-model` and write it with `manage-model`, both on
`model_type: "0-301"`:

- Read the current list with `get-model` on `model_type: "0-301"` (or `query-model` to find
  the inbox in the first place) — that is also how you get the inbox ID to write against.
- Write with `manage-model`, `action: "update"`, `model_type: "0-301"`, `id: <inbox>`,
  `data: {"forward_targets": [{"email": "…", "label": "…"}]}` — every entry needs both keys,
  `label` ≤ 100 characters. This is a **full replace**, not an append: include every target
  you want to keep; an empty array clears them all. Two-stage as always: `confirmed: false`
  to preview, then `confirmed: true` to save — show the operator the before/after first.

Writing `forward_targets` requires the **settings-manage** permission, which is narrower than
the `inboxes.edit` that other inbox fields need. Without it the update is rejected with
"Changing forward targets requires the settings-management permission" — report that to the
operator rather than retrying, and never route around it by forwarding to a free-text address.

So when the confirmed bookkeeping address isn't a configured target yet, the flow is:
confirm the exact address and label with the operator → read the current `forward_targets`
→ `update` (preview → confirm) with the existing targets plus the new one → then `forward`.
Only add targets the operator has explicitly confirmed — the preset list is a guardrail,
not a formality.

## Forwarding to a Contact: `forward-ticket`

A misdirected inbound mail often belongs to a person the tenant already knows — the Pflege-
dienstleitung who actually owns the request, the client contact the sender meant to write to.
That forward runs as a **record action on the ticket**, not through `manage-ticket`:

`manage-record-action`, `operation: "execute"`, `model_type: "0-300"`, `record_id: <ticket>`,
`action: "forward-ticket"`, `data: {"contact_id": <id>}` — preview with `confirmed` omitted,
show the operator what will be sent to whom, then repeat with `confirmed: true`.

- `contact_id` — the preferred recipient: a **Contact** record (`0-105`), whose address is
  resolved from the CRM. Resolve it with `search-model` / `query-model` first and name the
  person to the operator; never send to an id you guessed. A Contact with no email on file is
  refused with a clean error naming them.
- `to_email` — the fallback for someone who isn't a Contact yet (an internal colleague, a
  one-off address). Free text: **this action does not check the inbox's `forward_targets`**,
  unlike `manage-ticket` `forward`. That guardrail simply doesn't apply here, so operator
  confirmation of the exact address before `confirmed: true` is the only check there is.
- Give **one of the two**. Omitting both errors at execute time; passing both silently uses
  `contact_id` and ignores `to_email`.
- `note` — optional cover text shown above the forwarded message. `include_attachments` —
  default `true`, so the original's attachments travel unless you opt out.

**What it does and doesn't do:**

- The forward lands as another outbound message on **this same ticket** — never a new one —
  and the ticket's last-message timestamp moves, so it resurfaces in the list.
- What gets forwarded is the ticket's **first inbound customer message**, not the latest one.
  On a long thread say that to the operator; if they mean the last reply, this is the wrong
  tool. A ticket with no inbound message at all (our own outbound-only thread) is refused.
- A Contact not yet linked to the ticket is attached to it (role *Mentioned*, an existing
  role such as Primary is never overwritten), so the forward and the whole conversation show
  up on their timeline. Mention that — it changes what the Contact's record shows.
- **It does not close the ticket.** There is no `close_after` here; if the forward settles the
  matter, close separately via `manage-ticket` `set_status` with a reason and an evidence
  note, under the checkpoint in step 5.
- **Email tickets only (Gmail).** The ticket must sit on a Gmail inbox channel; a WhatsApp,
  chat or phone ticket is rejected. The action is still *listed* as available on those — the
  constraint only fires on execution — so check the ticket's channel before you promise a
  forward.
- Requires update permission on the ticket, like any other ticket write.

**The preview is thinner than `manage-ticket`'s.** A record-action preview echoes back the
`data` you passed plus form validation — it does **not** resolve the Contact's email, does not
test the Gmail constraint, and does not render the message that will go out. So don't present
it as a message preview: state recipient (by name *and* address), cover note and attachment
choice in your own words, and get the operator's go-ahead. A sent mail can't be recalled. The
subject rewrite applies here as everywhere: the recipient sees `[TKT-000042] Fwd: <Betreff>`
on the four shared inboxes, not the stored subject the preview would print.

**Which of the two forwards:** a known Contact (or any recipient outside the preset list) →
`forward-ticket`. A configured third-party mailbox such as Fibu, especially when it should be
closed in the same step → `manage-ticket` `forward` with `close_after`.

## Inbox settings: Geschäftszeiten (business hours)

The Inbox record itself (`0-301`) is reachable through the generic tools — `get-model-schema`,
`get-model`, `search-model`, `query-model` and `manage-model` all accept it, so an inbox's
opening hours are readable and settable from here instead of "ask an engineer". `InboxChannel`
(`0-302`) is **read-only** through those generic tools — see "the Vapi phone assistant's
instructions" below for the one sanctioned write. `InboxMember` (`0-303`) has **no** MCP
surface: memberships still cannot be read or changed this way.

`business_hours` is a map keyed by **lowercase English weekday name** (`monday` … `sunday`),
each open day carrying `start` and `end` as `H:i` 24-hour strings:

```
{"monday":  {"start": "08:00", "end": "17:00"},
 "friday":  {"start": "08:00", "end": "15:00"}}
```

- **A weekday absent from the map is closed** — that is the only way to close a day. There is
  no "closed" flag, and a day present with only `start` or only `end` is rejected outright,
  not read as closed.
- German keys are rejected (`montag` errors and names the valid set), as are times that
  aren't `H:i` (`8:00`, `08:00:00`).
- Writing is a normal two-stage `manage-model` `update` — `model_type: "0-301"`, the inbox
  `id`, `data: {"business_hours": …}`: preview without `confirmed`, show the operator, then
  `confirmed: true`. It **replaces the whole map**, so send every open day, not just the one
  being changed. Read the current value first with `get-model` rather than reconstructing it
  from memory.
- Requires the `inboxes.edit` permission. With `inboxes.view` only, the write is refused with
  a clean error and nothing is saved.

**Before changing the hours, tell the operator where they take effect:**

- **Terminbuchung.** They are the fallback bookable window for a host with no personal
  availability setting (per-user setting → inbox `business_hours` → system default), so they
  shape what `get-booking-availability` offers. **Only the hours fall back this way.** The
  Vorlaufzeit does not: a host without a personal setting gets the 240-minute system default,
  never anything derived from `business_hours`. Changing the hours therefore never changes how
  short-notice a booking may be — see the next section for the two places that do.
- **The Vapi phone assistant** — the important caveat. Its prompt states the opening hours
  and whether the caller reached us outside them, but that prompt is composed **at sync
  time**. A `business_hours` change is saved and correct for booking immediately, while the
  live assistant keeps announcing the old hours until it is re-synced. Re-syncing is now
  part of this skill: run `update-vapi-instructions` on the inbox's phone channel with a
  bare `data: {"confirmed": true}` — **no `custom_instructions`** (next section) — that
  recomposes the prompt from the fresh hours and pushes it, without touching the tenant's
  own instruction text. An unconfirmed call is a pure read and pushes nothing, so it is
  not a re-sync. So the sequence for an
  hours change on an inbox with a phone channel is: update `business_hours` → re-sync →
  only then tell the operator the caller-facing text has changed. Until the re-sync
  succeeds, don't claim it has.

The inbox's SLA policy has a `business_hours_only` mode that reads this same map, but ticket
SLA due dates are not currently computed on ingestion — do not promise an operator that
changing the hours moves any ticket's deadline.

## Vorlaufzeit (booking lead time): per person, or per Terminart

How short-notice a slot may be booked is a separate setting from the hours above, and it has
**two** homes. Say which one the operator means before writing either:

- **Per person** — `min_notice_minutes` on the host's own availability, read with
  `get-booking-availability` and written with `manage-booking-availability` (`action:
  "update"`, preview → `confirmed: true`). Applies to everything that host is booked for.
- **Per Terminart** — `min_notice_minutes` on the **MeetingType** record (`0-348`, minutes,
  `null` = no override), a normal two-stage `manage-model` `update`. When set it **wins over**
  the host's own value, so "a Führerscheinkontrolle needs two days' notice" does not stretch
  that checker's other appointments to two days as well.

**Finding the right Terminart.** List them with `query-model` on `0-348` and pick the row by
its `slug` — the Führerscheinkontrolle is the system type `driving-licence-check`. Only
`category` (`system` / `custom`) and `is_active` are filterable; `slug` is **not**, so narrow
with `category eq system` and read the slug off the result rather than filtering on it.

**System meeting types accept this one field.** They are otherwise immutable — slug, label and
category are referenced by code — but `min_notice_minutes` and `is_active` are writable. Any
other field included in the same `update` is refused, and the whole call fails with it.

**The operator's own booking path ignores the lead time.** When a Führerscheinkontrolle is
booked with no employee in scope — the dispatcher's booking panel — the notice window is
bypassed: slots inside it are shown and can be booked. The same slot is hidden from the
employee in the Mitarbeiter-App. So never tell an operator a slot is "too soon to book"
because of the Vorlaufzeit; it binds the employee, not them.

## Öffentliche Buchungslinks — `MeetingBookingLink` (`0-444`)

A booking link is the public page a Kunde or Kandidat opens to pick a slot themselves,
instead of the operator negotiating a time by mail. It belongs to **exactly one host** and
publishes that person's real Google free/busy at

```
https://app.<domain>/<tenant-slug>/meetings/<slug>
```

Full read+write over the generic model tools (`get-model-schema`, `query-model`,
`search-model`, `get-model`, `manage-model`, `delete-model`) with `model_type: "0-444"`.
Writes are the normal two-stage shape: `manage-model` without `confirmed` previews, show the
operator, then re-call with `confirmed: true`.

**The host is not an ordinary field.**

- `user_id` is **required on create**, and a non-admin may only name **themselves**. Naming a
  colleague comes back as a field-level error, not a bare 403 — holding
  `meeting_booking_links.create` is not consent to publish somebody else's calendar.
- `user_id` is **absent from the update rules entirely**: a link can never be moved to another
  host. Handing a link over is a new link, not an edit.
- Ownership is enforced on top of the `meeting_booking_links.*` permissions, so a role granted
  `scope: all` still cannot read or repoint a colleague's link. Administrators pass.

**Activation needs a live Google calendar — this is the missing "warum geht das nicht".**
`is_active` cannot be switched **on** for a host with no active Google-Kalender-Verknüpfung,
on create and on update alike, and the `activate-booking-link` action is simply not offered.
If the operator runs into that, the fix is connecting Google Calendar **for that host** —
retrying, or recreating the link, changes nothing. Creating the link inactive now and
activating it once the calendar is connected is the right sequence.

**An already-active link can still go dead**, and none of these switch it off:

| State | What it means | What the visitor sees |
|---|---|---|
| `calendar_disconnected` | the host's Google connection is gone | the page says it cannot offer slots |
| `calendar_unreadable` | the connection exists, the free/busy read failed | same — we refuse to guess |
| `host_inactive` | the host's user account is deactivated | same |
| `host_paused` | the host's availability carries the away toggle (`manage-booking-availability`) | an **empty calendar**, which reads as "ausgebucht" rather than "abwesend" |

So when an operator says "mein Buchungslink zeigt keine Termine", check those four before
touching the link's own settings. Only the first is something they can fix themselves.

**`null` means inherit, not "no value".** Every scheduling field on the link may be `null`.
The chain is **link → (only for `min_notice_minutes`) MeetingType → the host's own
availability setting** (`manage-booking-availability`, above); the system default is applied
last by the resolver and is stored nowhere. Clearing a field on the link therefore hands the
decision back up the chain rather than switching it off — say that before writing a `null`.

**The fields, with the ranges validation actually enforces.** Confirm against
`get-model-schema` (`create` / `update` context) before writing; these are the ones operators
ask for:

- `title` (required), `slug` (required), `description`, `meeting_type_id`, `location_id`.
- `slug` is lowercase letters, digits and hyphens only (`^[a-z0-9-]+$`), unique, and
  **`confirm` and `manage` are refused**: those are the sibling routes
  (`/meetings/confirm/{token}`, `/meetings/manage/{token}`), so a link carrying either slug
  would be permanently unreachable.
- `durations` (array, max 10, each 5–1440 min), `default_duration_minutes` (5–1440),
  `min_notice_minutes` (0–525600), `buffer_minutes` (0–1440), `rolling_horizon_days` (1–365),
  `slot_increment_minutes` (5–1440).
- `location_type` — `phone`, `in_person`, `video_call`, `custom` — plus `location_details`.
- `requires_email_verification`, `reservation_ttl_minutes` (1–1440 — how long an unconfirmed
  reservation holds its slot).
- `form_fields`, `custom_questions`, `consent_text`, `requires_consent`.
- `confirmation_message`, `redirect_url` (must be a URL), `allow_reschedule`, `allow_cancel`,
  `cancel_notice_minutes` (0–525600).

**`record_target` decides what a booking creates besides the Contact and the Meeting** —
`contact_only`, `candidate` (Bewerbungslink) or `company_lead` (Vertriebslink). The **Contact
is always created** (and matched against existing ones by the sanctioned resolver, alternative
addresses included, so a known person does not get a second record); `record_target` only
decides whether a Bewerber or a Firmen-Lead hangs off it. Everything the link mints carries
`record_source: booking_link`, which is how "woher kommt dieser Kandidat" is answered later.

> **`record_source_detail` is validated but never saved — do not send it.** Both the create
> and the update rules accept it, but the model does not carry it in its fillable list, so
> `manage-model` reports it back under **IGNORED FIELDS** and writes nothing. It is meant to be
> the per-link Herkunftstext ("Karriereseite Nachtschicht") stamped onto every Contact the link
> mints, so sending it would leave the operator believing that provenance was stored. api-side
> gap → alluvo#4509. Until that lands, leave the field alone and don't promise it.

**Embedding and Aussehen.**

- `allowed_origins` (max 20) is the allowlist of sites that may frame the booking page. A bare
  `*` is **rejected** — the two filters that read this value disagree about it, and one of them
  would read it as "jede Website".
- `theme` and `font_css_url` are deliberately strict, because both end up inside the
  `<style>` block of a page that carries personal data: colours are `#rgb` / `#rrggbb` only
  (no `rgb()`, no `var()`, no named colours), a radius is a number with a unit, a font stack
  may not contain a parenthesis (so no `url()`), an **unknown token key is refused outright**
  rather than stored and ignored, and `font_css_url` must start with `https://`. If the
  operator hands you `rgb(0,0,0)` or `cornflowerblue`, convert it to hex before writing.

**The four record actions** — `manage-record-action`, `operation: "execute"`,
`model_type: "0-444"`, `record_id: <link>`:

| `action` | What it does |
|---|---|
| `copy-booking-link` | Read-only. Returns the public URL in `url` — the thing to paste into a mail signature, an Angebot or a chat. Needs `view`. |
| `copy-booking-embed-snippet` | Read-only. Returns `snippet`, the `<div data-alluvo-booking="…"></div>` + `<script>` pair for the Kunde's own website. Needs `view`. |
| `activate-booking-link` | Sets `is_active: true`. Offered **only** when the link is off *and* the calendar check above passes. Needs `update`. |
| `deactivate-booking-link` | Sets `is_active: false`. Deliberately ungated, so a broken link can always be switched off; it carries a confirmation. Bereits bestätigte Termine bleiben bestehen — only new bookings stop. Needs `update`. |

An action that does not apply right now is **not offered at all**. Run `operation: "list"` on
the record and read that, rather than treating a missing action as "the tool cannot do it".

**Unbestätigte Buchungen — `MeetingBookingRequest` (`0-445`), read-only.** A reservation holds
its slot until `expires_at` and then either becomes a real Meeting or is pruned. It is written
**only** by the booking service (book → confirm → cancel), never by hand: `manage-model`
create/update is refused and there is no action for it. What it is good for is the question
operators do ask — "wer hat gebucht, aber nicht bestätigt":

```json
{"filter_groups": [{"conditions": [
  {"field": "confirmed_at", "operator": "is_null"},
  {"field": "expires_at", "operator": "gt", "value": "<jetzt>"}
]}]}
```

- Filterable on `0-445`: `meeting_booking_link_id` (a **relationship** filter — `in` /
  `not_in`, there is no `eq`), `email` (text), and `start_at` / `confirmed_at` / `expires_at`
  (datetime — `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `between`, `is_null`, `is_not_null`).
- Filterable on `0-444`: `is_active` and `requires_email_verification` (boolean),
  `record_target` (enum — `in` / `not_in`, no `eq`), `user_id` (relationship). Finding a link
  by title or slug is `search-model`, not a filter.
- An operator the field does not carry is **not applied**: it comes back in the response's
  `skipped_conditions` and the result set is quietly wider than asked for. Read that array
  before quoting a count.

**An empty result is not proof that nobody booked.** Open reservations past their `expires_at`
are removed by a scheduled prune job, so anything expired is gone from the table by design —
report "keine offenen Reservierungen gerade", never "es hat niemand gebucht".

## Inbox settings: the Vapi phone assistant's instructions

What the phone assistant says to callers is composed by alluvo, but the tenant gets one knob
in it — a block of their own instructions. Changing it is a record action on the **channel**,
not on the inbox:

> **Not an Agent record.** The phone assistant lives on the InboxChannel and is edited only by
> the action below. `manage-agent-prompt` — which does reach the tenant's conversational and
> task agents (`→ build-automation-agent`) — cannot see or change it, and neither can
> `manage-automation-agent`. The two surfaces share the shape (read the composed prompt,
> confirm, then write) but not the tool.

`manage-record-action`, `operation: "execute"`, `model_type: "0-302"`, `record_id: <channel>`,
`action: "update-vapi-instructions"`. The action gates on `confirmed` **inside `data`**, and
the tool fills that key from its top-level `confirmed` when you leave it out — so a top-level
`confirmed: true` with `custom_instructions` but no `data.confirmed` **writes**. Set it
explicitly on every call: `data: {"custom_instructions": "<full markdown>", "confirmed":
false}` to preview (write-free — the response shows the stored text and the composed prompt
your edit would produce), show it to the operator, then re-call with `"confirmed": true` in
`data` to write and push.

**Find the channel first.** `query-model` on `0-302` filtered by `inbox_id` lists the inbox's
channels; take the one whose `type` is `phone` and whose `provider` is `vapi`. The action is
offered **only** on such a channel that also has an assistant connected — on a Gmail,
WhatsApp or chat channel, or a phone channel that was never provisioned, it isn't available
and `execute` refuses with the reason. Check with `operation: "list"` on the channel if
unsure. Reading needs `inbox_channels.view`, the action `inbox_channels.update`.

**The write replaces the block — read before you write.** `custom_instructions` is
overwritten wholesale, never appended, and an empty string deletes the block. The read path
is the unconfirmed call itself: `data: {"confirmed": false}` (or top-level `confirmed:
false`) writes nothing, calls Vapi nothing, and returns the currently stored
`custom_instructions` plus the full `composed_prompt` that would be pushed — this is the
**only** way to see the current text over MCP (`get-model` omits `config` because it also
holds mailbox OAuth tokens). Send `custom_instructions` along on that read call and the
`composed_prompt` reflects your proposed edit instead of the stored text. So: read the
stored text first, fold the operator's change into the **full** text, preview, then
confirm — never compose an edit from memory or from a fragment.

**A bare `data: {"confirmed": true}` — no `custom_instructions` — is the explicit re-sync**
— recompose and push, stored text untouched. That is the right call after a
`business_hours` change, and the right retry when a push failed. The old "no data = safe
re-sync" convention is gone: a call without an explicit `confirmed: true` is a pure read
and pushes nothing.

**A failed push is not a failed save.** If the text was stored but Vapi rejected the push, the
error says so explicitly. Re-run with a bare `data: {"confirmed": true}` (no
`custom_instructions`) to retry only the push — re-sending the edit would be a second write
of text that is already stored.

**`manage-model` is not an alternative here.** `0-302` is deliberately excluded from generic
create/update: such a write would set `config` and push nothing, leaving the live assistant on
the old prompt while the record claims it was synced. This action is the only sanctioned path
— if it isn't available on the channel, the answer is "not from here", never a workaround.

### What the instructions may and may not say

The block is folded into the composed prompt under `## Tenant-Kontext (vom Kunden hinterlegt)`,
and its own headings are pushed down a level so tenant text can never pose as one of alluvo's
framework sections. A precedence section then states what it outranks:

- **Fair game — conversation strategy:** the order questions are asked in, how strongly a topic
  is weighted, framing and tone, named contacts to mention, and statements about opening hours
  (those may legitimately deviate from the composed default).
- **Never overridable — the hard rules:** the recording / AI-disclosure behaviour (§ 201 StGB —
  never push a caller, and end the call politely without collecting data if they object); no
  binding statements on prices, hourly rates, contract or legal terms; never promising that a
  shift or Dienst can be filled; never inventing information; and the exact final sentence
  before the call ends — Vapi's hang-up detection matches that wording, so it may not be
  reworded, shortened, replaced, or followed by any extra farewell.

Draft instruction text on the strategy side of that line. If the operator asks for something on
the hard-rule side — a price quote, a staffing promise, a different sign-off — say plainly that
the prompt won't honour it, rather than writing text that the precedence section overrides
anyway. And this is tenant configuration reaching every caller: preview it to the operator in
full and let them approve the wording, the same as any other outbound message in this skill.

## Inbox notifications: folgen / entfolgen (follow / unfollow)

Following an inbox decides whether the operator hears about tickets **arriving** in it, on
any channel (email, WhatsApp, chat widget, phone). That is a different fact from
membership, which grants access to work those tickets. Both run as record actions on the
Inbox (`0-301`) through `manage-record-action`:

- `operation: "list"`, `model_type: "0-301"`, `record_id: <inbox>` — shows which of
  `follow-inbox` / `unfollow-inbox` is available, and that availability **is** the current
  state: `follow-inbox` is offered only when not subscribed, `unfollow-inbox` only when
  subscribed. Read the state there instead of asking the operator whether they follow it.
- `operation: "execute"`, `model_type: "0-301"`, `record_id`, `action: "follow-inbox"`
  (or `"unfollow-inbox"`) — preview with `confirmed` omitted, show it, then repeat with
  `confirmed: true`.

**Self-scoped, always.** Both actions act on the authenticated user and take no target-user
parameter — there is no MCP path to subscribe or silence a colleague. If the operator asks
for that, say so plainly rather than looking for a workaround.

**Unfollowing silences, it does not remove access.** Membership — and with it the ability to
open and work the inbox's tickets — is untouched; that is precisely what someone on a
high-volume queue wants. Joining an inbox subscribes automatically and being removed from it
unsubscribes, so an explicit `follow-inbox` is mainly how someone comes back after
unfollowing.

**A subscription only delivers to a member.** Recipients of the arrival notification are the
inbox's subscribers narrowed to its **members** (or holders of full tenant access):
`inboxes.view` is tenant-wide, so following an inbox one doesn't staff is permitted but
delivers nothing. `InboxMember` (`0-303`) has no MCP surface, so membership cannot be granted
from here — when the operator wants notifications for an inbox they aren't a member of, tell
them the membership has to be added in the app first.

**Set the channel expectation.** Arrival notifications (`inbox.ticket_created`) go out
**in-app and as push; email is off by default** — the trigger fires once per arriving ticket,
and a busy inbox runs dozens a day. Never tell an operator that following an inbox will mail
them without switching that channel on first.

**Channels per notification type are editable from here** — following decides *whether*, the
per-type preferences decide *how*:

- `get-notification-preferences` — the effective in-app / email / push / Slack setting per
  type, plus `email_frequency`. Defaults to the calling user; `user_id` reads a colleague's
  and needs permission to view them.
- `manage-notification-preferences` — `action: "update"` with one `preferences` entry per
  type (`notification_type` plus only the channels being changed; omitted fields keep their
  value). Preview with `confirmed` omitted, then repeat with `confirmed: true`.
- Relevant type keys here: `inbox.ticket_created` (arrivals — email, push and Slack can be
  switched off, in-app cannot) and `inbox.queue_digest` (the daily unassigned-queue digest).
  Transactional types are always on and are silently skipped if included.

**These two tools are the channel surface for every notification type, not just the inbox's** —
operators are routed here for "welche Kanäle bekomme ich" in general. The one most often asked
about outside the inbox is `meeting.owner_assigned` (category `meetings`): it fires when
somebody **else** books a meeting onto the operator, or moves an existing one onto them —
until it existed, a manually booked appointment reached its owner only as a calendar invite.
Email, push and Slack are switchable; in-app stays on. Before treating a missing one as a bug,
check the deliberate silences: it does **not** fire when the owner is the person who acted, for
a meeting that is not `Scheduled` (one logged after the fact is a record, not an appointment),
or for AI-booked meetings — `meeting.agent_booked` and `meeting.agent_booking_failed` cover
those, and those three are the only meeting notification types there are.

Individual tickets are followed separately — `follow-ticket` / `unfollow-ticket` on
`0-300`, same self-scoped preview → confirm flow — and that subscription covers replies and
status changes on that one ticket, not arrivals in the inbox.

## Ask before deciding, don't decide alone

- The matter involves money or a deadline and the data situation isn't clear-cut.
- Something was promised to an employee that you can't verify.
- Multiple assignments or contracts overlap — a record filed under the wrong one lands in
  the wrong payroll run.
- An attachment is genuinely ambiguous.
- It touches termination, Mutterschutz, Elternzeit, an AU certificate (Arbeitsunfähigkeit),
  or social insurance.

## What this work doesn't fix

An overflowing inbox is often a symptom of a broken process — employees fall back to email
because the app doesn't accept the case some other way. Seventy reimbursement tickets
against zero `Reimbursement` records isn't backlog, it's a product finding, and it belongs
in the wrap-up report to the operator, not worked ticket by ticket. Always check: do the
underlying operational records even exist for what's coming in? If not, say so explicitly
instead of grinding through the tickets as if the app were the source of truth.

## Output

- Ticket count before/after, by status, for the inbox worked.
- Per cluster: how many closed (with reason) vs. tasked, and the reference numbers covered.
- Coverage check result: every remaining open ticket number appears in a task, or an
  explicit list of the ones that don't (and why).
- Product-level findings (a case type with no backing records, a recurring data error, a
  tool gap) called out separately from the ticket-by-ticket work.

## Related skills

- `→ triage-data-quality` — the broader data-quality routine when findings point beyond
  this one inbox.
- `→ merge-duplicate-companies` — merges the Contact duplicates an inbound call or WhatsApp
  message left behind before number formats were reconciled.
- `→ record-absence` / `→ build-dienstplan` / `→ approve-stundenfreigabe` — where a
  confirmed gap actually gets written, once the operator has verified it from the task.
- `→ build-automation-agent` — inbox deployments (Posteingang-Agenten): which agent runs on
  this inbox, what it is allowed to do, and how to deploy or remove one. Also the right place
  when recurring triage work here should be automated instead of repeated.
