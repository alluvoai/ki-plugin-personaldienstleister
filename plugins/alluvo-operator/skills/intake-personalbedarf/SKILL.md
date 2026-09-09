---
name: intake-personalbedarf
description: Capture a client staffing requirement (Personalbedarf) end-to-end. Use when the operator says "neuer Personalbedarf", "Anfrage aufnehmen", "Kundenbedarf erfassen", "intake staffing requirement", "Stelle anlegen", "Bedarf von Kunde X", or when a client calls with a new placement request. Also covers maintaining the client's Abteilungen ("Abteilung archivieren", "Station stilllegen", "Abteilung lässt sich nicht löschen", "Wohnbereich aus dem Portal nehmen", "archivierte Abteilung wiederherstellen", "archive a department").
---

# Capture Personalbedarf (Intake)

## Purpose
Fully capture a new client request (Personalbedarf) as a **StaffingDemand**
(`0-415`) — from the minimum matchable data through role and timeframe to
follow-up tasks for open items.

> **MUTATING.** Every write goes through `manage-model` two-stage: preview
> (`confirmed: false`) → operator approval → `confirmed: true`.

## Prerequisites
Uses only the connected alluvo MCP tools (`mcp__alluvo__*`). No tokens, no shell.
Everything runs inside the operator's tenant.

> **StaffingDemand (`0-415`) is the single write path for new demand.** ALL new customer
> demand — however it arrives: operator intake by phone or email, inbound mail the agent
> triages, client-portal booking, stazzle sync, guest request via a public profile page —
> is a `StaffingDemand` (`0-415`), created with `manage-model`.
>
> **StaffingRequirement (`0-102`) is the LEGACY predecessor.** Read it for historical
> records and existing outreach/proposal business — that stays fully available via
> `search-model` / `get-model` / `query-model`. **Never create new demand there.** That rule
> is now yours to keep, not the server's to enforce: `manage-model` create/update on `0-102`
> used to be rejected outright, and today it **goes through**. A misrouted write no longer
> errors — it silently files a legacy record that never appears in any `0-415` view, while
> kicking off the old contact-matching pipeline instead of the demand matcher. So do not
> offer `0-102` as a fallback when a `0-415` write fails; fix the `0-415` payload instead.
> Correcting an *existing* legacy `0-102` record with `manage-model` `action: "update"` is
> legitimate (same two-stage preview) — confirm with the operator that they mean the historic
> record and not a new Bedarf before you write. (The former `StaffingRequest` (`0-127`) and
> `StaffingRequestMatch` (`0-410`) models no longer exist — those model type IDs are gone
> from MCP entirely and return not-found. Do not reference them.)
>
> There is no `manage-staffing-requirement-prompt` — that prompt was removed from the MCP
> server. Drive the intake with `manage-model` as described below.
>
> **A machine-channel demand often has no linked Abteilung — read the reported name.**
> `StaffingDemand` carries the Abteilung twice: `company_department_id` (the relation to a
> `CompanyDepartment` `0-107`) and `company_department_text` (label "Gemeldete Abteilung" /
> "Reported Department") — the name exactly as the inbound source reported it. The stazzle
> sync no longer creates Abteilungs-Stammdaten: it links an existing department only when the
> name matches one on the same company (case- and whitespace-insensitive), otherwise
> `company_department_id` stays null and only the text survives. So when you read or
> summarise such a demand, take `company_department_id` → falls back to
> `company_department_text`, and **do not report a missing linked Abteilung as missing data**
> — the name is usually there, just as text. Matching already reads it the same way, so a
> text-only Abteilung does not degrade the candidate list. If the demand later needs a real
> Abteilungs-Datensatz (an Einsatz requires `company_department_id`), confirm the department
> with the operator before creating a `0-107` — never turn a reported string into master data
> on your own.
>
> **An Abteilung can carry Schwerpunkte — they gate the client portal, not this intake.**
> `FocusArea` (`0-369`, "Schwerpunkte": Intensivpflege, Palliativ, Beatmung, …) is a flat,
> tenant-wide catalogue maintained with `manage-model` — `name` required and **unique
> tenant-wide**, plus optional `code` (also unique), `description`, `is_active`, `sort_order`.
> Search it with `search-model` (`0-369`) before creating anything; reading it needs the
> `focus-areas.view` permission. Attach the Schwerpunkte of a `CompanyDepartment` (`0-107`)
> with `manage-association`: `action: "attach"` (or `"bulk-attach"` with `target_ids`, max 50),
> `source_type: "0-107"`, `source_id: <department>`, `target_type: "0-369"` — two-stage as
> always (`confirmed: false` preview → operator approval → `confirmed: true`). `detach` /
> `bulk-detach` remove them again.
>
> What they do: a person who declared one of the department's **active** Schwerpunkte a
> **No-Go** is neither shown nor bookable for that Abteilung **in the client portal**. Nothing
> else changes — the `0-415` Bedarf is not filtered, matching still proposes that person, and
> Dienstplan and AÜV ignore no-gos entirely. `is_active: false` takes a Schwerpunkt out of
> effect immediately and is the normal way to retire one; deleting is the exception. Setting a
> person's No-Go: `→ onboard-new-employee`. The MCP prompt `manage-focus-areas-prompt`
> (arguments `company_department_id`, `contact_id`) carries the full rules.
>
> **Retiring an Abteilung: archive it, don't delete it.** A `CompanyDepartment` (`0-107`) that
> carries Einsätze, Einsatzverträge, Personalbedarfe or Schichtvorlagen **cannot** be deleted —
> `delete-model` comes back with those reference counts, which is a referential block, not a
> missing permission. The sanctioned exit is the `archive` record action on `0-107` via
> `manage-record-action` (two-stage: `confirmed: false` preview → operator yes →
> `confirmed: true`; `unarchive` brings it back). It only sets `archived_at` — existing
> Einsätze, Verträge, Schichten and Schwerpunkte stay exactly as they are.
>
> Two independent flags on an Abteilung, and they are not interchangeable:
>
> - **`is_active`** — writable with `manage-model`, the **operator's** toggle. This is the one
>   that actually takes the Abteilung out of the Einsatz- and Dienstplan-Kandidatenpool.
> - **`archived_at`** — action-only (never writable via `manage-model`, which silently drops
>   it), the **client's** "raus aus meiner Liste, Historie behalten" flag. In the Kundenportal
>   an archived Abteilung disappears from the Abteilungsliste (it moves to the **"Archiviert"**
>   tab, where the row's `unarchive` action restores it) and drops out of the portal booking
>   picker. Customers can archive/unarchive there themselves with `client.departments.manage`.
>
> **Archiving does not lock the Abteilung on our side** (api#4210 tracks the mismatch). MCP
> reads still return it — `archived_at` is not a default display column, so nothing warns you —
> `manage_einsatz` still accepts its `company_department_id`, and Dienstplan resolution still
> counts it as a candidate. So whenever you resolve an Abteilung by name for an Einsatz or a
> Dienstplan, read `archived_at` (`fields: ["name", "code", "archived_at"]`, or filter
> `is_null` / `is_not_null`) and have the operator confirm before a retired ward lands on a
> contract: the Abteilung is printed into the signed AÜV and the §11 Abs. 2 AÜG
> Einsatzmitteilung. Full mechanics: `→ using-alluvo-operator`.
>
> **Email intake includes the operator's own mailbox.** Where the mailbox agent is enabled
> (tenant feature + per-mailbox setting), an inbound email on a *personal* 1:1 mailbox that
> describes a Personalbedarf **auto-creates a `StaffingDemand` (0-415)** — duplicate-checked
> per company, status `signal` (no concrete dates) or `qualified` — and matching then
> auto-drafts a candidate proposal that waits for the mailbox owner's approval. So when the
> request the operator is dictating **arrived by email**, the demand (and possibly a proposal
> draft awaiting approval) may already exist — see the duplicate check in step 1. Shared
> company inboxes are NOT covered by the agent; demand mails there still need this intake
> flow.
>
> **Mass-circular staffing inquiries (Rundmails an den Verteiler) get an auto-redirect
> reply.** When the tenant has configured a redirect address — `manage-settings`, group
> `ai_takeover`, key `staffing_inquiry_redirect_email` (nullable email) — the mailbox agent
> answers a mass-circular staffing inquiry that lands on a *personal* 1:1 mailbox with a
> deterministic canned reply (never AI-generated) asking the sender to send future inquiries
> to that address instead. On the **third** such circular from the same contact it creates a
> call task for that contact, so someone phones them and asks them to update their Verteiler
> (one open task at a time — no duplicates). Fail-closed: while the key is blank the whole
> auto-reply/3-strikes flow does nothing, and there is no fallback address. The inquiry is
> still classified and demand-captured as usual — the auto-reply is additional, not a
> replacement for intake. An operator changes the address via `manage-settings`
> `action: "update"`; the tool writes immediately (no `confirmed` flag), so show the
> operator the exact key and value and get their go-ahead before calling it.

## Before you write — gather this information from the client

| Information | Maps to | Example |
|---|---|---|
| **Client (company)** | `company_id` (required) | Marienhospital GmbH |
| **Deployment site / Einsatzort** | `client_site_id` | Gelsenkirchen, Station 3 |
| **Role** | `staffing_role_id` | Gesundheits- und Krankenpfleger |
| **Headcount** | `headcount` (defaults to 1) | 2 |
| **Timeframe** | `valid_from` / `valid_until` | 01.07.–31.08.2026 |
| **Weekly hours** | `weekly_hours` | 38.5 |
| **Requesting contact / department** | `contact_id`, `company_department_id` | Frau Ackermann, Pflegedienstleitung |
| **What is needed, in words** | `title` (required), `description` | "2× GuK Nachtdienst Station 3" |
| **Special requirements** | `description` | Own vehicle; check AÜG § 1 Abs. 1b if applicable |

> **A demand is only useful if it can be matched.** Missing any of these makes it silently
> unworkable — the operator only finds out when matching reports *"keine Rolle zuordenbar"*:
>
> - `company_id` **and** `client_site_id` — the Einsatzort is a specific work site
>   (ClientSite, `0-341`), not just the company. **Never guess** among a company's several
>   sites; if you cannot resolve one, say so and flag the gap.
> - `staffing_role_id` — resolve the qualification the client named with **`resolve-staffing-role`**
>   (free-text → formal StaffingRole `0-100`) rather than guessing via `search-model`. Without
>   it, matching, the customer proposal email and the AÜV draft all fail.
> - `valid_from` (+ `valid_until` for a period) — without a start date the demand stays
>   `signal` instead of becoming `qualified`, and matching never runs at all.
>
> If items are still open, create the demand anyway and add a task for the outstanding
> points (step 4) — a `signal` demand is a legitimate in-progress state.

## Steps

### 1. Check for an existing demand first
The same need routinely arrives worded differently across several mails, and the backend
dedupes the same way. Before creating anything, `search-model` on `0-415` for the company and
look for an **open** demand (`status` not in `covered` / `lost` / `cancelled`) on the same
**company + role + overlapping date window**. If one exists, **update that record** instead of
creating a second — and if it already carries a proposal draft awaiting approval, point the
operator there.

> **"One Bedarf" is no longer "one row" — demands are grouped.** Lines are tied together by
> `demand_group_id`, a self-FK: the **anchor** line carries it as **null** and lists the rest
> under its `children` relation; a child always points directly at an anchor, never at another
> child. A newly created line is folded into an open anchor automatically when it matches on
> company + Abteilung (the linked `CompanyDepartment`, else the reported text) + Rolle (the
> linked `StaffingRole`, else the reported title) + a period that overlaps or sits within a day
> of the anchor's. Only open demands are eligible anchors.
>
> Three consequences for intake:
> - When you find a candidate duplicate, check whether it is an anchor or a child and take the
>   operator to the **anchor** — that is where the group's proposal and matching live.
> - A company showing many `0-415` rows is not necessarily a pile of distinct Bedarfe. Read
>   `demand_group_id` on the rows you fetched and group them before telling the operator how
>   many open Bedarfe there are.
> - Grouping happens **only on create**, never on update. So correcting a line's role, Abteilung
>   or period does not re-parent it — if a line ended up in the wrong group, say so rather than
>   trying to fix it by editing the fields the grouping was derived from.
>
> Proposal drafting dedupes over the same group **plus** a 7-day window on the same Kontakt +
> Rolle + Einsatzort, so a duplicated Anfrage no longer produces one mail per line. If the
> operator expects a second proposal for what is really the same Bedarf, that suppression is the
> reason — not a failed matching run.

### 2. Resolve the role and the Einsatzort
- `resolve-staffing-role` with the client's own wording (`qualification_freetext`) → take the
  returned `role.id`. It is read-only: it reports the match, you apply it. It reports
  *ambiguous* or *no confident match* rather than guessing — surface that to the operator
  instead of picking a role yourself. It reports the role only: **neither** its Gruppe nor its
  `level` come back, so read those off `0-100` if you need them.

> **The role you pick sets a floor, not a fence — #NachUntenGehtImmer.** The scoring below is
> what the matching workspace (`/staffing/matching`) applies when an operator runs it — that
> engine is live even though automatic matching is off (step 6), so the role you record still
> decides who surfaces. Matching lets a
> higher-qualified candidate cover a lower requirement, never the reverse: same role group and
> `level` ≥ the demanded role's level scores **0.8** (a valid downward substitution, decaying by
> 0.05 per extra level of distance beyond one and floored at 0.6), below it **0.0**. If the
> demand carries several roles of one group, the **lowest** of their levels is what counts —
> adding a stricter role does not exclude anyone who meets a looser one, so pick the
> qualification the client actually named rather than hedging upward.
>
> Two unclassified cases, and they are **not** symmetric:
> - The **demanded** role has no `level`/`staffing_role_group_id` → every same-group candidate
>   collapses to a flat **0.6** and the shortlist gets vaguer.
> - A **candidate's** role has no `level` while the demanded one has → **0.0**, i.e. dropped
>   outright, not blurred. An unclassified person is never treated as possibly-qualified.
>
> Flag either instead of swapping in another role to compensate (`→ triage-data-quality`
> step 3c cleans the catalog up).
>
> **The role's Fachrichtung now shapes the shortlist too — pick it deliberately.** Besides
> Gruppe and Level, a `StaffingRole` carries a `specialty` (Intensiv, Anästhesie, OP, Notfall, …),
> and the demand's role passes it into matching. A candidate of the same Gruppe and a sufficient
> Level but the **wrong** Fachweiterbildung now scores **0.4** on the role feature instead of
> counting as an exact hit, and a covering specialty bridges *across* Gruppen at 0.5. This is a
> downgrade, never an exclusion — but combined with the minimum score of 25 it can be the
> difference between a candidate surfacing and not. So resolve the role the client actually
> named: choosing
> a Notfall role when the client just said "Intensivpflege" quietly demotes every Intensiv
> candidate. If the client genuinely has no Fachrichtung requirement, pick the role without one.
>
> Where a demand names several roles of one Gruppe with **different** specialties, the Gruppe is
> treated as having no specialty requirement at all (the same permissive fallback as an un-leveled
> Gruppe) — so hedging by adding a second, differently-specialised role does not narrow the
> shortlist, it widens it.
- `search-model` on ClientSite (`0-341`) for the company to find the Einsatzort. Confirm the
  right one with the operator when there is more than one.

### 3. Create the demand
`manage-model` on `0-415`, `confirmed: false` first — show the operator the full preview,
then repeat with `confirmed: true`. Confirm the exact writable fields with
`get-model-schema` (`context: create`) before calling; fields not in the schema are silently
dropped.

`status` defaults to `signal`. Leave it there and lift it with the actions in step 5 rather
than setting it by hand — the status transitions are what open the demand for work.

### 4. Task for open points
If anything is still missing (Einsatzort, role, dates), `manage-task` a follow-up for the
operator naming the exact gap, so the demand does not sit unmatchable.

### 5. Move it forward
`manage-record-action` on `0-415`:
- `qualify` — Signal → Qualified. **Rejected unless `valid_from`, `staffing_role_id` and
  `client_site_id` are all set**, and only from Signal.
- `activate` — Qualified → Active, once a Disponent starts actively working it.

### 6. Find the candidates yourself — nothing matches this demand for you
> **Automatic matching is switched off (Pennant flag `AutomaticDemandMatching`, off by
> default per tenant). A qualified demand produces no shortlist on its own.** While the flag
> is off, creating or qualifying a `0-415` files **no** `StaffingDemandMatch` (`0-416`) rows,
> **no** "Personalbedarf prüfen" task, **no** "Anschlusseinsatz prüfen" task and **no**
> auto-drafted candidate-proposal email. In Slack the demand card still appears in the
> channel, but there is no "⏳ Matching läuft" placeholder and no "✅ Matching abgeschlossen"
> reply — so there is no thread to answer "biete 1 und 2 an" in. It was disabled because the
> autonomous shortlist proposed people who had reported themselves unavailable and missed the
> fachlich right person by ignoring higher, neighbouring roles.
>
> **Never tell the operator a proposal is coming.** After the intake, hand over the demand
> with the search you actually ran, or route them to a skill that does one:
> - `→ match-bench-to-clients` — the demand-side search: verleihfrei employees near the
>   Einsatzort with the required (or a higher) role.
> - `→ bench-check` — who is free in the demand's window at all.
> - `search-model` on `0-126` (EmployeeStaffingOpportunity) filtered by the client
>   `company_id` — the nightly company↔employee opportunity scoring is **not** gated and
>   stays the best standing MCP shortcut to "who fits this client".
> - The operator-driven matching workspace (`/staffing/matching`,
>   `/staffing/company-matching`) is **not** gated either — the same scoring engine runs
>   there, just on a human's explicit request. Point the Disponent at it when they want the
>   ranked list.
>
> **The demand also stays where you put it.** Nothing flips it to `NotCoverable` any more —
> a new demand (client portal included) sits in its intake status, normally `Qualified`,
> until an operator moves it. A demand still sitting at `Qualified` is un-worked, not
> un-coverable.
>
> Everything that *does* land on the demand is readable in one call: `get-timeline` with
> `subject_type: "0-415"` returns its `action` / `task` / `issue` / `ticket` / `email`
> history. Read it rather than assuming — a demand from before the shutdown, or a tenant
> with the flag switched back on, may legitimately carry matches and tasks.

## Output
- Created (or reused) Personalbedarf `0-415` with ID and summary
- Einsatzort (ClientSite) · role · headcount · timeframe · status
- Open task(s) for missing information (title · due date)
- Recommended next steps (Bench match / contract)

## Related skills
After a successful intake, consider:

- `→ match-bench-to-clients` — immediately search for verleihfreie employees who fit the Bedarf.
- `→ bench-check` — see who is verleihfrei before matching.
- `→ manage-contract-lifecycle` — once a match is agreed, create the Rahmen-/Einsatzvertrag.
