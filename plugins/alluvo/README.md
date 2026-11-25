# alluvo – KI-Plugin für Personaldienstleister

Guided workflows for alluvo staffing-agency operators. Version 1.32.0.

The workflows are **served by the alluvo MCP server**, not shipped in this
repository: this plugin carries the trigger phrases, the assistant carries the
steps. A workflow therefore updates when alluvo deploys — there is nothing to
reinstall — and it follows your organization's plan, so a workflow outside it
answers with the plan boundary instead of instructing you to use tools you do
not have.

## Install

```
/plugin marketplace add alluvoai/ki-plugin-personaldienstleister
/plugin install alluvo@alluvoai
```

In Codex: `codex plugin marketplace add alluvoai/ki-plugin-personaldienstleister` then
`codex plugin add alluvo@alluvoai`.

Then connect the bundled MCP server with your alluvo account (OAuth) and pick
your organization. See the marketplace README for Claude Cowork and for
connecting the assistant without the plugin.

## Workflows

| Workflow | Use it when |
|---|---|
| `account-briefing` | Firma recherchieren, Kontakt nachschlagen, was wissen wir über Firma X, Termin vorbereiten — dossier on a company or contact, or prep for one call. |
| `advertise-job` | Stellenanzeige buchen, Anzeige schalten, welcher Kanal lohnt sich, Multiposting, Anzeigenbudget — channels and budget; books paid job ads with preview. |
| `analyze-website-performance` | Wie läuft die Kampagne, Web-Analyse, Website-Statistik, Absprungrate, Wer ist gerade auf der Website — web and Talent Hub analytics, funnel, Web Vitals. |
| `bench-check` | wer ist verleihfrei, Bank prüfen, wer hat keinen Einsatz, wessen Einsatz läuft aus, freie Mitarbeiter — who is unassigned now or soon, by urgency. |
| `build-automation-agent` | Automatisierungs-Agent bauen, KI-Bericht einrichten, Agent auf Posteingang setzen, Prompt ändern — AI automation agents, schedules, instructions. |
| `capture-staffing-request` | neuer Personalbedarf, Anfrage aufnehmen, Kundenbedarf erfassen, Stelle anlegen, Abteilung archivieren — capture a new staffing request; departments. |
| `change-employer` | Arbeitgeberwechsel, Gesellschaft wechseln, in andere GmbH versetzen, Mitarbeiter umhängen — move an employee to another GmbH of the group. |
| `check-out-session` | Session auschecken, Session an die Entwickler übergeben, Session exportieren — hand this AI session and its transcript to the alluvo developers. |
| `coordinate-sales` | Vertriebsübersicht, Umsatzprognose, Forecast, Pipeline-Review, BDRs koordinieren — pipeline, forecast, BDR performance, delegated sales work. |
| `coordinate-staffing-operations` | Dispo-Übersicht, Auslastung, auslaufende Einsätze, offene Bedarfe, Disponenten koordinieren — dispatch overview and dispatcher follow-up. |
| `daily-briefing` | was steht heute an, Tagesbriefing, mein Tag, Morgenbriefing — today's meetings, tasks, replies and priorities. |
| `define-icp` | Wunschkunde, ICP definieren, welche Unternehmen passen zu uns, Zielkundensegment — define and apply Ideal Customer Profiles. |
| `enrich-contacts-from-activities` | Kontakte anreichern, Kontaktdaten aus Aktivitäten, E-Mail-Signatur auslesen, WhatsApp-Einwilligung, Anrede festlegen — contact data from activities; consent, du/Sie. |
| `lead-radar-prospecting` | Lead-Radar, Agentur für Arbeit, Bundesagentur Jobsuche, offene Stellen im Umkreis — BA vacancies and hiring employers; import or export. |
| `manage-client-portal-access` | Kundenportal-Zugang, Portal-Zugang einrichten, Kunde soll Stunden im Portal freigeben, Portalzugang entziehen — invite client contacts, roles, revoke. |
| `manage-company-website` | Website erstellen, Website ändern, Website live schalten, Website übersetzen, Landingpages vorschlagen — company website: build, go live, edit, translate, SEO pages. |
| `manage-contract-lifecycle` | Rahmenvertrag anlegen, Einsatzvertrag erstellen, AÜV abschließen, Vertrag stornieren, Abrechnungszeitraum — contracts, §11 AÜG notice, billing, invoice account. |
| `manage-data-retention` | Löschliste, fällige Löschungen, Löschsperre, Bewerber löschen — deletion list: due steps, holds, consents, two-stage erasure. |
| `manage-deals` | Deal anlegen, Verkaufschance, Deal gewonnen, Deal verloren, offene Deals — create, move, win (signature proof), lose or reopen deals. |
| `manage-inbox` | Inbox aufräumen, Tickets bearbeiten, Ticket weiterleiten, Web-Chat einrichten, Geschäftszeiten ändern — shared-inbox tickets, settings, web chat. |
| `manage-invoices-and-payments` | Zahlung erfassen, offene Posten, Gutschrift erstellen, Mahnung schicken, Rechnung erstellen — invoices, payments, e-invoices, dunning. |
| `manage-meta-ads` | Werbeanzeigen, Kampagnen-Performance, Lead Ads erstellen, Leads kommen nicht an — Meta campaigns, creatives, lead mapping, conversion tracking. |
| `manage-outreach-enrollments` | Unternehmen in Sequenz aufnehmen, Outreach starten, Sequenz pausieren, aus Sequenz entfernen — outreach sequence enrollments. |
| `manage-reimbursements` | Beleg einreichen, Belege abgleichen, doppelt eingereicht, Spesen freigeben, Reisekosten prüfen — receipts and travel expenses: file, approve, pay. |
| `manage-shift-schedules` | Dienstplan erstellen, Schichten anlegen, Schicht stornieren, Schicht umbesetzen, Dienstplan veröffentlichen — compliant shift schedules. |
| `manage-staffing-demand` | Bedarf bearbeiten, Personalbedarf bearbeiten, Personalbedarf managen — work an existing staffing demand: status, next steps, fitting people, profile proposals, job postings. |
| `manage-timesheet-approvals` | Stundenfreigabe, Stundenzettel prüfen, Stunden genehmigen, Stundenkorrektur, falscher Unterzeichner, Freigabe zurücknehmen — review, release, correct timesheets. |
| `market-talent-profiles` | Profilvertrieb, Mitarbeiter platzieren, Bank vermarkten, Kandidatenprofil verschicken — market one available employee to target companies. |
| `match-bench-to-clients` | matche die Bank, Einsätze für verleihfreie Mitarbeiter, wer passt zu welchem Kunden, Bestandskunden matchen — bench to existing clients. |
| `merge-duplicate-records` | Dubletten bereinigen, doppelte Firmen zusammenführen, doppelte Kontakte zusammenführen, Kontakt-Dublette — find, preview, merge duplicates. |
| `message-employee` | Mitarbeiter anschreiben, Mitarbeiter fragen, Nachricht in die App schicken, beim Mitarbeiter nachfragen — one question by app or email; reply as ticket. |
| `onboard-new-employee` | Mitarbeiter onboarden, Personalfragebogen schicken, Stammdaten übernehmen, Passwort zurücksetzen — questionnaire, master data, bank, app access. |
| `plan-marketing-campaign` | Kampagne planen, Kampagne anlegen, UTM-Links, Kampagne auswerten — campaign record, validated UTM links, performance per campaign. |
| `process-call-notes` | Gesprächsnotiz erfassen, Notiz erfassen, Call nachbereiten, Follow-up schreiben — call notes or transcript, tasks, follow-up; also for a new staffing need. |
| `prospect-companies` | Zielfirmen finden, passende Firmen für Mitarbeiter, Unternehmen in der Nähe, wer kommt für Mitarbeiter in Frage — target companies for one employee. |
| `publish-job-posting` | Stellenanzeige veröffentlichen, Stellenanzeige anlegen, Job auf der Karriereseite, bei der Arbeitsagentur veröffentlichen — Talent Hub job, BA, Google for Jobs. |
| `record-absence` | Krankmeldung eintragen, Urlaub buchen, AU-Bescheinigung hochladen, Resturlaub prüfen — sick notes, vacation, absences, vacation balance. |
| `research-staffing-agencies` | Erlaubnisregister, AÜG-Erlaubnis, wer darf verleihen, Wettbewerber in meiner Region — agencies and permit holders in the AÜG register. |
| `setup-booking-link` | Buchungslink anlegen, Terminlink erstellen, Buchungslink aktivieren, keine Termine, Terminlink schicken — create, repair or share a booking link. |
| `setup-cold-outreach-mailbox` | Kaltakquise-Postfach einrichten, Signatur anlegen, Tracking ausschalten, E-Mail-Signaturen — cold-outreach sender, signatures, tracking. |
| `setup-organization` | Organisation einrichten, alluvo einrichten, Onboarding durchgehen, was fehlt noch im Setup — tenant onboarding step by step. |
| `setup-talent-hub-chat` | Chat im Talent Hub einrichten, Chat im Talent Hub fehlt, Chat-Button erscheint nicht, Bewerbungs-Chat — set up or repair the applicant chat. |
| `triage-data-quality` | Datenqualität prüfen, Issues triagieren, nach Import aufräumen, Rollenkatalog aufräumen, Profil aufräumen — data-quality findings, role-catalogue gaps. |
| `using-alluvo-operator` | wie funktioniert, was kannst du, wie fange ich an, welche Workflows gibt es, Berechtigung prüfen — entry point: which workflow fits, conventions, access. |

Ask "was kannst du" (or install and say hello) to get the live catalogue,
including any workflow a higher Tarif would unlock.


## Freie Skills (ohne alluvo-Konto nutzbar)

| Skill | Use it when |
|---|---|
| `write-job-posting` | Stellenanzeige schreiben, Stellenausschreibung erstellen, Stellenanzeige überarbeiten, Anzeige AGG-konform machen, Stellenanzeige veröffentlichen, im Talent Hub ausschreiben — write or check a job posting (AGG, AÜG, pay transparency); works without an alluvo account. |

## Requirements

An alluvo account with MCP access. Everything runs as the signed-in user,
inside their organization, and writes are previewed before they execute.
