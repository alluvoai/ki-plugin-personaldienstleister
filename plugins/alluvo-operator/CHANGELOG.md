# Changelog

All notable changes to the **alluvo-operator** plugin are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning is
[SemVer](https://semver.org/).

## [Unreleased]

### Changed — 2026-09-09 `triage-data-quality`: the Kunde-ohne-Firmensitz non-fix note explains the BillingAccount (alluvo#4673)

The *Kunde ohne Firmensitz* remediation's "setting a billing address does not help" line now says
why: the Rechnungsempfänger is its own record, a **BillingAccount** (`0-447`) selected via
`billing_account_id`, and it only feeds the *Rechnungsempfänger* block — never the Vertragskopf
preamble. `billing_location_id` stays named as the retired parameter that steers callers there by
mistake.

The rest of alluvo#4673 — the `manage-contract-lifecycle` sections on `billing_account_id` — is
not landed here. That skill is now a thin stub served by the alluvo MCP server
(`get-workflow-guidance`, alluvo#4937 below); its prose lives in
`resources/mcp/workflows/manage-contract-lifecycle/SKILL.md` in the api repo and was ported there
directly (api PR [#4942](https://github.com/Doing-the-right-things/alluvo/pull/4942)) rather than
through this plugin.

### Changed — 2026-09-09 Pilot: `bench-check`, `profilvertrieb` and `manage-contract-lifecycle` are now thin stubs served by the MCP server (alluvo#4937)

The alluvo MCP server gained a core tool **`get-workflow-guidance`**
(`app/Mcp/Generic/Tools/GetWorkflowGuidanceTool.php`), the sibling of `get-tool-guidance`: where
that one serves per-tool dispatch guidance, this one serves whole multi-step operator workflows
out of `resources/mcp/workflows/<slug>/SKILL.md`. Called without arguments it returns the
catalogue of workflows the organization has — locked ones included, each with the Tarif that
unlocks it; called with `workflow: "<slug>"` it returns the guidance, as the whole body for a
short workflow or an overview plus a section index for a long one (fetch one with
`section: "<slug>"`). A workflow outside the organization's plan answers `MODULE_LOCKED`. The
server's `$instructions` now carry a "Guided workflows" index pointing at the tool, so an MCP
client finds the workflows with no plugin installed at all.

This release pilots the thin-plugin model on **three** skills. `bench-check`, `profilvertrieb`
and `manage-contract-lifecycle` keep their frontmatter unchanged — the `description` is what
Claude Code reads to decide activation, so trigger phrases are untouched — and their bodies are
replaced by the three-line stub that calls `get-workflow-guidance` and follows what it returns.
That removes ~2,700 lines of prose from what activation injects into the conversation, and the
steps now update when alluvo deploys instead of when an operator updates the plugin. The stubs
are byte-identical to what `php artisan mcp:build-operator-plugin` generates from the same
workflow sources.

The other 23 skills stay fat in this pilot. Cross-references into the three pilot skills (for
example `→ manage-contract-lifecycle`, step 6) still route correctly — following one now means
calling `get-workflow-guidance` for that workflow rather than reading a local file.

`using-alluvo-operator` documents the tool in "Fetching docs on demand" (now four mechanisms,
not three) and marks the three pilot entries in the Catalog as *guidance served by the
assistant*.

Version bumped 0.7.1 → **0.8.0** (minor: the three workflows change how their guidance is
delivered, not what they do).

### Changed — 2026-09-09 Public-facing manifests no longer carry a personal e-mail or a private repo pointer

The marketplace and plugin manifests, and both READMEs, still pointed at a private repo
(`Doing-the-right-things/alluvo-claude-plugins`) and a personal e-mail address
(`p.kremp@pinetco.com`) — fine while this repo was private, wrong once it's meant to be shared
publicly. `.claude-plugin/marketplace.json`'s `owner.email` and
`plugins/alluvo-operator/.claude-plugin/plugin.json`'s `author.email` and `repository` keys are
removed (all optional in the manifest schema); the top-level `README.md` and
`plugins/alluvo-operator/README.md` install instructions now point readers to "ask your alluvo
contact for the marketplace to add" instead of naming the private repo — the public marketplace
name isn't decided yet.

### Changed — 2026-09-08 `manage-location` ist abgelöst: Adressen laufen über `manage-address` (alluvo#4672)

Die Adress-Refaktorierung ist auf `main` **komplett** gelandet — nicht nur Phase 1. `manage-location`
ist **abgeschaltet**, und Location (`0-95`) ist gar nicht mehr über MCP erreichbar: `manage-model`,
`get-model`, `query-model`, `search-model`, `count-model` und `manage-record-action` antworten dort
mit *„not available via the generic model tools"* — ohne Hinweis auf den Nachfolger. Adressen sind
jetzt ein eigener, historisierter Datensatz (**Address, `0-446`**), der genau einem Eigentümer für
genau einen Zweck gehört.

- **`using-alluvo-operator`** bekommt einen neuen Querschnitts-Abschnitt *Addresses
  (`manage-address`)*: die fünf Eigentümer-Typen mit ihren erlaubten `purpose`-Werten (Company
  `0-3`: `headquarter`/`postal`/`billing`; ClientSite `0-341`: `site`; Contact `0-105`:
  `home`/`second_residence`/`postal`/`work`; Branch `0-73`: `branch`; CompanyJobPosting `0-160`:
  `site`), die vier Aktionen `set` / `correct` / `list` / `end` samt der wichtigen Unterscheidung
  („Umzug" vs. „Tippfehler"), und welche drei Eigentümer+Zweck-Paare überhaupt geokodiert werden
  (Contact `home`, Company `headquarter`, ClientSite/CompanyJobPosting `site`).
- **Die Adresse einer Niederlassung ist jetzt schreibbar.** Die bisherige Aussage „geht über MCP
  gar nicht, schick den Operator in die Einstellungen" ist überholt: entweder ein verschachteltes
  `address`-Objekt an `manage-model` `create`/`update` auf `0-73`, oder `manage-address`
  `action: "set"` mit `purpose: "branch"`. Korrigiert in `using-alluvo-operator` und
  `onboard-new-employee`.
- **Mitarbeitende besitzen weiterhin keine Adresse.** `model_type: "0-2"` wird abgelehnt — mit
  Verweis auf die `contact_id`. `bench-check`, `profilvertrieb`, `onboard-new-employee` und
  `enrich-contacts-from-activities` schreiben die Wohnadresse jetzt über `manage-address`
  `action: "set"` auf den **Contact** (`0-105`, `purpose: "home"`).
- **Ein nicht auflösbares Bundesland blockiert den Schreibvorgang nicht mehr.** Früher wurde ein
  `manage-location`-Create ohne auflösbare PLZ abgewiesen; `manage-address` schreibt und erzeugt
  stattdessen das hochpriorisierte Issue **Unresolvable Federal State** auf der Adresse. Nach der
  PLZ zu fragen bleibt richtig — aber „wird abgelehnt" zu sagen wäre falsch. Angepasst in
  `bench-check`, `profilvertrieb`, `onboard-new-employee`, `enrich-contacts-from-activities` und
  `triage-data-quality`.
- **`triage-data-quality`** kennt die neuen Address-Detektoren: *Unresolvable Federal State* auf
  `0-446` wird mit `manage-address` `action: "correct"` behoben (nie `set` — ein Tippfehler gehört
  nicht in die Adresshistorie), die `create_related`-Remediationen (Missing Home Address, Missing
  Headquarter Address, Missing Billing Address, ClientSite Missing Address) laufen über
  `action: "set"` mit `addressable_type` → `model_type` und `addressable_id` → `model_id`. Das
  Skill sagt außerdem, dass dieselbe Meldung parallel noch auf einer Alt-Location (`0-95`) stehen
  kann — die ist über MCP **nicht** behebbar, also Adresse korrigieren und den Altsatz benennen,
  statt einen fehlgeschlagenen Tool-Call zu melden.
- **`manage-contract-lifecycle`**: die Rubrum-Auflösung (Auftraggeber-Anschrift) stimmt wieder.
  Neu an der Spitze steht der **beim Signieren eingefrorene Snapshot** — eine unterschriebene
  Vertragsurkunde rendert nie unter einer später geänderten Firmenadresse neu. Danach der
  vertragseigene **`client_party_address_override`** (ein Freitext-Adressobjekt, keine Referenz),
  den **auch ein Einsatzvertrag eigenständig besitzt** und der dort *vor* dem des Rahmenvertrags
  greift — ein Standalone-AÜV ist damit direkt korrigierbar. Danach die Company-Adresse
  (`headquarter` → `postal` → jede andere aktuelle außer `billing`). Die vier zurückgezogenen
  Parameter `client_party_location_id`, `billing_location_id`, `selected_location_id` und
  `billing_emails` werden mit einem „did you mean"-Hinweis abgelehnt; der Rechnungsempfänger ist
  jetzt `billing_account_id` (BillingAccount, `0-447`, trägt Rechnungsadresse und E-Mail-Liste).
  Die Aussage, `create` verweigere einen Rahmenvertrag ohne „usable HQ Location", ist entfallen —
  der Vertrag entsteht ohne Sitzadresse und die Vollständigkeitsprüfung meldet es.
- **`record-absence`, `build-dienstplan`, `manage-contract-lifecycle`** benennen den Einsatzort
  für die Feiertagsauflösung jetzt korrekt als **`site`-Adresse des Einsatzbetriebs**. Dass ein
  nicht auflösbares Bundesland die **Rechnungsstellung des ganzen Laufs** blockiert (mit Nennung
  der betroffenen Einsatzbetriebe), bleibt richtig und steht weiterhin drin.
- **Bekannte Lücke, ehrlich benannt:** die Remediation *Missing Geocodes* auf einer Adresse nennt
  eine `geocode`-Aktion, die es auf `0-446` nicht gibt (alluvo#4903). `triage-data-quality` sagt
  jetzt, was tatsächlich hilft — ein echtes Feld per `correct` korrigieren, dann läuft die
  Geokodierung von selbst neu an; ist die Adresse bereits richtig, das Issue verwerfen statt einen
  scheiternden Tool-Call abzusetzen.
### Changed — 2026-09-08 „Missing Company Site Location" wird über ClientSite behoben, nicht über die Firma (alluvo#4677)

Phase 5 des Address-/BillingAccount-Refactors hat `manage-location`, den Model-Type Location
(`0-95`) und die vier Location-Parameter der Vertrags-Tools endgültig entfernt. Der
Einsatzort ist damit die **eigene Adresse des Einsatzbetriebs** — eine Firma kann gar keine
Adresse mit Zweck `site` mehr tragen (erlaubt sind nur `headquarter`, `postal`, `billing`).

- **`triage-data-quality`** beschreibt den Befund *Missing Company Site Location*
  (`App\Issues\DataQuality\Company\MissingSiteLocation`, hoch, **nicht abweisbar**) erstmals
  eigenständig: Er sieht aus wie die anderen Adress-Befunde, ist aber der einzige, dessen
  `create_related`-Ziel **ClientSite (`0-341`)** ist und nicht Address. Die Behebung sind zwei
  Schreibvorgänge in fester Reihenfolge — `manage-model` `create` des ClientSite mit
  `company_id` + `name`, danach `manage-address` `set` mit `model_type: "0-341"`,
  `model_id: <neue client_site_id>`, `purpose: "site"`.
- Zwei Fallen stehen ausdrücklich dabei: `manage-address` auf `0-3` mit `purpose: "site"` wird
  abgelehnt (*„Purpose 'site' is not allowed for Company. Allowed: headquarter, postal,
  billing"*), und **Schritt 1 allein schließt den Befund nicht** — der Detektor greift erst,
  wenn einer der ClientSites eine **aktuelle** `site`-Adresse trägt.

Nicht betroffen: die entfernte Assoziation Contact → Location und die Umbenennung der
Kundenportal-Berechtigung `client.locations.manage` → `client.addresses.manage` kommen in
keinem Skill vor.

### Changed — 2026-09-08 Outreach-Enrollment akzeptiert jedes verbundene Postfach, nicht nur Gmail (alluvo#4854)

Die Postfach-Voraussetzung von `manage-outreach-enrollment` ist nicht mehr an Google gebunden:
`create` und `bulk-enroll` prüfen jetzt, ob das Postfach **senden kann**, nicht ob es Gmail ist.
**Gmail und Outlook / Microsoft 365 erfüllen die Bedingung gleichermaßen** (IMAP-Verbindungen
können nicht senden und zählen nicht).

- **`enroll-outreach`** nennt die Voraussetzung erstmals überhaupt: das Tor greift vor allem
  anderen — auf `create` scheitert schon die `confirmed: false`-Vorschau — und es gilt für den
  **effektiven Absender** (`sender_user_id`, sonst der angemeldete Nutzer). Die Fehlermeldung
  lautet jetzt `… must connect a mailbox before enrolling. Go to Settings → Email to connect.`
  (vorher „must connect a Gmail account …"), bei gesetztem `sender_user_id` mit dessen Namen
  statt „You".
- **`head-of-sales`** (Delegation an einen BDR) und **`profilvertrieb`** (Schritt 6a) halten
  fest, dass `sender_user_id` die Voraussetzung auf diesen Nutzer verschiebt — das eigene
  Postfach deckt das fremde nicht ab.

Operator-Anleitungen sollen niemanden mehr auf „Gmail verbinden" verweisen; ein
Outlook-Postfach öffnet die Sequenz genauso.

### Changed — 2026-09-07 `merge_employee` verlangt `acknowledge_relations`, Preflight zählt jede Tabelle (alluvo#4892)

Die Mitarbeiter-Zusammenführung (`merge_employee` über `manage-record-action`) hat ein zweites Tor
bekommen, und ihr Preflight zählt jetzt alles statt fünf handgepflegter Relationen:

- **`acknowledge_relations: true` ist Pflicht**, sobald die Dublette Lohn-, Arbeitszeit- oder
  Rechtsunterlagen trägt (`absence_periods`, `bank_accounts`, `compensation_components`,
  `employee_documents`, `employment_periods`, `invoices`, `payslips`, `reimbursements`,
  `salaries`, `shift_assignments`, `sick_leave_requests`, `tax_profiles`, `time_entries`,
  `timesheets`, `vacation_requests`). Ohne das Flag verweigert der bestätigte Lauf und nennt jede
  betroffene Tabelle mit Zeilenzahl. Eine leere Dublette merged weiterhin allein mit
  `data.confirmed: true`. `merge_candidate` hat kein solches Flag.
- **Der Preflight ist schemabasiert**: er zählt jede Tabelle, die auf die Dublette zeigt (~60
  Kandidaten statt fünf), und jede Zeile ist nach **Tabellenname** benannt (`timesheets`,
  `employee_vehicle`) — feste Schlüssel wie `staffing_experiences` oder `assignment_contracts`
  gibt es dort nicht mehr.
- **Wo die Zahlen stehen**: im schreibfreien Lauf der Aktion selbst (`confirmed: true` +
  `data.confirmed: false`) unter `Response Data` — `columns_moved`, `relations_repointed`,
  `needs_acknowledgement`, `unique_collisions`, `open_decisions` (alluvo#4894). Für
  `merge_candidate` gilt das **nicht**: dort bestätigt der Preview nur, dass der Aufruf sauber
  ist, und der Plan kommt weiter aus `preview-merge` auf dem Kontakt-Paar.
  `merge-duplicate-companies` sagt das jetzt so.

`merge-duplicate-companies` (Schritt 3a) und `triage-data-quality` (`duplicate_employee`) führen
den Operator entsprechend: erst die Zählung zeigen, dann bestätigen lassen, dann das Flag setzen —
das Flag vorsorglich mitzuschicken, um die Verweigerung zu umgehen, hebelt das Tor aus.

### Changed — 2026-09-07 Top-Level `confirmed: false` ist bei `manage-record-action` immer ein schreibfreier Preview (alluvo#4843)

Der Preview-Zweig von `manage-record-action` (`operation: "execute"`) schreibt nicht mehr. Bisher
nahm ein explizites `data: { confirmed: true }` bei Top-Level `confirmed: false` den **Write**-Zweig
der Aktion — unter einer `# Preview:`-Überschrift und ohne Hinweis darauf, dass geschrieben wurde.
Jetzt gilt: Top-Level `confirmed: false` (oder weggelassen) erzwingt `data.confirmed: false`, echot
das unter `## Data to submit` und sagt dazu, dass der gesendete Wert ignoriert wurde.
`data.confirmed` zählt nur noch auf dem Top-Level-`confirmed: true`-Zweig — dort ergibt ein
ausdrückliches `data.confirmed: false` weiterhin den schreibfreien Preview der Aktion. **Zum
Ausführen also Top-Level `confirmed: true` senden; `data.confirmed` allein reicht nicht.**

- `approve-stundenfreigabe` (`correct_signer`) dokumentierte genau die alte Kombination als
  Schreibpfad — korrigiert.
- `manage-contract-lifecycle` (`end_contract` / `end_assignment`): „ein explizit gesetztes
  `data.confirmed` gewinnt in beide Richtungen" gilt nicht mehr; die Aufruf-Tabelle hat jetzt die
  Zeile für Top-Level `false` + `data.confirmed: true`.
- `build-dienstplan` (`reassign_shifts`): dieselbe Präzedenz-Korrektur. Außerdem richtiggestellt,
  dass Top-Level `confirmed: false` den Umbesetzungsplan sehr wohl berechnet (unter
  `## Action Preview`) — der Umweg über `data.confirmed: false` ist eine Variante, keine Pflicht.
- `merge-duplicate-companies` (`merge_employee` / `merge_candidate`): Präzedenz auf den
  Top-Level-`true`-Zweig eingegrenzt. Dass es dort auf einem Top-Level-`false`-Aufruf keinen
  Preflight gibt, bleibt richtig — diese beiden Aktionen haben keinen eigenen Preview-Zweig.
- `using-alluvo-operator` bekommt den Vertrag als eigenen, übergreifenden Abschnitt.
### Changed — 2026-09-07 MCP-Tools werden pro Mandant nach Modul geladen — `MODULE_LOCKED` statt „not found" (alluvo#4631)

Der MCP-Server (Version 1.8.0) lädt Tools, Prompts und Resources ab sofort **pro Mandant** anhand
der Modul-Freischaltung. Ein Tool, dessen App der Mandant nicht freigeschaltet hat, fehlt komplett
in `tools/list` — ein in einem Skill genannter Toolname kann also legitim nicht existieren. Wird er
trotzdem aufgerufen, kommt kein generisches „not found" mehr, sondern ein JSON-RPC-Fehler mit
`error.data.code = "MODULE_LOCKED"`, dessen (bewusst deutsche) Meldung Tool, Modul, nötigen Tarif,
aktuellen Tarif und einen Testphasen-Link nennt — sie ist zum wörtlichen Weiterreichen an den
Operator gedacht. Ein echter Tippfehler bleibt ein normales „not found". Neu lesbar: `manage-apps`
`action: "modules"` (Tarif, Testphase samt Enddatum und Apps je Modul) sowie der Abschnitt
„Your Modules" in jeder `get-tool-guidance`-Antwort. Beide Tools sind Core und immer verfügbar.

- `using-alluvo-operator`: neuer Abschnitt „A tool is missing, or answers `MODULE_LOCKED`" — was das
  Fehlerbild bedeutet, wie man es prüft (`manage-apps` `action: "modules"`, `get-tool-guidance`),
  dass die deutsche Meldung unverändert weitergegeben wird, und eine Tabelle, welches Modul die
  gegateten Tools besitzt (Disposition & Verträge, Vertrieb, Recruiting, Service & Inbox,
  KI & Automatisierung). Dazu der Hinweis, dass Basis-Modul-Apps (`get-issues-overview`,
  `manage-duplicates`, `query-analytics`, `manage-analytics-goal`, `get-news-readership`) nie am
  Tarif hängen, aber abgeschaltet sein können.
- `manage-meta-ads`, `build-dienstplan`, `clean-inbox`, `enroll-outreach`, `build-automation-agent`:
  je eine Voraussetzung, welches Modul das tragende Tool besitzt und dass bei `MODULE_LOCKED` die
  Meldung weitergereicht wird, statt den Workflow von Hand zu umgehen.
- `bench-check`, `match-bench-to-clients`, `onboard-new-employee`, `profilvertrieb`: `get-profile`
  gehört zum Modul **Recruiting** — jeweils mit dem Weg, der ohne das Tool bleibt (Bench-Liste ohne
  Completeness, Qualifikationen über `query-model`, Onboarding ohne Profilansicht, Pitch ohne
  teilbaren Profillink).

### Changed — 2026-09-07 `manage-1on1-email` `update` ist berechtigungsgeprüft und zieht den Primary Contact mit (alluvo#4780)

`action: "update"` prüft ab sofort die Email-Policy, **bevor** der Entwurf geladen oder geschrieben
wird: nötig ist `emails.edit` auf dem Record **oder** `emails.create` plus Eigentümerschaft am
Entwurf. Sonst kommt `You do not have access to update this email.` und es wird nichts geschrieben —
vorher konnte jeder Aufrufer Betreff, Body und Empfänger eines fremden Entwurfs allein über die ID
umschreiben. Der Gate läuft vor der 1:1-Typ- und der Draft-Status-Prüfung. Zweitens: wird bei
`update` der erste Empfänger in `to_emails` getauscht, löst das Tool den Primary Contact aus der
neuen Adresse neu auf und meldet das (`**Primary contact:** relinked to …` bzw. `… unlinked — no
contact carries the new first recipient's address …`). Das entscheidet, auf wessen Timeline die Mail
landet und wessen Firmen-Opt-out geprüft wird.

- `profilvertrieb` (Schritt 6b, der Referenzblock für `manage-1on1-email`): neuer Punkt zum
  Berechtigungs-Gate auf `update` — inklusive der Folge, dass die dokumentierten Reparaturpfade
  („der Fix ist `action: update` auf derselben `email_id`") nur auf eigenen Entwürfen greifen. Der
  `to_emails`-Punkt bekommt das Relink-Verhalten samt seiner schmalen Grenzen (kein Primary Contact
  bei `reply`/`forward`-Entwürfen, `alternative_emails` sind kein Wechsel, eine von Hand gesetzte
  Verknüpfung bleibt stehen, eine nur über den alten Kontakt hängende Firma wird gelöst) und dem
  Hinweis, dass über MCP die Adresse entscheidet — die Aktion nimmt kein `contact_id`.
- `call-summary`: der Engagement-Disclosure-Reparaturpfad verweist jetzt darauf, dass `update` den
  eigenen Entwurf voraussetzt.

### Changed — 2026-09-06 Notizen gehen auf jeden Record-Typ, der Notizen trägt (alluvo#4770)

`manage-activity` nimmt für `activity_type: note` jetzt jeden Record-Typ an, der Notizen führt —
abgeleitet aus den Modellen selbst (`ModelRegistry::getNoteableIds()`), nicht mehr die vier fest
verdrahteten `0-105` (Kontakt), `0-3` (Firma), `0-30` (Rahmenvertrag), `0-31` (AÜV). Heute kommt
damit vor allem der **Stundennachweis** (`0-426`) dazu; die Liste wächst ohne Plugin-Änderung mit.
`call` und `meeting` bleiben unverändert auf Identitäten + Verträgen. Gate für die neuen Subjekte
ist `view` auf dem Record über dessen Policy, nicht `contacts.edit` / `companies.edit` — eine Notiz
hängt am Datensatz, ohne ein Feld daran zu ändern. Zurücklesen geht über `get-timeline` mit
demselben `subject_type` / `subject_id`.

`approve-stundenfreigabe` sagte bisher das Gegenteil („Notes still do not attach to a
Stundennachweis over MCP") und schickte einen Vermerk zum Zeitraum in die Tages-**Bemerkung** oder
den `review_note` einer Klärung; der Abschnitt beschreibt jetzt den Notiz-Weg, grenzt ihn gegen
die beiden weiterhin richtigen Textfelder ab und hält fest, dass `follow_up_task` hier funktioniert
(`0-426` trägt auch Aufgaben), auf einem nur-noteable Record dagegen vorab abgelehnt wird.
`using-alluvo-operator` bekommt die passende Routing-Zeile („Notiz an den Stundennachweis"),
inklusive des Hinweises, dass der Umweg über den verknüpften Kontakt entfällt. `call-summary` hält
fest, dass nur Notizen diese weitere Reichweite haben.
### Added — 2026-09-06 Slack-Companion: Gruppe `slack` mit `channel_instructions` (alluvo#4778)

`manage-settings` führt jetzt die Gruppe **`slack`** mit `companion_enabled` (bool, Default `true`,
per-Tenant-Kill-Switch für den `@alluvo`-Bot) und `channel_instructions` (Liste, max. 100 Einträge).
Ein Eintrag ist `{ channel_id, channel_name, instructions }`: `channel_id` (max. 64 Zeichen) ist
Pflicht und der Schlüssel, auf den gematcht wird, `instructions` (max. 2000 Zeichen) ist Pflicht,
`channel_name` ist optional und reines Anzeigefeld — ein Rename in Slack invalidiert den Eintrag
nicht. Für `channel_instructions` gibt es **keine Einstellungsseite**; MCP ist der einzige
Schreibweg. Der Text landet im statischen Block „Anweisungen für diesen Channel" über dem
Thread-Verlauf jedes Companion-Laufs in diesem Channel.

`using-alluvo-operator` bekommt dafür einen eigenen Abschnitt im `manage-settings`-Kapitel plus
eine Routing-Zeile. Festgehalten sind die drei Fallen: `describe` hat für diese Gruppe **keine**
Langdoku (die Gruppe ist trotzdem real — `get` ist hier der Read-before-write-Schritt), `update`
**ersetzt die komplette Liste** (also erst `get`, dann die vollständige Liste zurückschreiben,
sonst löscht man das Priming aller anderen Channels), und es gibt **kein** `confirmed`-Gate — der
Schreibvorgang läuft sofort, das Ja des Operators muss davor liegen.

Dazu das Budget des Companions (alluvo#4619): ein einzelnes Lese-Tool-Ergebnis wird bei 12.000
Zeichen abgeschnitten (Ausnahme: der unteilbare Workflow-Guidance-Text), und die Agentenschleife
endet nach 8 Schritten. Eine abgeschnittene Liste in Slack ist damit erwartetes Verhalten, kein
Fehler — die Skills sollen den Operator auf eine engere Abfrage oder auf die Operator-Session
verweisen statt einen vollständigen Export im Slack-Thread zu versprechen.

`build-automation-agent` grenzt im Abschnitt *Slack delivery* die beiden Slack-Oberflächen
gegeneinander ab: `send_slack_message` ist ein Workflow, der etwas **hinausschickt**, der Companion
der Bot, den man **erwähnt** — eine Companion-Beschwerde ist `manage-settings`, kein Workflow.
### Fixed — 2026-09-06 `manage-1on1-email`: Forwards sind über MCP adressierbar (`to_emails`) (alluvo#4779)

`manage-1on1-email` nimmt auf `forward`, `reply`, `reply-all` und `update` den Parameter
**`to_emails`** entgegen (Liste gültiger E-Mail-Adressen). Ein `forward` löst **keine eigenen
Empfänger** auf — der ursprüngliche Absender ist keiner —, also wird er direkt beim
`forward`-Aufruf adressiert. Ohne `to_emails` bleibt der Entwurf unadressiert und ist nicht
versendbar; die Preview schreibt dann `To: (none — pass to_emails, otherwise the draft cannot be
sent)`, und `update` mit `to_emails` ist der Reparaturweg.

`profilvertrieb` (Schritt 6b) behauptete bisher das Gegenteil — der Forward sei „nur aus der App
adressierbar", das Tool habe außer auf `draft` keinen To-Parameter. Das ist ersetzt. Festgehalten
sind zusätzlich: `to_emails` **ersetzt** die Empfänger (im Gegensatz zu `employee_document_ids`,
die ergänzt werden), auf `reply`/`reply-all` bleibt es ohne den Parameter beim Empfängerkontext
des Parents, auf `draft` wirkt er nicht (dort kommt der Empfänger aus `contact_id`), eine ungültige
Adresse lässt den ganzen Aufruf scheitern — und erst das Adressieren lässt den Profil-Link-Guard
greifen: ein `/profile-completion/…`-Link ist an genau einen Kandidaten gebunden und wird für
jeden anderen Empfänger abgelehnt.
### Fixed — 2026-09-06 `manage-record-action`: ein schreibfreier Preview heißt jetzt auch so (alluvo#4782)

`manage-record-action` überschreibt einen Lauf, der nichts geschrieben hat, nicht länger mit
`# Action Executed`. Nimmt eine zweistufige Action ihren schreibfreien Zweig (`operation:
"execute"`, top-level `confirmed: true`, explizit `data: { …, confirmed: false }`), kommt die
Antwort als **`# Action Preview (nothing written): <action>`** zurück, gefolgt von einem Satz,
dass nichts geschrieben und nichts versendet wurde. Nur ein echter Write bleibt
`# Action Executed` + `success_message`. Im `execute_bulk` erscheint pro Datensatz
`preview (nothing written)`, und die Summary führt eine eigene Zeile „Previewed (nothing
written)".

Damit ist der Workaround gegenstandslos, den `manage-contract-lifecycle` (`end_contract` /
`end_assignment`), `build-dienstplan` (`reassign_shifts`) und `merge-duplicate-companies`
(`merge_employee` / `merge_candidate`) trugen — „traue der Überschrift nicht". Alle drei Skills
lesen die Überschrift jetzt als das, was sie ist, und behalten `preview_only` (bzw.
`plan.result: null` bei `reassign_shifts`) als **Beleg auf der Payload-Seite**. Ein Einsatzende
oder ein Merge wird dem Operator nur bei `# Action Executed` **und** `preview_only: false`
gemeldet. `record-absence` nennt für den Bulk-Pfad zusätzlich den neuen Bucket „previewed".
### Added — 2026-09-06 Zugriff auf eine Wissensdatenbank über `manage-record-action` (alluvo#4783)

Wer eine **Wissensdatenbank** (`KnowledgeBase`, `0-180`) lesen darf, ist jetzt über MCP les- und
steuerbar: drei Record-Actions auf `0-180` — `list_members`, `add_member`, `remove_member` —
adressieren die Mitglieder-ACL der einzelnen Wissensdatenbank. Bisher war `is_public` der einzige
Hebel, und der ist alles-oder-nichts: eingeschaltet sieht **jeder** interne Nutzer die
Wissensdatenbank, nicht das eine Team, das der Operator gemeint hat.

`list_members` ist schreibfrei und beantwortet bereits den *unbestätigten* Aufruf — die Rolle
steht unter `## Action Preview`, das abschließende „Call again with `confirmed: true`" ist hier
Boilerplate und kein zweiter Schritt. Die gerenderte Liste ist bei 20 Einträgen gekappt, während
`count` die echte Gesamtzahl bleibt. Ein Mitglied wird immer über das Paar (`memberable_type`,
`memberable_id`) angesprochen — `"user"` oder `"role"`, nie die ID der Mitgliedszeile selbst.

`add_member` und `remove_member` sind zweistufig (Vorschau → `confirmed: true`). `add_member` auf
ein bestehendes Mitglied **ändert dessen Rolle**, statt eine zweite Zeile anzulegen;
`remove_member` scheitert laut auf einem Paar, das gar kein Mitglied ist — das heißt „falsche ID",
nicht „schon entfernt". Alle drei hängen an `knowledge_bases.manage_members`, `list_members`
eingeschlossen, weil die Mitgliederliste die ACL *ist*.

`using-alluvo-operator` führt das als Querschnittsabschnitt samt Routing-Zeile, inklusive der
Warnung, das nie über `is_public` abzukürzen, und der Unterscheidung der zwei „Rollen" im selben
Payload: `memberable_type: "role"` ist eine **Berechtigungsgruppe**, das Feld `role` dagegen die
Wissensdatenbank-Rolle (`viewer` | `editor` | `admin`).
### Added — 2026-09-06 Führerscheinkontroll-Termin absagen — über das Meeting (`0-201`), nicht über die Kontrolle (alluvo#4784)

`using-alluvo-operator` routet „Führerscheinkontroll-Termin absagen / gebuchten Kontrolltermin
stornieren / die Kontrolle wieder auf fällig setzen" jetzt auf `manage-record-action` mit
`model_type: "0-201"` und `action: "cancel"` — zweistufig wie immer.

**Warum nicht auf der Kontrolle selbst.** Auf DrivingLicenceCheck gibt es seit alluvo#4764 eine
`#[McpExposed]`-Action `cancel_booking`, und die Ausgangsmeldung zu diesem Issue nannte sie als
den Weg über `manage-record-action`. Der Abgleich gegen `origin/main` zeigt: **`0-60` steht
nicht in `ModelTypeEnum::availableForMcp()`**, und `ManageRecordActionTool` prüft das als
Allererstes (`guardMcpModelType()`). Der Aufruf endet also mit *„Model type '0-60'
(DrivingLicenceCheck) is not available via the generic model tools"* — die Action ist über MCP
nicht erreichbar. Dasselbe gilt für `perform_check`, `clear_invalid` und `void_check`: eine
Kontrolle wird in der Web-App erfasst, nie über MCP. Der Skill dokumentiert diesen Zustand
ausdrücklich, damit der Agent den Weg nicht mit dem nächsten generischen Tool nochmal versucht.
Die fehlende Freigabe ist als eigenes Issue auf dem api-Repo gemeldet (alluvo#4797).

**Der erreichbare Weg leistet dasselbe.** `CancelMeetingAction` (`action: "cancel"`, Recht
`meetings.edit`) schreibt genau dieselbe eine Änderung — `outcome = Cancelled`. Danach übernimmt
`MeetingObserver::handleOutcomeChange()`: Google-Kalendereintrag abgesagt, die verknüpfte
Kontrolle zurück auf **`due`** mit geleertem `scheduled_at`, plus die übliche Rückruf-Aufgabe für
den Owner des Termins. Verfügbar nur, solange der Termin `scheduled` und nicht schon abgesagt ist.

Drei Punkte, die der Eintrag mitnimmt, weil sie sonst falsch geraten werden:

- **Den Termin erst finden.** Die Kontrolle gibt ihre `meeting_id` über MCP nicht heraus —
  `get-timeline` am Mitarbeiter, oder `query-model` auf `0-201` mit `status: "scheduled"` und der
  `meeting_type_id` der System-Terminart `driving-licence-check`. Nach Mitarbeiter ist nicht
  filterbar.
- **Verlegen heißt neu buchen, nicht erst absagen.** Die Neubuchung hängt den neuen Termin an,
  *bevor* sie den alten absagt, die Kontrolle bleibt also durchgehend `scheduled`. Absagen und
  dann buchen fällt zwischendurch auf `due` und erzeugt eine Rückruf-Aufgabe, die niemand wollte.
- **Nie löschen.** `MeetingObserver::deleting()` blockt jeden Löschpfad — der Termin gehört zum
  Prüfprotokoll.
### Added — 2026-09-06 Portalzugang entziehen — `revoke-portal-access` auf der Mitgliedschaft (alluvo#4785)

Die Portal-Mitgliedschaft (`0-430`) trägt jetzt eine eigene, MCP-ausführbare Record-Action
**`revoke-portal-access`** — der sanktionierte Weg für „Zugang entziehen". Sie läuft über
`manage-record-action` (zweistufig, ohne Parameter), löscht **ausschließlich die Rollen-Grants**
der Mitgliedschaft und lässt Kontakt, Mitgliedschaft, Historie und die rollenlose **Platzierung**
im Organigramm samt Abteilungen stehen. Weil Portalzugang Opt-in ist, kann sich eine
rollenlose Mitgliedschaft nicht mehr anmelden — es gibt keinen Rückfall auf `viewer`; `status`
bleibt dabei unverändert `active`, die Aktion ist also keine „Deaktivierung".

`approve-stundenfreigabe` dokumentiert sie als eigenen Abschnitt neben Archivieren, inklusive
Kohorten über `operation: "execute_bulk"` (max. 100 `record_ids`, z. B. die per Backfill
vergebenen firmenweiten `viewer` ohne je erfolgte Anmeldung) — deren Vorschau ist die einzige
Stelle, an der die Ablehnungen pro Zeile sichtbar werden. Die Aktion ist **versteckt** auf einer
Mitgliedschaft ganz ohne Rollen-Grant (eine reine Platzierung hatte nie Zugang) und
**unavailable** für den letzten aktiven `administrator` eines Unternehmens; anders als beim
`portal_access_active`-Schalter greift dieser Guard auch für interne Operator:innen. Sie
funktioniert außerdem für Kontakte ohne Portal-Account, für die `assign-portal-roles` gar nicht
erst angeboten wird.

Die bisherigen Umwege sind entsprechend eingeordnet: eine leere `roles`-Liste auf
`assign-portal-roles` bleibt destruktiv (sie nimmt die Platzierung mit) und `archive` auf `0-430`
nimmt die Person zusätzlich von der Kontakte-Liste des Kunden — beides ist nicht mehr die Antwort
auf „nur den Zugang wegnehmen". `using-alluvo-operator` routet die Formulierung, und
`manage-contract-lifecycle` verweist beim Offboarding eines Empfängers darauf.

### Fixed — 2026-09-06 Konfliktmarker in der Frontmatter von `approve-stundenfreigabe` (alluvo#4785)

Beim Landen von alluvo#4732 blieben unaufgelöste Merge-Marker (`<<<<<<<` / `=======` /
`>>>>>>>`) um die `description:`-Zeile in `approve-stundenfreigabe/SKILL.md` stehen, wodurch die
YAML-Frontmatter des Skills ungültig war. Die beiden Varianten sind jetzt zusammengeführt: die
Trigger für die Beleg-/Upload-Warteschlange (alluvo#4730) **und** die für `correct_signer`
(alluvo#4732) stehen beide in der Beschreibung.
### Added — 2026-09-06 Anrede je Kontakt festlegen, optional für einen anderen User (alluvo#4789)

Die Record-Action `set-formality-override` auf Kontakt (`0-105`) ist der Weg, die **eigene**
du/Sie-Form für einen Kontakt zu pinnen: `formality` `formal`/`informal`, leer lassen löscht den
Override. Sie schlägt `contacts.address_formality` — wer seine Form gepinnt hat, sieht eine
Änderung am Kontakt-Default nicht. Neu akzeptiert sie optional `user_id` (eine **Tenant-User-ID**,
Modelltyp `0-1`) und schreibt damit die Präferenz eines anderen Users. Das hängt an der
Berechtigung `users.impersonate`: ohne sie taucht der Parameter in `operation: "list"` gar nicht
erst auf, und ein trotzdem gesendetes `user_id` wird mit einem Validierungsfehler abgelehnt statt
still auf den eigenen Override umgebogen. Damit ersetzt sie den entfernten
`manage-contact-formality`-Pfad.

`enrich-contacts-from-activities` dokumentiert die Aktion mit der vollständigen Fallback-Kette
(User-Override → Kontakt-Default → Rollen-Default Employee/Candidate → Marken-Einstellung), der
Zweistufigkeit und der Regel, die Präferenz eines Kollegen nur auf dessen ausdrücklichen Wunsch
und mit namentlicher Bestätigung in der Vorschau zu schreiben. `call-prep` weist beim Feld
`address_formality` darauf hin, dass es nur der Default ist.

### Changed — 2026-09-05 Scope-Berechtigungen brauchen `scope`, sonst 422 (alluvo#4726)

`manage-permission-set` (`resource: "set"`, `create`/`update`) weist einen `permissions`-Eintrag
`{ "enabled": true }` **ohne** `scope`-Schlüssel jetzt ab, sobald der Key scope-gesteuert ist
(in `describe-permissions` als `(scope)` markiert). Die Fehlermeldung nennt den Key und die
gültigen Werte `all | team | branch | own` bzw. `none` zum Entziehen. Bisher wurde diese Form
angenommen und mit „Permission set updated." quittiert, obwohl der Resolver den geschriebenen
Eintrag als *denied* auflöste — eine solche Zuweisung hat also nie etwas freigeschaltet.
Nur `(toggle)`-Keys kommen weiterhin mit `enabled` allein aus.

`using-alluvo-operator` hält das im `manage-permission-set`-Abschnitt fest, zusammen mit dem
Zeitpunkt der Prüfung: die Vorschau (ohne `confirmed: true`) zählt nur die Änderungen, geprüft
wird erst beim bestätigten Schreiben — und weil der Call transaktional ist, rollt ein abgelehnter
Key den ganzen Batch samt einer Umbenennung im selben `update` zurück. Der `resource: "access"`-
Pfad (`grant`) ist nicht betroffen: der Planner setzt den Scope selbst und lässt den Schlüssel
bei Toggle-Keys weg.

### Added — 2026-09-05 Upload-/Extraktions-Warteschlange über MCP sichtbar und verwerfbar (alluvo#4730)

Die Warteschlange hinter jedem hochgeladenen Beleg, Dienstplan oder Stundenzettel ist jetzt
Modelltyp `0-29` (ExtractionUploadJob) und **read-only** über `query-model` / `get-model` /
`search-model` / `count-model` lesbar — `manage-model` create/update wird abgelehnt, weil jedes
Feld dort von der Mitarbeiter-App oder einem Prozessor geschrieben wird. Damit ist ein hängender
`pending`- oder ein `failed`-Upload sichtbar, statt als unerklärlich fehlender Datensatz zu
enden, und ein doppelt hochgeladener Beleg über `content_sha256` belegbar.

`get-attachment` hat eine dritte Quelle, `extraction_upload_job` — die Rohdatei eines noch nicht
übernommenen Uploads, mit der **Job-ID** als `attachment_id`. Neu ist außerdem die Record-Action
`discard_upload` auf `0-29`: zweistufig (Vorschau → `confirmed: true`), destruktiv (die Datei ist
danach weg), und bei einem `committed` Job nicht verfügbar.

`approve-stundenfreigabe` bekommt dafür den Abschnitt „The upload queue behind a Beleg (`0-29`)"
mit Feldern, Filtern, Status- und Kind-Werten, dem zweistufigen Discard-Aufruf und den
Berechtigungen. Korrigiert wurde dort zugleich die bisherige Aussage, die Duplikatswarnung habe
„keine MCP-Oberfläche": den byte-identischen Fall beantwortet jetzt `content_sha256` auf `0-29`,
das zweimal fotografierte Belegbild weiterhin nur der `document_date`-/`amount_gross`-Vergleich
auf `0-20` — beide Ebenen prüfen, in dieser Reihenfolge. Ebenso, dass die
Operator-Benachrichtigung nicht mehr die einzige Spur eines leer gebliebenen Draft-Entwurfs ist:
`status`, `error` und `warnings` stehen am Job. `using-alluvo-operator` routet die passenden
Operator-Formulierungen dorthin.

### Added — 2026-09-05 Falschen Unterzeichner einer Stundenfreigabe korrigieren (alluvo#4732)

`TimesheetRelease` (`0-435`) war bisher rein lesbar. Neu trägt der Typ genau eine Record-Action:
`correct_signer` („Unterzeichner korrigieren", über `manage-record-action`) verschiebt die
Zuordnung einer bereits erteilten Kundenfreigabe auf den Ansprechpartner, der tatsächlich
unterschrieben hat — der Fall, dass der Mitarbeiter beim Abzeichnen auf dem Gerät aus dutzenden
Kontakten den falschen antippt und damit eine nie beteiligte Person unter der § 17c-AÜG-Signatur
steht.

`approve-stundenfreigabe` bekommt dafür den Abschnitt „Correcting who a release names" mit dem
zweistufigen Aufruf, den beiden Pflichtparametern (`contact_id` — zwingend ein Kontakt **des
eigenen Entleihers** des Einsatzes, sonst 422; `reason` — landet mit altem und neuem Unterzeichner
im Protokoll), den Feldern der Vorschau (`preview_only`, `previous_*`/`new_*`, `company`, `days`,
`regenerates_activity_report`), der Berechtigung `timesheet_releases.correct_signer` und der
Nichtverfügbarkeit bei einer Fristablauf-Freigabe (`auto_approved` — dort hat niemand
unterschrieben). Ausdrücklich dokumentiert ist dabei, dass Unterschrift, Zeitpunkt, Kanal und
Tages-Snapshots unangetastet bleiben, dass die überholten Wochenspalten nur dann mitgezogen
werden, wenn sie noch den alten Unterzeichner nennen, und dass die Aktion den Tätigkeitsnachweis
**selbst** neu rendert (die überholte PDF wird archiviert, nicht gelöscht) — ein zusätzlich
angestoßener Lauf archiviert nur eine weitere Kopie umsonst.

Klargestellt wurde zugleich die Abgrenzung zu den beiden Rücknahmen: „die falsche Person hat
unterschrieben" heißt entweder *die falsche Person wurde überhaupt um eine Unterschrift gebeten*
(→ `revoke_release` / `revoke_approval`) oder *die richtige Person hat unterschrieben und der
falsche Name wurde ausgewählt* (→ `correct_signer`). Die Capability-Box der Skill nennt jetzt vier
statt drei Schreib-Aktionen; `using-alluvo-operator` routet die passenden
Operator-Formulierungen dorthin.

Aufrufform: `confirmed` gehört bei dieser Aktion **top-level** und nicht in `data` — ein
`data: { confirmed: true }` bei top-level `false` schreibt, während die Antwort noch mit
`# Preview:` überschrieben ist.
### Changed — 2026-09-04 Portal-Rollen: eine Position statt einer Zuweisungsliste (alluvo#4615)

`send-portal-invitation` und `assign-portal-roles` fragen die Position eines Ansprechpartners
seit alluvo#4609 **einmal** ab statt je Rolle. Der Repeater `assignments`
(`{ role, client_site_id, department_ids }`) ist durch drei Parameter ersetzt:
`position_client_site_id` (leer/weggelassen = unternehmensweit, sonst eine Einsatzbetrieb-ID),
`position_department_ids` (Stationen **dieses** Einsatzbetriebs; leer = ganzer Betrieb,
unternehmensweit gar keine) und `roles` (flache Liste der Rollenwerte, die dort gelten).

`approve-stundenfreigabe` — der Abschnitt *`assignments` — a role plus where it applies* wurde zu
*The position + the roles that hold there* umgeschrieben: die drei Parameter, die unveränderten
Scope-Regeln (`administrator` unternehmensweit, `site_admin` site-scoped und ohne Stationen — jetzt
mit einer feldbezogenen Fehlermeldung auf `position_department_ids`, die als „Stationen weglassen"
zu lesen ist, nicht als vorübergehender Fehler), und die neue Fähigkeit: ein Einsatzbetrieb mit
**leerer** `roles`-Liste ist eine reine **Platzierung** im Organigramm ohne Portalzugang —
unternehmensweit mit leerer Liste löscht dagegen wie bisher alle Zuweisungen. Die
Vollersatz-Warnung nennt jetzt die tatsächlichen Fallstricke (`assign-portal-roles` nur mit
`portal_access_active`; ein vertippter Rollenwert wird still verworfen und leert die Liste) statt
des überholten „bare list of role values". `position_conflict` ist über diese beiden Aktionen nicht
mehr erreichbar — die Parameterform kann keine gemischte Position mehr ausdrücken; die Tabelle sagt
das und verweist `position_conflict_existing` weiter auf den `approve-portal-role-request`-Pfad.
Der alte `assignments`-Payload wird serverseitig noch als Fallback verstanden, ist aber
ausdrücklich nicht mehr der Vertrag.

`manage-contract-lifecycle` und `using-alluvo-operator` folgen: Wiederfreischalten eines
deaktivierten Empfängers und das Verschieben einer Person nennen Position + `roles` statt
`assignments`, und der Navigator-Eintrag zu „Portal-Rolle lässt sich nicht vergeben" erklärt, warum
`position_conflict` von dort nicht mehr kommt.

### Added — 2026-09-03 Niederlassung und ihre Org-Struktur sind über MCP erreichbar, Firmenanschrift vollständig lesbar (alluvo#4625)

Vier Model-Types der tenant-eigenen Org-Struktur sind seit dem 03.09.2026 über `manage-model`
les- **und** schreibbar: `0-73` Branch (Niederlassung) und `0-75` BusinessUnit sowie `0-72`
CostCenter hatten vorher gar keine MCP-Fläche — ein `search-model` auf `0-73` war ein harter
Fehler —, `0-74` Team war nur lesbar. Damit entfällt der Widerspruch, dass `Employee.branch_id`
schon immer schreibbar war, die Branch-ID aber nie auflösbar.

`using-alluvo-operator` — neuer Querschnittsabschnitt *Org structure: Niederlassung, Bereich,
Kostenstelle, Team*: die Kette **Branch → BusinessUnit → CostCenter** (eine Kostenstelle hängt an
`business_unit_id`, nicht an der Niederlassung), die bewusste Asymmetrie `Team.branch_id`
**required** vs. `BusinessUnit.branch_id` **nullable** (ein Bereich darf ohne Niederlassung
existieren — nie eine Branch erfinden, um einen Create durchzubekommen), `code` als
required + unique bei BusinessUnit und CostCenter (Branch und Team haben keins), und dass die
Anschrift einer Niederlassung über MCP **gar nicht** setzbar ist: Branch nimmt nur `name`,
`description`, `email`, `phone`, `is_active`, `owner_id`, und `manage-location` lehnt
`parent_type: "0-73"` ebenfalls ab — kein ausgelieferter Location-Purpose ist für `branch`
freigegeben (alluvo#4626). Die Adresse bleibt Sache von *Einstellungen → Niederlassungen*. Ebenfalls
festgehalten: `owner_id` fällt beim Create auf den handelnden Benutzer zurück, eine Niederlassung
bleibt also nie ohne Owner. Alle Schreibpfade zweistufig wie üblich (`confirmed: false` →
Freigabe → `confirmed: true`).

`using-alluvo-operator` — die Routing-Zeile *„Standort der Agentur hinterlegen"* nennt zusätzlich
die sechs neuen Felder der `general`-Gruppe von `manage-settings`: `company_address`,
`company_address_line_2`, `company_zip`, `company_country`, `company_website`, `industry`. Bisher
kannte der Assistent nur `company_city`/`company_state` und damit die halbe Adresse. Wichtig für
die Abgrenzung: nur `company_city`/`company_state` speisen den `agency-location`-Block der Agenten,
die übrigen sind Tenant-Stammdaten für Anschreiben, Verträge und Standortangaben; `industry` ist
die Branche des **eigenen** Unternehmens, nicht die einer Kundenfirma.

`onboard-new-employee` — Schritt 0.1 löst die Niederlassung weiterhin per `search-model` auf, kann
sie bei einem echten Treffer-Null jetzt aber auch anlegen (`model_type: "0-73"`, `name` required;
die Adresse bleibt der App vorbehalten) — mit dem ausdrücklichen Vorbehalt, das nur nach Bestätigung
durch den Operator zu tun: ein vertippter Suchbegriff ist die häufigere Ursache, und eine doppelte
Niederlassung zerlegt das Reporting des ganzen Tenants.

`record-absence` — die Telefon-Wasserfall-Erklärung korrigiert sich: die beiden Hotline-Nummern und
die Reihenfolge sind `manage-settings`-Felder, die **erste** Quelle `branch` ist keins. Sie liest
das `phone` der Niederlassung des Mitarbeiters — jetzt per `get-model`/`search-model` auf `0-73`
lesbar und per `update` füllbar. Genau diese Quelle war vorher die einzige des Wasserfalls, an die
der Assistent nicht herankam, obwohl sie standardmäßig zuerst greift.

### Changed — 2026-09-02 Auftraggeber-Anschrift ist über MCP korrigierbar, nicht nur bei der Anlage (alluvo#4611)

`client_party_location_id` (die Auftraggeber-Anschrift im Rubrum „Zwischen … und …") steht seit
dem 02.09.2026 auch in `UPDATABLE_FIELDS` von `manage-framework-contract` — `action: "update"`
nimmt das Feld an (DRAFT-Stage, wie jedes andere `update`) und validiert es genau wie der
create-Pfad: die Location muss existieren **und** eine vollständige Adresse tragen, weil der Wert
wörtlich gedruckt wird (AÜG §12). Der Schreibpfad **repliziert** die Firmen-Location auf den
Vertrag (`origin_location_id`), verlinkt sie also nie direkt — eine vertragsbezogene Korrektur
ändert nie die Adresszeile der Firma. Bisher wies der update-Pfad das Feld als unbekannt zurück
und riss den gesamten Aufruf inklusive aller anderen Felder mit.

`manage-contract-lifecycle` — der Abschnitt *Which address the contract prints for the customer
(Vertragskopf / Rubrum)* verliert die (jetzt falsche) „create-only"-Warnung samt der Anweisung,
das Feld niemals an `update` zu schicken. Stattdessen stehen dort beide Korrekturwege: (1) am
Vertrag über `manage-framework-contract` `update` — wirkt auf genau diesen Vertrag; (2) an der
Firma über `manage-location` mit `purpose_slug: "headquarter"` — wirkt auf alle Verträge der
Firma, aber nur solange `client_party_location_id` leer ist, denn der explizite Sitz am Vertrag
gewinnt immer. Für Einsatzverträge bleibt Weg 1 nur am zugehörigen Rahmenvertrag möglich (der AC
hat kein eigenes Feld). Dazu der Hinweis, die `confirmed: false`-Vorschau zu lesen: sie zeigt jetzt
alle drei Adressen (*Selected Location ID*, *Client Party (HQ) Location ID*, *Billing Location
ID*), sodass eine Anschriften- von einer Rechnungsadressänderung unterscheidbar ist, und
`describe(topic: "billing")` trägt dieselbe Abgrenzung ausführlich.

`triage-data-quality` — die Behebung von *Kunde ohne Firmensitz* nennt beide Wege statt nur des
Firmenstandorts, mit der Empfehlung, bei einem schlicht dünnen Firmendatensatz weiterhin an der
Firma zu korrigieren. `billing_location_id` hilft nach wie vor nicht.

### Changed — 2026-09-02 Vertragskopf nennt den Firmensitz statt der Rechnungsadresse (+ informativer Check `client_party_address`) (alluvo#4600)

Der Vertragskopf („Zwischen … und …") aller AÜV-Dokumente — Rahmenvereinbarung, AÜV,
Einzel-AÜV, §12 Konkretisierung — nennt den Kunden seit dem 02.09.2026 mit dem **Sitz der
Kundenfirma** (`App\Legal\Rendering\ClientPartyAddressResolver`): zuerst
`frameworkContract.client_party_location_id`, sonst ein Firmenstandort mit Zweck `headquarter`,
dann `branch-office`, dann irgendein aktueller Standort außer `billing-address`. Fehlt alles,
bleibt der Kundenblock bewusst ohne Anschrift. Nie mehr aus `billing_location_id`,
`contract_location_id` oder dem Standort des Einsatzbetriebs (GH-#4597 — Falschangabe im
unterschriebenen Vertrag bei Trägerstrukturen).

`manage-contract-lifecycle` bekommt dafür einen eigenen Abschnitt *Which address the contract
prints for the customer (Vertragskopf / Rubrum)*: die Auflösungsreihenfolge, die drei
Adressen, die dort nie stehen (Rechnungsadresse → nur Block „Rechnungsempfänger";
`contract_location_id` und der Einsatzbetrieb → §12-AÜG-Einsatzort in eigenen Blöcken), und
der Weg zur Behebung (`manage-location` mit `purpose_slug: "headquarter"` an der Firma — nicht
die Rechnungsadresse). Dazu die Warnung, dass `client_party_location_id` über MCP
**create-only** ist: `manage-framework-contract` `action: "update"` weist das Feld als unbekannt
zurück und verwirft damit den ganzen Aufruf (api#4604 macht das Feld nachträglich änderbar) —
an einem bestehenden Rahmenvertrag geht die Korrektur nur über den Firmenstandort oder den
Wizard. **Noch am selben Tag überholt** — siehe den Eintrag zu alluvo#4611 oben: das Feld ist
inzwischen auch über `update` setzbar, und die Warnung steht nicht mehr im Skill. Dazu der Hinweis,
dass `manage-framework-contract` `action: "create"` die Anschrift bereits selbst ableitet und
ohne brauchbaren Firmenstandort verweigert, der Check also vor allem Einsatzverträge und
Importe trifft.

Der neue Completeness-Check **`client_party_address`** in der `completeness`-Ausgabe von
`manage-framework-contract` und `manage-assignment-contract` ist **informativ** (`gates: []`)
und blockiert weder `review` noch `sending` noch `signature`. Beide Stellen in
`manage-contract-lifecycle`, die die Prüfliste abarbeiten (Rahmenvertrag-Sendegate,
Einsatzvertrag Schritt 2), sagen das jetzt ausdrücklich — maßgeblich sind die Per-Gate-Zeilen,
nicht die Zahl der roten Punkte.

`triage-data-quality` führt „Kunde ohne Firmensitz" in Abschnitt 3d als Vertragsmangel: kein
Detector meldet ihn, die `completeness` der Vertrags-Tools schon, behoben wird er an der Firma
(`manage-location`, Zweck `headquarter`) und nie über die Rechnungsadresse — und er ist kein
Sendehindernis.

### Changed — 2026-09-02 Portal-Rollen: ein Ansprechpartner hat genau eine Position (alluvo#4603)

Seit dem 02.09.2026 belegt eine Mitgliedschaft pro Firma genau **eine Position** —
unternehmensweit, ein ganzer Einsatzbetrieb oder einzelne Stationen eines Einsatzbetriebs — und
alle Rollen gelten dort. `approve-stundenfreigabe` führt die Regel jetzt im `assignments`-
Abschnitt aus, samt der beiden 422-Absagen als erwartete Antworten: `position_conflict` (die
gesendete Liste mischt Positionen — z. B. ein site-scoped `approver` neben einem
unternehmensweiten `viewer`, dieselbe Rolle an zwei Häusern, oder zwei Zeilen am selben Standort
mit verschiedenen `department_ids`) und `position_conflict_existing` (eine Rolle wird an einer
Position *hinzugefügt*, die die Person nicht belegt — der `approve-portal-role-request`-Pfad).
Dazu die Folgen für die Praxis: `administrator` und site-scoped Rollen schließen sich aus, ein
Umzug bewegt die ganze Mitgliedschaft in *einem* Full-Replace-Call, und die erste vergebene Rolle
schluckt die Platzierung. Die frühere Zeile „dieselbe Rolle an zwei Standorten sind zwei Zeilen"
ist damit falsch und entfernt.

Die Automatiken respektieren die bestehende Position, statt eine zweite anzulegen — beide Skills
sagten bisher das Gegenteil. `ensureLoginAccess()` vergibt den **Empfänger-`viewer` an der
vorhandenen Position** (nicht mehr unternehmensweit) und löscht die Platzierungszeile;
`ensurePlacement()` legt für eine Person mit Rolle **gar keine** Platzierung mehr an, verschiebt
niemanden an einen anderen Einsatzbetrieb und **vereinigt** Abteilungen, statt sie zu ersetzen.
`manage-contract-lifecycle` streicht deshalb die Behauptung, wer Empfänger *und*
Ansprechpartner vor Ort ist, stehe zu Recht zweimal im Organigramm (einmal unternehmensweit,
einmal am Standort) — es ist genau ein Knoten —, und sagt jetzt, dass eine §11-Korrektur einen
bereits platzierten Ansprechpartner **nicht** verschiebt. Der Rollenanfrage-Abschnitt dokumentiert
die `position_conflict_existing`-Absage beim Genehmigen (die Anfrage bleibt `pending`, nichts wird
vergeben) mit zwei gangbaren Auswegen: die Rolle direkt über `assign-portal-roles` /
`send-portal-invitation` vergeben, oder mit `context_only: true` genehmigen, was gar keine
stehende Rolle vergibt und deshalb nicht kollidieren kann. `using-alluvo-operator` bekommt den
passenden Symptom-Eintrag.

Beim Verifizieren gefunden und als **api#4605** gemeldet: die On-Device-Unterschrift des Kunden
läuft über denselben Add-Pfad und **schlägt komplett fehl** (422, keine Freigabe), wenn der
Unterzeichner schon eine andere Position belegt — etwa der unternehmensweite `administrator`, der
auf der Station unterschreibt. `approve-stundenfreigabe` beschreibt das tatsächliche Verhalten als
bekannten Defekt samt Ausweichwegen, statt es zu beschönigen.

### Changed — 2026-09-02 Einsatzvertrag: `discount_percent` macht den gesendeten `billing_rate` zum regulären Satz (alluvo#4589)

`manage-assignment-contract` nimmt seit dem 02.09.2026 `discount_percent` (0–100, nullable) auf
`create` **und** `update`. Damit ändert sich die Bedeutung des gesendeten Satzes: mit gesetztem
Nachlass ist `billing_rate` der **reguläre** Satz, der vereinbarte wird serverseitig über
`RateConcession::resolveWrite()` abgeleitet und in `billing_rate` geschrieben — der eingegebene
reguläre Satz landet in der neuen Spalte `list_billing_rate`. Beim **Lesen** (`get-model` /
`query-model` auf `0-31`) ist `billing_rate` also weiterhin immer der abgerechnete Satz;
`list_billing_rate` + `discount_percent` sind nur bei hinterlegtem Nachlass gefüllt.

`manage-contract-lifecycle` Schritt 2 führt die Regel jetzt aus: den 100-%-Fall
(unentgeltliche Überlassung, stufenweise Wiedereingliederung) samt dem Hinweis, dass der
reguläre Satz trotzdem mitgeschickt werden muss — ohne ihn bleibt die Rate-Prüfung in
`completeness` rot und `send_for_signoff` verweigert; den Re-Apply-Fallstrick beim `update`
(nur ein neuer `billing_rate` gesendet → stehender Nachlass wird erneut darauf angewandt);
und dass ein Nachlass mit `discount_percent: 0` entfernt wird, nicht mit `null` (der `update`-
Pfad verwirft Null-Werte, bevor er den Satz auflöst, ein gespeicherter Nachlass überlebt).
Dazu die Warnung, dass der **`create`**-Preview den Nachlass noch nicht abbildet und den
regulären Satz als „Hourly Rate" ausweist (api#4591 dagegen aufgemacht) — der `update`-Preview
zeigt das aufgelöste Trio korrekt.

`head-of-sales` liest `list_billing_rate` + `discount_percent` mit: `billing_rate` bleibt der
richtige Faktor für die gewichtete Forecast-Rechnung (er ist bereits der vereinbarte Satz),
aber ein Vertrag mit 0,00 €/h ist eine unentgeltliche Überlassung und kein Datenfehler und
muss als Nachlass mit seinem regulären Satz benannt werden. Bei der Gelegenheit korrigiert:
`billing_rate` steht in der Feldtabelle nicht mehr als „in cents" — der Money-Cast liefert an
der MCP-Grenze EUR. `match-bench-to-clients` sagt jetzt, dass ein Matching-Entwurf zum
schlichten vereinbarten Satz preist und Konzessionen zu `manage-contract-lifecycle` gehören.

### Changed — 2026-09-02 Stundenfreigabe: „war nicht anwesend" ist ein eigener Korrekturgrund, und ein von Menschen entschiedener Tag wird nicht mehr neu abgeleitet (alluvo#4579)

`TimesheetCorrectionReason` kennt seit dem 02.09.2026 den Fall `day_not_worked`
(„Mitarbeiter war nicht anwesend"). Er ist der **einzige** Grund, der ohne
`proposed_start`/`proposed_end` eingereicht werden darf; jede andere Korrektur ohne beide Zeiten
wird von `TimesheetCorrectionService::request()` bzw. der Portal-Validierung mit 422 abgelehnt
(*„A correction must propose a start and an end, or state day_not_worked as its reason."*).
`other` verlangt weiterhin eine Notiz. Vorher waren „der Mitarbeiter war nie da" und „korrigiere
die Zeiten auf null" dieselbe gespeicherte Zeile — der Mitarbeiter nahm beim Annehmen etwas an,
das so nie ausgesprochen wurde.

Zweite Änderung an derselben Fläche: `TimesheetBuilder` friert einen Tag jetzt nicht mehr nur bei
`client_confirmed_at`, sondern auch bei `edited_by_contact_id` ein. Ein Tag unter Korrektur ist per
Definition **nicht** kundenseitig unterschrieben, deshalb hatte genau der Fall, für den die Sperre
gedacht war, gar keine: eine angenommene Korrektur wurde vom nächsten Rebuild sofort auf den
Dienstplan zurückgeschrieben (Timesheet 224, 02.09.2026 — fünf Annahmen, fünf Rebuilds, keine
bleibende Änderung). Und „korrigiert" heißt jetzt, dass sich ein Wert **unterscheidet**: ein
geprüfter, aber unveränderter Tag meldet `was_touched_by_human`, nicht `is_agreed_correction`.

Die Einschränkung auf `day_not_worked` gilt für den Kunde→Mitarbeiter-Weg (Portal-Dialog und
`request()`). Der Vorschlag der Agentur an den Kunden (🔴 Stundenklärung, `proposeToClient()`)
validiert das nicht — die Skills beschreiben deshalb weiter nur den Portal-Weg.

- **approve-stundenfreigabe** — der Korrekturabschnitt führt die Gründe vollständig auf, nennt
  `day_not_worked` als einzigen Grund ohne Zeiten und den 422 für alle anderen, und sagt
  ausdrücklich, dass „Grund: Sonstiges, Zeiten leer lassen" für einen No-Show weder gemeint noch
  möglich ist. Der Rebuild-Abschnitt friert jetzt „von einem Menschen entschieden" statt nur
  „vom Kunden unterschrieben" ein, widerruft die alte Aussage, eine Korrektur auf einem
  unsignierten Tag sei nicht dauerhaft, und trennt „korrigiert" von „geprüft".
- **record-absence** — die Rebuild-Sperre nennt neben dem unterschriebenen Tag auch den von einer
  Person bearbeiteten.

### Changed — 2026-09-02 Portal-Mitgliedschaft (`0-430`): Archivieren entzieht den Zugang, Wiederherstellen gibt ihn nicht zurück (alluvo#4576)

`CompanyContactResource` registriert seit dem 02.09.2026 die Actions
`ArchiveCompanyContactAction` / `UnarchiveCompanyContactAction`. Beide erben `#[McpExposed]` vom
generischen `ArchiveRecord` und sind damit über `manage-record-action` auf `0-430` aufrufbar — mit
der **geerbten** Beschreibung, die eine reine Sichtbarkeitsänderung verspricht. Auf diesem Modell
stimmt das nicht:

- **`archive` entzieht den Portalzugang.** `CompanyContactService::setArchived()` setzt
  `archived_at` **und** `status = disabled` (plus `disabled_at` / `disabled_by`).
- **`unarchive` ist bewusst asymmetrisch.** Es löscht nur `archived_at`; der Zugang bleibt
  deaktiviert, weil der Status *vor* dem Archivieren nirgends festgehalten ist. Vollständiges
  Wiederherstellen sind zwei Aufrufe.
- **Ein Wächter greift für Operatoren:** die letzte aktive `administrator`-Mitgliedschaft einer
  Firma lässt sich nicht archivieren — die Action meldet das als `unavailableReason()`, nicht als
  Fehler. Die zweite Regel (niemand archiviert sich selbst) gilt nur für Akteure *im* Kundenportal
  und ist über MCP nicht erreichbar.

**Korrektur am Drift-Ticket:** dort stand, `query-model` / `search-model` lieferten archivierte
`0-430`-Zeilen nicht mehr ohne `with_archived=1`. Das ist am Code auf `origin/main` nicht der Fall.
`Resource::applyArchivedDefault()` wird ausschließlich von `SchemaPageIndexPropsBuilder` und
`BoardViewPropsBuilder` aufgerufen — den Inertia-Listenseiten. Die MCP-Tools rufen es nie auf und
kennen kein `with_archived`. Die Leseseite ist also **unverändert**: archivierte Zeilen kommen
weiterhin zurück. Genau das ist die Falle, und die Skills sagen sie jetzt: das Feld ist keine
Standardspalte, die Oberfläche des Operators blendet die Zeilen aus, die eigene Abfrage nicht — ein
Zählergebnis kann deshalb höher liegen als das, was auf dem Bildschirm steht.

Der neue Enum-Fall `CompanyContactPortalState::Archived` ist ein UI-Sub-Select über `contacts` und
über MCP nicht lesbar; kein Skill greift darauf zu, deshalb keine Änderung dazu.

- **using-alluvo-operator** — der Archivierungs-Abschnitt nennt `0-430` als zweiten Alltagsfall und
  führt die Ausnahme (zugangsentziehend, nicht symmetrisch) direkt neben der allgemeinen Regel.
  Der Punkt „nicht vor MCP-Lesezugriffen versteckt" um die Divergenz zur Oberfläche bei `0-107`
  und `0-430` ergänzt. Neue Triage-Zeile für „Ansprechpartner ist aus der Kontakte-Liste
  verschwunden".
- **approve-stundenfreigabe** — `archived_at` in der `0-430`-Feldtabelle, plus ein eigener
  Abschnitt *Archivieren* mit den drei Punkten oben und dem Zwei-Schritt-Weg zurück.
- **manage-contract-lifecycle** — gesetztes `archived_at` als zweite Ursache dafür, dass ein
  Empfänger trotz Versand nicht ins Portal kommt.
- **head-of-sales** — die Single-Threaded-Zählung filtert `archived_at` `is_null`; ein nur noch
  archivierter Zweitkontakt deckt ein Konto nicht ab.
- **account-research** — archivierte Mitgliedschaften gehören nicht in „key people".

### Changed — 2026-09-02 Stundenfreigabe: der Ansprechpartner-Picker schlägt nur noch die *eigenen* Kontakte des Mitarbeiters vor (alluvo#4572)

Der Picker im Stundenfreigabe-Wizard der Mitarbeiter-App hat seit dem 02.09.2026 **zwei klar
getrennte Zonen**. Die Vorschlagsgruppe über dem Suchfeld hieß „Zuletzt bestätigt von" und war
**firmenweit** — sie schlug jedem Mitarbeiter jeden Kontakt vor, den irgendein Kollege beim
Entleiher hatte unterschreiben lassen, samt Datum. Sie heißt jetzt **„Meine Ansprechpartner"** und
enthält nur noch bis zu **fünf** Kontakte, die *dieser* Mitarbeiter selbst schon hat unterschreiben
lassen (`lastSignedAt`, jetzt auf `timesheets.employee_id` eingegrenzt) oder selbst im Wizard
angelegt hat (`createdByMe`, neu). Die **Namenssuche bleibt bewusst firmenweit** — sonst legt jeder
neue Mitarbeiter auf der Station eine Dublette der Stationsleitung an. Gleicher Picker im Wochen-
und im Tagesmodus (`EmployeeApprovableDaysPayload` liest dieselben Zeilen).

**Kein Fallback:** hat der Mitarbeiter beim Entleiher noch nichts Eigenes, ist die Gruppe leer und
es erscheint nur der Tipp-Hinweis. Bewusste Produktentscheidung — aber ein neuer sichtbarer
Zustand, den ein Operator sonst als kaputte Kontaktverknüpfung fehldiagnostiziert.

Mitgeliefert als Bugfix: die Kurzliste las `timesheets.client_confirmed_by_contact_id`. Diese
Wochenspalte ist seit der Teilfreigabe abgelöst und in echten Daten meist NULL, so dass die Liste
bei Mitarbeitern mit vielen Unterschriften leer blieb. Gelesen wird jetzt `timesheet_releases` mit
`standing()` — dieselben Zeilen wie im Freigaben-Reiter.

Kein MCP-Tool, kein Schema, keine Action und kein Enum geändert.

- **approve-stundenfreigabe** — *The signer picker* neu geschnitten: die beiden Zonen, die
  Fünfer-Grenze, die Herkunft der Datumsangabe, der leere Zustand als Normalfall, und die
  Korrektur, dass das `timesheet_approver`-Label (Sortierung + „Ansprechpartner"-Badge) nur auf
  die **getippten Suchtreffer** wirkt und die Vorschlagsgruppe gar nicht erreicht. Trigger-Begriffe
  für den Picker in die `description` aufgenommen.
- **merge-duplicate-companies** — der Dubletten-Herkunftskasten sagt jetzt, dass die Vorschlagsliste
  pro Mitarbeiter gilt: wer neu auf der Station ist, startet leer und muss suchen, sonst entsteht
  die nächste Dublette. Label und Portalrolle helfen der Auffindbarkeit erst beim Tippen.

### Changed — 2026-09-02 „Dienst ändern“: der Mitarbeiter korrigiert den begonnenen Dienst, solange der Tag offen ist (alluvo#4559)

Auf der **Zeiterfassung** kann der Mitarbeiter eine einzelne Schicht seit dem 02.09.2026 selbst
ändern („Dienst ändern“) oder stornieren („Dienst entfällt“). Das Fenster endet nicht mehr an der
Uhr, sondern am **Tag**: änderbar, solange der Tag offen ist — kein Tagesabschluss des
Mitarbeiters, keine Kundenfreigabe (`PastShiftGuard::withinOpenDay()`). Eine bereits *begonnene*
Schicht und eine Schicht auf einem nie abgeschlossenen **vergangenen** Tag sind damit für ihn
korrigierbar. Ein Verschieben prüft zusätzlich den **Zieltag**; das Zurückziehen des
Tagesabschlusses öffnet das Fenster wieder.

Der Operator-/MCP-Pfad ist unverändert: `update-shift` und `remove-shift` verweigern weiterhin jede
begonnene oder vergangene Schicht (durch einen Test festgenagelt). Genau diese **Asymmetrie** ist
das, was die Skills bisher falsch beschrieben — sie behaupteten, der Mitarbeiter könne eine
begonnene Schicht ebenfalls nicht anfassen. Ebenfalls nicht betroffen: der **Dienstplan-Assistent**
des Mitarbeiters (ganzer Plan) behält die Kalendersperre, und das **Anlegen** einer Schicht auf
einem vergangenen Tag bleibt überall Operator-Sache (`past_date_acknowledged`).

Kein MCP-Tool, -Parameter, -Schema, keine Enum- oder ModelType-Änderung. Die Änderung ist **laut**:
§-11-Change-Log-Zeile und Mitarbeiter-Digest laufen wie bei jeder anderen Planänderung.

Mitgeliefert: die `max_hours`-Decke des Einsatzes blockt auf dem Mitarbeiterpfad nur noch, wenn der
Schreibvorgang die Überschreitung **verschlimmert** — ein Monat, der ohnehin über der gebuchten
Decke liegt, hat den Mitarbeiter zuvor komplett aus seinem Dienstplan ausgesperrt (161,7 h gegen
151,67 h: selbst das Verkürzen einer Schicht wurde abgelehnt).

- **build-dienstplan** — die Sperr-Box in Schritt 6 sagt jetzt, dass sie *deine* Sperre ist, und
  nennt die Open-Day-Regel des Mitarbeiters daneben; 6b trennt die beiden Mitarbeiter-Oberflächen
  (Zeiterfassung = Tag offen, Assistent = Kalendersperre); der Backfill-Absatz grenzt „bestehende
  Schicht korrigieren" gegen „fehlende Schicht anlegen" ab; die `max_hours`-Box trägt die
  Verschlimmerungs-Regel.
- **approve-stundenfreigabe** — neuer Hinweis, dass sich das Soll eines offenen Tages noch bewegen
  kann, und in *Changing a closed day*, dass der Tagesabschluss auch die **Schicht** einfriert und
  das Zurückziehen sie wieder öffnet.
- **head-of-disposition** — 1d: eine Stornierung kann jetzt auch auf einem laufenden oder
  vergangenen Tag auftauchen; das ist eine Stundenfreigabe-Tatsache, keine Deckungsaufgabe.
- **record-absence** — die „Sackgasse" bei rückdatierten Krankmeldungen ist die des Operators; auf
  einem offenen Tag kann der Mitarbeiter selbst stornieren.
- **using-alluvo-operator** — neue Routing-Zeile für „warum kann er das und ich nicht", und die
  `max_hours`-Zeile trägt die Verschlimmerungs-Regel.

### Changed — 2026-09-01 „Ohne Einsatz" ist wieder weg: der Zeitraum entsteht nicht bzw. landet im Papierkorb (alluvo#4516)

Der Status `closed` / „Ohne Einsatz", eine Release zuvor eingeführt (alluvo#4489, PR #269), ist
zurückgenommen. `TimesheetStatus` (`0-426`) hat wieder **fünf** Werte, `TimesheetLifecyclePhase`
wieder vier Stationen, und eine Tenant-Migration hat jede überlebende `closed`-Zeile auf `open`
umgeschrieben und soft-gelöscht. Das ist die schärfste Form von Drift: die Skills nannten einen
Status, den die API zurückweist.

An seine Stelle treten zwei Regeln:

- **Ein Zeitraum ohne freigebbaren Tag entsteht gar nicht.** Die Substanzprüfung in
  `EnsureTimesheetsService` verlangt jetzt einen *freigebbaren* Tag — eine wirksame Schicht, für
  die niemand krankgemeldet ist, oder einen abgeschlossenen Zeiteintrag. Ein Zeitraum, dessen
  **jeder** geplante Tag durch eine gemeldete Krankmeldung gedeckt ist, wird nicht materialisiert.
  Ein erfasster Zeiteintrag zählt immer, auch an einem gedeckten Tag.
- **Ein Zeitraum, der leer wird, wird soft-gelöscht** (`TimesheetWithoutActivityPruner`) — er liegt
  im Papierkorb, nicht in einem Status, und ist damit gleichzeitig aus Liste, Board,
  Warteschlangen, Fristen und Kundenportal heraus. Der Weg zurück ist die Wiederherstellung
  **derselben Zeile**: Schicht wieder einplanen oder Krankmeldung ablehnen, dann holt
  `RebuildTimesheetsForAbsence` sie mit Id, Tagen und Historie zurück.

Weiterhin **keine** `soll_minutes = 0`-Regel — ein komplett krankgeschriebener Zeitraum behält sein
Soll. Der Landing-Tab „Aktiv" der Stundennachweis-Liste ist mit dem Status entfallen (`views[0]`
ist wieder „Alle"), ebenso der Tab „Kann sich nicht selbst heilen".

Der Satz, der überall stimmen muss: **der Zeitraum ist nicht geschlossen, er ist weg — und er kommt
von selbst zurück.**

- **approve-stundenfreigabe** — Statustabelle zurück auf fünf, Abschnitt *`closed` / Ohne Einsatz*
  gestrichen, Landing-Tab-Absatz auf „Alle" korrigiert (inkl. des Hinweises, dass es weder „Aktiv"
  noch „Kann sich nicht selbst heilen" gibt). Die Materialisierungs-Gates führen jetzt die
  Freigebbarkeits-Regel, und *Which periods the employee actually sees* trägt den Papierkorb-Fall
  als eigenen Block: Auffinden über `search-model` auf `0-426` mit `trashed: "only"`, kein
  Hand-Restore anbieten, Beweis-Blocker (Bestätigung, Freigabe, signierter Tag, `invoiced_at`,
  offene Korrektur, jeder Status außer `open`) unverändert. Trigger für „der Zeitraum ist plötzlich
  weg" ergänzt.
- **head-of-disposition** — sechs zurück auf fünf; der Rat „`closed` aus jeder Backlog-Zahl
  ausschließen" ist gegenstandslos (solche Zeiträume sind schlicht nicht da) und durch die
  Umkehrung ersetzt: **verschwindende** Zeiträume sind ein Planungssignal, kein
  Freigabefortschritt. Phasen-Schiene auf vier Stationen, Wartepartei ohne `closed`.
- **using-alluvo-operator** — `TimesheetStatus` wieder fünf Werte; der Navigationseintrag „Warum
  steht der Zeitraum auf *Ohne Einsatz*" heißt jetzt „Der Zeitraum ist weg" und beschreibt
  Papierkorb statt Endstatus.
- **record-absence** — eine Krankmeldung über den ganzen Zeitraum **entfernt** ihn in den
  Papierkorb, statt ihn zu schließen; eine Ablehnung **stellt dieselbe Zeile wieder her**. Dass die
  Wochen-Neuberechnung die soft-gelöschten Zeilen einschließt, ist genau der Mechanismus dahinter.

### Fixed — 2026-09-01 Task-Wiederholungsfelder über die generischen Tools: schreibbar, aber ohne Wirkung (alluvo#4497)

`repeat_interval`, `repeat_frequency` und `repeat_until` haben in `Store/UpdateTaskRequest`
Validierungsregeln bekommen (alluvo#4496). Vorher hat die `validated()`-Allowlist sie
kommentarlos verworfen — `manage-model` / `bulk-manage-model` auf `0-5` meldete Erfolg für
einen Schreibvorgang, der nie stattfand. Die Felder landen jetzt tatsächlich am Datensatz.

**Die Aufgabe wiederholt sich damit trotzdem nicht.** `is_repeating` hat weiterhin keine Regel
und wird nirgends abgeleitet — wer es mitschickt, bekommt es im ⚠️ IGNORED-FIELDS-Block zurück.
Genau auf dieses Flag filtert der Scheduler, wenn er die nächste Instanz erzeugt. Ein über den
generischen Pfad geschriebener Wiederholungsrhythmus ist also Dokumentation, keine Serie. Als
api-seitige Lücke gemeldet: alluvo#4519.

- **head-of-disposition** — der Satz "Keep `manage-task` for what the bulk path can't do:
  repeating tasks (`repeat_interval`)" stimmte so nicht mehr und stimmt in der naheliegenden
  Gegenrichtung erst recht nicht. Ersetzt durch die genaue Lage: die drei Felder persistieren
  (mit den fünf gültigen `repeat_interval`-Werten und der Offset-Pflicht auf `repeat_until`,
  wie bei `due_at`), `is_repeating` nicht, und für eine echt wiederkehrende Delegation bleibt
  `manage-task` `action: "create"` der Weg — es setzt das Flag selbst und defaultet
  `repeat_frequency` auf 1. Dazu der Hinweis, dass es **keinen** MCP-Weg gibt, eine bestehende
  Aufgabe wiederkehrend zu machen (`manage-task` `update` ignoriert die Repeat-Felder
  vollständig), und die Ansage, das offenzulegen statt eine Serie zu berichten, die nicht
  existiert.
- **call-summary** — dieselbe Korrektur an der Stelle, an der die Follow-up-Tasks aus dem
  Debrief geschrieben werden: `manage-task` bleibt für den wiederkehrenden Follow-up und den
  Ticket-Thread (`ticket_id`) zuständig, aber aus dem richtigen Grund.

**Keine Änderung nötig:** die AÜV-Stage-Tabelle in `manage-assignment-contract-prompt` wurde in
derselben api-Änderung von einer linearen Kette auf den echten
`ContractStage::allowedTransitions()`-Graphen korrigiert. **manage-contract-lifecycle** führt
diesen Graphen bereits feldgenau — inklusive `won` nur aus `sent`, `won` ohne Weitergang und
`cancelled` als Endzustand. Gegen den Enum abgeglichen, keine Abweichung, kein Widerspruch zur
neuen Prompt-Tabelle.

### Fixed — 2026-09-01 Zehn entfernte MCP-Tools aus den Skills getilgt (alluvo#4503)

alluvo#4502 hat zehn veraltete Shim-Tools vom MCP-Server entfernt. Vier Skills haben sie noch
als aufrufbar beschrieben; jede Stelle zeigt jetzt auf die tatsächlich deckende Oberfläche:

- **onboard-new-employee**: Der Absatz am Ende von Schritt 5 nannte
  `get-employee-invitation-status` und `invite-employee-user` als „deprecated fallbacks",
  die man nutzen soll, falls `manage-record-action` die `invite-user`-Action nicht listet.
  Beide Tools existieren nicht mehr — es gibt keinen Fallback. Einladungsstatus kommt aus
  `operation: "list"` auf `0-2` (Verfügbarkeit und `unavailable_reason` des
  `invite-user`-Eintrags), Einladen und Erneut-Senden aus `action: "invite-user"`.
- **manage-contract-lifecycle**: `copy-safety-agreement-template` an zwei Stellen (die
  `client_site_safety_agreement_id`-Regel bei `add_role`/`update_role` und die
  Unresolved-fields-Tabelle) ersetzt durch `manage-record-action` →
  `action: "copy-from-template"` auf dem **Template**-Datensatz (`0-342`, `is_template: true`)
  mit `data: {"client_site_id": <site id>}`, Preview mit `confirmed: false` zuerst. Die
  Idempotenz ist jetzt benannt: derselbe Aufruf zweimal liefert den bestehenden Klon zurück,
  nie ein Duplikat.
- **clean-inbox**: Die wörtlich zitierte Fehlermeldung von `mode: "employee_app"` verwies auf
  `invite-employee-user`. Der Servertext lautet jetzt „invite them via the invite-user record
  action (manage-record-action) before opening a conversation" — Zitat angeglichen, damit die
  Meldung wiedererkennbar bleibt.
- **triage-data-quality**: Der Hinweis zu `open-data-quality-dashboard` nannte das Tool einen
  „deprecated alias". Es ist entfernt; `get-issues-overview` mit `action: "open-dashboard"`
  ist der einzige Weg ins Data-Quality-Dashboard.

Die übrigen sechs entfernten Tools (`get-employee-stats`, `list-employee-document-types`,
`manage-trash`, `manage-assignment-feedback`, `manage-contact-formality`, `manage-onboarding`)
kamen in keinem Skill vor — keine Änderung nötig.

### Changed — 2026-09-01 `log-signal` und Weiterleitungsziele laufen jetzt über Record-Action bzw. `manage-model` (alluvo#4506)

Fünf MCP-Tools wurden zu `#[McpExposed]`-Actions bzw. den generischen Model-Tools
degradiert (`manage-playbook`, `manage-compliance-certificate`,
`manage-inbox-forwarding-targets`, `normalize-contact-education`, `log-signal`). Drei
Skills nannten zwei davon beim alten Tool-Namen und hätten ins Leere gegriffen:

- **log-company-signal** — Schritte 2 und 4 rufen nicht mehr das entfallene Tool
  `log-signal`, sondern die **Record-Action `log-signal` auf der Firma**:
  `manage-record-action`, `operation: "execute"`, `model_type: "0-3"`,
  `record_id: <company>`, `action: "log-signal"`, Nutzlast in `data`. Das vollständige
  Feldset ist jetzt dokumentiert (`type` und `title` Pflicht, `title` ≤ 500 Zeichen,
  dazu `description`, `metadata`, Kind-Einträge `signals: [{title, description?,
  source_url?}]` und `contact_ids`). Neu benannt: die **Fingerprint-Deduplizierung** —
  dasselbe Signal zweimal zu loggen legt keinen Zweitsatz an, sondern frischt
  `last_seen_at` der bestehenden Signalgruppe auf und meldet `deduplicated: true`; das
  Skill soll das so berichten statt ein neues Signal zu behaupten. Ebenfalls ergänzt:
  Schreiben verlangt die Berechtigung `signals.create`. Die Ausgabe nennt jetzt die
  Signalgruppen-ID statt einer "Signal-ID · Zeitstempel"-Zeile, die die Action nicht
  zurückgibt. Die sechs gültigen Typen bleiben unverändert.
- **prospect-companies** — Schritt 6 verweist beim Loggen eines Markttriggers auf
  dieselbe Record-Action (statt auf das Tool) und quer auf `→ log-company-signal`.
- **clean-inbox** — der Abschnitt *"Configuring forwarding targets"* beschrieb
  `manage-inbox-forwarding-targets` mit `action: "list"` / `action: "set"`. Die
  Weiterleitungsziele sind jetzt das Feld `forward_targets` auf dem **Inbox-Record**:
  Lesen mit `get-model`, Schreiben mit `manage-model` (`action: "update"`,
  `model_type: "0-301"`, `id: <inbox>`, `data: {"forward_targets": [{email, label}]}`,
  `label` ≤ 100 Zeichen). Vollständiges Ersetzen statt Anhängen und die
  Zweistufigkeit gelten weiter. Neu ausbuchstabiert ist die **Berechtigungsgrenze**: `forward_targets`
  verlangt *settings-manage* — enger als das `inboxes.edit` der übrigen Inbox-Felder —
  und die Degradierung des Tools hat sie nicht aufgeweicht; das Skill meldet die
  Ablehnung, statt sie zu umgehen. Der Verweis weiter oben bei `manage-ticket`
  `action: "forward"` zeigt entsprechend nicht mehr auf das entfallene Tool.

Für `manage-playbook`, `manage-compliance-certificate` und `normalize-contact-education`
war keine Änderung nötig — kein Skill referenziert diese Flächen.

### Changed — 2026-09-01 Personalakten-Audit läuft jetzt über `manage-employee-document` `action: "audit"` (alluvo#4499)

Das eigenständige Tool `audit-employee-documents` gibt es nicht mehr — es ist unverändert in
`manage-employee-document` als `action: "audit"` aufgegangen (gleicher Auswertungspfad, gleiche
Ausgabe, weiterhin rein lesend). Beide Modi bleiben: ein einzelner Mitarbeiter über
`employee_id`, oder ein Massenlauf über `filters` (`status`: `all` / `has_missing` /
`has_expiring` / `has_expired`, `limit` max. 100, `offset`), in beiden Fällen mit optionalem
`expiring_within_days` (Standard 30).

- **profilvertrieb**, **call-summary**, **approve-stundenfreigabe** — alle drei Stellen, die für
  `employee_document_ids` bzw. für die Kontrolle des `reimbursement_period_statement` auf das
  alte Tool verwiesen, nennen jetzt den neuen Aufruf. In profilvertrieb steht zusätzlich, wo die
  `document_id` je Dokumenttyp wirklich steht: in den strukturierten Daten der Antwort — die
  Markdown-Ausgabe druckt nur Bezeichnung, `type_code` und Ablaufdatum.

Ebenfalls in derselben Zusammenlegung entfallen: `manage-record-card` ist in
`manage-record-view` (`resource: "card"`) aufgegangen. Kein Skill hat die Kartenbibliothek je
angesprochen, daher ändert sich dort nichts.

### Changed — 2026-09-01 Fünf MCP-Prompts sind ausgedünnt — die Skills sind jetzt der einzige Ort dieser Abläufe (alluvo#4515)

Fünf Prompts des MCP-Servers wurden auf eine kurze Startfrage bzw. ein kompaktes Faktenblatt
reduziert, weil die Operator-Skills die Abläufe ohnehin führen: `manage-meta-ads-prompt`,
`manage-ticket-prompt` (nur der Zero-Inbox-Block), `manage-employee-prompt`,
`invite-employee-user-prompt` und `issue-triage-prompt`. Kein Prompt wurde umbenannt oder
entfernt — Skills, die einen Prompt beim Namen rufen, sind unverändert. Geprüft wurde, ob die
zuständigen Skills wirklich alles abdecken, was die gestrichene Prosa gelehrt hat:

- **clean-inbox** — deckt die Zero-Inbox-Regeln vollständig ab (Schließen nur mit belegter
  Evidenz inkl. `close_reason_id`/`close_reason_note`, keine erfundenen operativen Daten,
  Anhänge vor dem Urteil lesen, Rückfrage statt Entscheidung bei Geld/Frist/Kündigung/
  Mutterschutz/Elternzeit/AU/Sozialversicherung, Newsletter-Cluster). Keine Änderung nötig.
- **triage-data-quality** — führt den Ablauf Überblick → Gruppieren → Remediation lesen →
  bestätigen → ausführen bereits vollständig. Keine Änderung nötig.
- **manage-meta-ads** — die EMPLOYMENT-Targeting-Verbote (kein Alter, kein Geschlecht, keine
  Interessen) standen schon da; ergänzt ist nur die **Radius-Untergrenze**: Meta lehnt auf
  einem EMPLOYMENT-Ad-Set alles unter ca. 24 km (15 mi) ab, also mit **≥ 25 km** planen und
  lieber weitere Städte ergänzen, statt einen Kreis enger zu ziehen.
  Nicht übernommen wurde der alte Hinweis, die „Total spend" aus `campaign_insights`
  `overview` sei Lifetime-Spend: der Wert respektiert inzwischen `date_preset` (verifiziert in
  `MetaInsightsService::getAccountSpend()`), der Hinweis ist überholt.
- **onboard-new-employee** — hier gab es tatsächlich eine Lücke: der Skill löst zwar auf
  „neuen Mitarbeiter anlegen" aus, begann bisher aber erst beim schon vorhandenen Datensatz.
  Neu ist **Schritt 0 „Create the employee record"**: Referenzen vorab auflösen (Owner `0-1`,
  Manager `0-2`, Sector `0-70`, Position `0-71`, Branch `0-73`), den **Employee** anlegen und
  nie vorab den Contact — `manage-model` `0-2` `create` matcht die Identität selbst über
  E-Mail, dann Name + Geburtsdatum, und legt den Contact (`0-105`) nur an, wenn nichts passt;
  Namensdubletten kommen als `⚠️ POSSIBLE DUPLICATE`-**Warnung**, nicht als Ablehnung zurück
  (zusammenführen über `manage-duplicates`). Ebenfalls neu: `is_active` wird **nie** gesetzt,
  sondern aus der EmploymentPeriod (`0-18`) abgeleitet — die Period erst mit dem echten
  Eintrittsdatum anlegen (ein geratenes Datum hat AÜG- und Lohnfolgen), und die
  Personalnummer ist nicht die Record-ID (über `search-model` auflösen).

Der Gate `invite-user` mit seinem `unavailable_reason`-Vertrag stand in onboard-new-employee
schon ausführlicher als im Prompt und bleibt unverändert.

### Changed — 2026-09-01 `manage-assignment-contract`: drei neue `describe`-Topics, Schema-Beschreibungen als Einzeiler (alluvo#4501)

Der Guidance-Katalog hinter `manage-assignment-contract(action: "describe")` ist von fünf auf
**acht Topics** gewachsen: neu sind `surcharges`, `work-tasks` und `pricing-and-hours`. Am
Aufruf ändert sich nichts — Parameter, Typen, Pflichtfelder und Enum-Werte sind unverändert.
Zusätzlich sind die Parameter-Beschreibungen im Schema jetzt Einzeiler, die auf das passende
`describe(topic: …)` verweisen; die ausführliche Erklärung steht nur noch dort.

- **manage-contract-lifecycle** — die Topic-Aufzählung im Abschnitt *"Long-form AÜV guidance
  now lives behind `action: "describe"`"* nennt jetzt alle acht Topics und ordnet die drei
  neuen den Abschnitten zu, die dieses Skill ohnehin führt (`surcharges` → Zeilenformat von
  `sync_surcharges`, Bruch-statt-Prozent-Skala, `is_exclusive`; `work-tasks` →
  `sync_work_tasks` als vollständige Ersetzungsliste plus `seed_role_work_tasks` beim
  `create`; `pricing-and-hours` → `hours_arrangement` inkl. `per_deployment` und die Bedeutung
  von `hours` je Action). Neu festgehalten: eine kurze Schema-Beschreibung ist **kein** Beleg
  dafür, dass eine Regel entfallen ist — erst das Topic lesen, dann schließen.
- **using-alluvo-operator** — dieselbe Topic-Liste im Navigator-Abschnitt *"Fetching docs on
  demand"* ergänzt, mit je einem Stichwort, was in den neuen Topics steht.

### Fixed — 2026-09-01 `get-open-tasks` entfernt, Outreach-/Landing-Page-/Task-Verben getrimmt (alluvo#4513)

alluvo#4512 hat zwei MCP-Tools zurückgezogen und drei auf ihren Kern zusammengestrichen. Neun
Skills beschrieben die alten Verben noch als aufrufbar — jede Stelle zeigt jetzt auf die
tatsächlich deckende Oberfläche:

- **`get-open-tasks` ist weg** — offene Aufgaben laufen über `search-model`/`query-model` auf
  `0-5` (Task). Wichtig und in den Skills jetzt benannt: `owner_id` ist hier **nicht** implizit
  wie beim alten Tool, ohne diese Bedingung kommen die Aufgaben aller Nutzer zurück. Status ist
  `not_started`/`in_progress`/`completed`, ein separates „open"-Flag gibt es nicht, und `body`
  kommt ungekürzt statt als ~150-Zeichen-Auszug. Betrifft **daily-briefing** (Schritt 1 komplett
  neu als `query-model`-Aufruf), **bench-check** (Anschlusseinsatz-Tasks per `search-model`),
  **match-bench-to-clients** und **using-alluvo-operator** (zwei Erwähnungen in den
  Querschnitts-Abschnitten zu `subject_id` und Namensdarstellung).
- **`manage-outreach-enrollment` kann nur noch `create` und `bulk-enroll`.**
  `pause`/`resume`/`unenroll` (samt Bulk-Varianten) sind Record-Actions auf `0-125` —
  `pause_enrollment` / `resume_enrollment` / `complete_enrollment` über `manage-record-action`,
  in Snake-Case und mit `operation: "execute_bulk"` für den Stapel. `complete_enrollment` **ist**
  das Unenroll und ist irreversibel, anders als Pause. `check`/`list`/`stats` sind
  `search-model`/`query-model`/`count-model` auf `0-125`. **enroll-outreach** hat dafür eine neue
  Intent-Tabelle statt der alten Action-Tabelle bekommen; **daily-briefing** (Schritt 3) und
  **head-of-sales** (Outreach health) lesen die Kennzahlen jetzt direkt vom Modell — inklusive
  der Korrektur, dass es die dort behaupteten Status `reply_received` / `awaiting_manual_step`
  nie gab: Statuswerte sind `active`/`paused`/`completed`, „wartet auf den Operator" liest man an
  `draft_emails_count` > `approved_emails_count` ab. **profilvertrieb** verweist an drei Stellen
  entsprechend weiter.
- **`manage-task` kann nur noch `create` und `update`.** `complete` ist die Record-Action
  `mark-as-completed` auf `0-5`, `bulk-update` ist `bulk-manage-model` auf `0-5` — mit dem
  Formwechsel: ein `operations`-Eintrag pro Task-ID statt eines Änderungssatzes für viele
  `task_ids`, und ISO-Datetime mit Offset statt tenant-lokalem `Y-m-d H:i`. Betrifft
  **head-of-disposition** und **clean-inbox** (Fälligkeiten staffeln). `manage-ticket` behält
  sein `bulk_update` mit Unterstrich — unverändert.
- **`manage-campaign-landing-page`** schaltet Seiten nicht mehr selbst live:
  `activate-landing-page` / `deactivate-landing-page` sind Record-Actions auf `0-340`. Kein Skill
  hat die alten Verben dokumentiert; **manage-meta-ads** fordert aber zum Aktivieren auf und
  nennt jetzt den passenden Aufruf.

`manage-portal-access` (ebenfalls entfernt) kam in keinem Skill vor — die Skills nutzen längst
`assign-portal-roles` / `send-portal-invitation` über `manage-record-action` und lesen den
Mitgliedschaftsstatus auf `0-430`. Keine Änderung nötig.

### Added — 2026-09-01 Öffentliche Buchungslinks (`0-444`) und unbestätigte Reservierungen (`0-445`) über MCP (alluvo#4355)

Zwei neue Model-Types stehen dem Assistenten offen: `MeetingBookingLink` (`0-444`) mit vollem
Lese- und Schreibzugriff über die generischen Model-Tools plus vier Record-Actions
(`copy-booking-link`, `copy-booking-embed-snippet`, `activate-booking-link`,
`deactivate-booking-link`), und `MeetingBookingRequest` (`0-445`) **nur lesend** — eine
Reservierung schreibt ausschließlich der Buchungsservice. Damit kann ein Operator seinen
öffentlichen Terminlink erstmals per Assistent anlegen, aktivieren, einbetten und auswerten.

- **clean-inbox** — neuer Abschnitt *"Öffentliche Buchungslinks — `MeetingBookingLink`
  (`0-444`)"* direkt nach der Vorlaufzeit, weil dort schon `manage-booking-availability`,
  MeetingType (`0-348`) und die Geschäftszeiten als Fallback-Buchungsfenster stehen. Enthält:
  die Host-Regeln (`user_id` ist beim Anlegen Pflicht, Nicht-Admins dürfen nur sich selbst
  eintragen, beim Bearbeiten fehlt das Feld ganz — ein Link wird nie umgehängt), die
  Aktivierungssperre ohne aktive Google-Kalender-Verknüpfung, die vier Zustände, in denen ein
  *aktiver* Link trotzdem nichts anbietet (`calendar_disconnected`, `calendar_unreadable`,
  `host_inactive`, `host_paused` — Letzteres rendert einen leeren Kalender, der wie "ausgebucht"
  aussieht), die Vererbungskette `null` → Link → MeetingType (nur `min_notice_minutes`) →
  Verfügbarkeit des Hosts, die validierten Feldgrenzen inklusive der reservierten Slugs
  `confirm`/`manage`, `record_target` (`contact_only` / `candidate` / `company_lead` — der
  Kontakt entsteht immer), die strengen Regeln für `allowed_origins` (ein blankes `*` wird
  abgelehnt) und `theme`/`font_css_url`, die vier Actions samt Berechtigung, sowie die
  Filterfelder für "wer hat gebucht, aber nicht bestätigt" mit dem Hinweis, dass abgelaufene
  Reservierungen weggeräumt werden — ein leeres Ergebnis ist kein Beleg dafür, dass niemand
  gebucht hat. Trigger für Buchungslink/Terminlink/Einbettungscode/offene Reservierungen ergänzt.
- **using-alluvo-operator** — drei neue Navigationseinträge: Buchungslink anlegen bzw. teilen,
  "mein Buchungslink zeigt keine Termine" (die vier Zustände, bevor an den Einstellungen
  gedreht wird), und "wer hat gebucht, aber nicht bestätigt" (`0-445`, read-only).
- **profilvertrieb** — der Querverweis auf `clean-inbox` nennt jetzt auch den Buchungslink als
  CTA für die 1:1-Mail, mit `copy-booking-link` statt einer aus dem Gedächtnis gebauten URL.

**Bekannte Lücke, bewusst so dokumentiert:** `record_source_detail` wird auf `0-444` von beiden
Form Requests validiert, fehlt dem Model aber in `$fillable` — `manage-model` meldet es unter
*IGNORED FIELDS* zurück und speichert nichts. Genau dieses Feld wäre der Herkunftstext, den
jeder über den Link entstehende Kontakt tragen soll. Die Skill sagt darum ausdrücklich: nicht
senden. API-seitig als alluvo#4509 gemeldet.

### Fixed — 2026-09-01 Tätigkeitsnachweis-Tabelle: `full` hat elf Spalten, Soll spannt drei, Pausenfenster dokumentiert (alluvo#4402)

Zwei Korrekturen an dem, was der Tätigkeitsnachweis tatsächlich druckt — beide aus
`52bd11830e` ("print the clocked break windows"), das die Spaltenarithmetik geändert hat, ohne
eine `plugin: review`-Issue zu öffnen. `TimesheetPlannedHoursDisclosure::tableColumnCount()` ist
7 + 1 (Abw.) + **3** = **elf**, nicht zwölf: der **Soll**-Block spannt Zeit · Pause · Std., seine
Von- und Bis-Werte teilen sich eine Zelle (`06:00–14:12`), nur **Ist** trennt Von und Bis. Die
Asymmetrie ist Absicht — die frei gewordene Breite trägt die Pausenfenster. Kein MCP-Tool und kein
Enum-Wert hat sich geändert; `none`/`delta_only`/`full` und die Setting-Keys bleiben wie
dokumentiert.

- **approve-stundenfreigabe** — *Tabelle* und die Disclosure-Tabelle sagten "zwölf Spalten" und
  "Soll und Ist, each spanning Von · Bis · Pause · Std."; beides korrigiert (elf Spalten, Soll =
  Zeit · Pause · Std.). Wichtig über Pedanterie hinaus: wer einem Operator eine "Soll-Von-Spalte"
  nennt, schickt ihn auf eine Spalte, die es nicht gibt — genau in dem Soll-Ist-Vergleich, für den
  `full` existiert. Neuer Block zu den **erfassten Pausenfenstern**: die Ist-Pause-Zelle druckt
  unter der Dauer, *wann* die Pause lag (`09:51–10:21`, mehrere stapeln sich) — § 4
  ArbZG-Nachweis auf dem Dokument, das der Entleiher unterschreibt, und zwar bei allen drei
  Disclosure-Werten. Nur wo die Fenster exakt die gedruckte Dauer ergeben; sonst steht kursiv
  *"korrigiert"* statt der Zeiten (die vereinbarte Dauer wurde nachträglich geändert — **nicht**
  "keine Pause erfasst"). Dazu, woher ein Fenster überhaupt kommt: eine eigene `break`-Zeitbuchung
  mit Start und Ende; die Stoppuhr-Pause speichert keins, ebenso wenig eine bloß eingetippte Dauer,
  und die Fenster sind auf den Einsatz dieses Nachweises begrenzt. Trigger für "wann war die
  Pause", "Pausenfenster" und "warum steht korrigiert bei der Pause" ergänzt.
- **using-alluvo-operator** — der `document_planned_disclosure`-Eintrag sagte "gespiegelter
  Soll-Block (Von/Bis/Pause/Std.)"; auf drei Spalten und elf Gesamtspalten korrigiert. Neuer
  Navigationseintrag für die Pausenfenster und das "korrigiert".
- **build-dienstplan** — "the whole planned block mirrored next to Ist (Von · Bis · Pause · Std.)"
  im Abschnitt *The Dienstplan is printed on the document the client signs* auf den realen
  Dreispalten-Block korrigiert.

### Changed — 2026-09-01 Passwortloser Login: `check-email` weg, E-Mail-Auth-Flag gelöscht, `locked_out`-Bucket abgeschafft (alluvo#4474)

OTP ist jetzt der einzige Standard-Loginweg. Der Endpunkt `/login/check-email` ("OTP oder
Passwort?") ist gelöscht, das Benutzerfeld `has_email_authentication` existiert nicht mehr, und
`InviteUser` repariert es folglich auch nicht mehr. Damit ist die Situation weg, die Operatoren
früher per Neu-Einladung zu heilen versuchten: **jedes Konto mit funktionierender Adresse bekommt
einen Code.** Neu dazu: ein Mitarbeiter kann sich **selbst** ein Passwort setzen oder
zurücksetzen — vom Login ("Passwort setzen") oder unter *Einstellungen → Passwort*, immer hinter
einem frisch gemailten Code. Auf *Auswertungen → Mitarbeiter-App* fällt die vierte Liste
"Freigeschaltet, aber Login unmöglich" weg (ebenso die Trichterstufe `can_log_in` und die
Roster-Spalte); es bleiben drei Listen: `no_life_sign`, `invitable`, `not_invitable`. Kein
MCP-Tool, kein Parameter und kein Enum-Wert hat sich geändert — die Drift steckt im Produktfluss
und in dem, was die Adoption-Seite meldet.

- **onboard-new-employee** — der Block *"Der Mitarbeiter hat nie einen Code bekommen"* nannte ein
  Flag, das es nicht mehr gibt, und erklärte, warum ein Resend den Fall *nicht* heilt. Ersetzt
  durch die drei realen Ursachen (noch kein verknüpftes Benutzerkonto → einladen; falsche/alte
  Adresse → `email` auf `0-2` korrigieren; schlichte Mailzustellung) plus den Hinweis, dass der
  "Code gesendet"-Screen **nichts** beweist: die Antwort ist absichtlich für bekannte und
  unbekannte Adressen identisch. Neuer Abschnitt zum Selfservice-Passwort (beide Einstiege, der
  Code-Zwang, "Stattdessen mit Passwort anmelden") mit der Ansage, nie einen operatorseitigen
  Reset zuzusagen und nie in Authentifizierungsfelder zu schreiben — ob jemand überhaupt ein
  Passwort hat, ist bewusst nirgends ablesbar. Der Verweis auf die Adoption-Seite listet jetzt
  Trichter und die drei verbliebenen Arbeitslisten. Trigger für "kann sich nicht anmelden",
  "bekommt keinen Code" und "Passwort vergessen/zurücksetzen" ergänzt.
- **using-alluvo-operator** — neuer Navigationseintrag "Mitarbeiter kann sich nicht anmelden /
  bekommt keinen Code / Passwort vergessen" → `onboard-new-employee` (Schritt 5), ausdrücklich
  abgegrenzt vom Kundenportal-Fall (PortalMembership `0-430`), der unverändert bleibt: dort
  sperrt eine `disabled` Mitgliedschaft den Code weiterhin.

### Changed — 2026-09-01 §5/ClientSite-Regel ist aus der Tool-Description in `describe(topic: "framework-linkage")` gewandert (alluvo#4493)

Rein eine Fundort-Verschiebung: `manage-assignment-contract` hat seine Beschreibung gekürzt (die
`tools/list`-Nutzlast lief gegen ihre 400.000-Zeichen-Grenze) und trägt die §5-Passage nur noch
als Einzeiler mit Verweis. Der vollständige Text — §5 *Erklärung des Kunden*, die
Branchenzugehörigkeit, `client_site_id`, das Anlegen eines Einsatzbetriebs über `manage-model`
(`0-341`) und die Tatsache, dass ein AÜV **unter** einem Rahmenvertrag die Erklärung erbt und den
Check überspringt — ist jetzt der Kopf des Topics `framework-linkage`. **Kein Tool, kein
Parameter und kein Verhalten hat sich geändert**, nur die Sichtbarkeit: was früher ungefragt im
Kontext stand, kostet jetzt einen `describe`-Aufruf.

- **manage-contract-lifecycle** — Schritt 2 (*Create Einsatzvertrag*) nannte die Regel für den
  **standalone** AÜV bisher nirgends; sie stand nur an FC-Stellen (Sendegate, `update`-Guard,
  Match-Draft). Neuer Block: ohne `framework_contract_id` braucht der AÜV einen Einsatzbetrieb mit
  `industry_classification`, sonst rendert §5 nicht — `client_site_id` explizit setzen oder über
  `manage-model` (`0-341`) anlegen/korrigieren; unter einem Rahmenvertrag entfällt der Check. Dazu
  ein zweiter Block, der das Topic-Verzeichnis des Tools benennt (`stage-machine`,
  `multi-einsatz`, `imports`, `field-derivation`, `framework-linkage`; `describe` ist read-only
  und ohne Berechtigung aufrufbar, ohne `topic` listet es die Themen) mit der Ansage, bei einer
  Lücke zu fragen statt aus dem Fehlen in der Tool-Description eine Regel abzuleiten.
- **using-alluvo-operator** — der `describe`-Absatz sprach nur von Feldlisten pro Aktion/Resource.
  Für `manage-assignment-contract` ist die Einheit ein **`topic`**; die fünf Topics sind ergänzt,
  ebenso der Hinweis, dass die §5/ClientSite-Regel dort und nicht mehr in der Beschreibung steht.

### Changed — 2026-08-31 `TimesheetStatus` hat einen sechsten Wert: `closed` / "Ohne Einsatz" (alluvo#4489)

Ein Stundennachweis-Zeitraum, in dem kein einziger Tag von irgendwem freigegeben werden kann,
landet automatisch im neuen Endstatus `closed` ("Ohne Einsatz", EN "No activity") — alle
Schichten storniert/gelöscht, oder **jeder** Tag durch eine gemeldete Krankmeldung gedeckt.
Endstatus wie `invoiced`, aber ohne Unterschrift erreicht und deshalb **nie abrechenbar**
(`isBillable()` bleibt Approved-only). `TimesheetLifecyclePhase` bekommt ein passendes
`closed`, das Schienenposition 4 mit `invoiced` teilt — ein alternatives Ende, keine weitere
Station. Wartepartei ist `nobody`. Die Liste *Stundennachweise* startet neu auf dem ersten Tab
**"Aktiv"** (`open_periods`), der `closed` ausblendet; "Alle" bleibt unverändert. Drei Skills
nannten die alte Zahl als harte Tatsache.

- **approve-stundenfreigabe** — Statustabelle und Ansichtenzählung auf sechs korrigiert, neuer
  Abschnitt *`closed` / Ohne Einsatz*. Die drei Punkte, die sonst falsch beantwortet werden:
  (1) **niemals an `soll_minutes = 0` erkennen** — ein komplett krankgeschriebener Zeitraum
  behält sein Soll, 23,10 h Soll gegen 0,00 h Ist ist ein legitimes `closed`; (2) geschlossen
  wird **nur** ein `open` Zeitraum ohne Beleg (keine Bestätigung, keine Freigabe `0-435`, kein
  vom Kunden signierter Tag, keine offene Korrektur), und der einzige Weg heraus ist ebenfalls
  automatisch (Schicht wieder eingeplant → `open`); (3) es gibt **keinen MCP-Schreibweg und
  keine Aktion** dafür — "Zeitraum schließen" nie als Schritt anbieten. Dazu: der Abschnitt
  "warum existiert der Zeitraum gar nicht" trennt jetzt *nie materialisiert* von *existiert,
  ist aber Ohne Einsatz* und schickt zuerst auf den Tab "Alle".
- **head-of-disposition** — "genau fünf Werte" → sechs; `closed` muss aus jeder Backlog-Zahl
  heraus (nie in freigegebene Stunden oder eine Abrechnungsreife-Zahl falten), und eine
  steigende `closed`-Quote ist ein **Planungs**-Signal, nicht eines der Stundenfreigabe.
  Phasen-Hinweis zur geteilten Position 4 ergänzt.
- **using-alluvo-operator** — "fünf Werte" → sechs, plus neuer Navigationseintrag "Warum steht
  der Zeitraum auf *Ohne Einsatz* / warum finde ich die Woche nicht in der Liste".
- **record-absence** — der Rebuild nach jeder Abwesenheits-Transition erfasst jetzt `open`
  **und** `closed`; neuer Callout, dass eine den ganzen Zeitraum deckende Krankmeldung ihn auf
  Ohne Einsatz setzt und eine Ablehnung ihn wieder öffnet.

### Changed — 2026-08-31 Day-Wizard als einzige Tagesfläche + Abweichungsfrage entfällt im §-4-Fall (alluvo#4480)

Die Mitarbeiter-App hat nur noch **eine** Tagesfläche. Erfassen, Bearbeiten und Abschluss laufen
durch den Wizard: „Tag prüfen & abschließen" öffnet ihn mit dem **gespeicherten** Tag vorbefüllt,
endet auf einem Prüfschritt und schreibt beim Bestätigen den ganzen Tag in einer Transaktion neu
(`log-day` mit `replace_existing`) und schließt ihn. Einzeleintrags-Editor, Einzelsegment-Dialog
und der separate „Tag abschließen"-Knopf sind weg; die Eintragszeilen sind durchgehend read-only.

- **approve-stundenfreigabe** (*Changing a closed day*): die Aufzählung „alle fünf
  Self-Service-Schreibwege (… Eintrag bearbeiten, Eintrag löschen)" beschrieb zwei Wege, die es
  nicht mehr gibt. Ersetzt durch einen Callout über den Wizard — samt der **einen Ausnahme**, in
  der der direkte „Tag abschließen"-Knopf bestehen bleibt: ein Tag mit Einträgen aus **mehreren
  Einsätzen** lässt sich nicht als eine Spanne plus Pausen ausdrücken, wäre sonst gar nicht mehr
  abschließbar. Ausdrücklich dazu: einem Mitarbeiter nie mehr „tippe den Eintrag an und bearbeite
  ihn" sagen. Der atomare Rewrite verweigert freigegebene/genehmigte Stunden und einen bereits
  abgeschlossenen Tag — die Regel „erst zurückziehen, dann neu abschließen" gilt unverändert.
- **approve-stundenfreigabe** (*Tagesabschluss*, „When it fires"): die Abweichungsfrage **entfällt**,
  wenn die §-4-Frage ohnehin kommt und die **Brutto**-Anwesenheit dem Plan entspricht (gleiche
  5-Minuten-Toleranz). So ein Tag trägt `no_break_reason` und **keinen** `deviation_reason` /
  `deviation_reason_code`, obwohl `deviation_minutes` ungleich 0 ist. Nur dann: eine **längere**
  Pause als geplant ist kein §-4-Fall und behält ihre Frage. Gilt gleichermaßen für
  `close_tracked_day_for_employee` — die Aktion baut ihr Formular aus denselben `DayCloseGates`
  und bietet die Abweichungsfelder auf so einem Tag gar nicht erst an.
- **head-of-disposition** (§ Abweichungs-Auswertung): fünfter Caveat. Die
  `group_by: "deviation_reason_code"`-Verteilung ist eine Verteilung der **codierten**
  Abweichungen, nicht aller — die „Pause nicht eingetragen"-Fälle fehlen systematisch, und ihre
  Begründung liegt auf `0-422`, das nicht auf der MCP-Allowlist steht. Den uncodierten Rest nie
  als „unbegründet" ausweisen.
- **approve-stundenfreigabe** (neuer Abschnitt *„Wann soll mein Mitarbeiter die Unterschrift
  holen?"*): die vier neuen Day-Mode-Settings `signature_gap_trigger_days` (2),
  `signature_accumulation_trigger_days` (5), `signature_client_ask_cadence_days` (3),
  `signature_prewarn_days` (3). Im Tagesmodus (`approval_granularity: "day"` **und**
  `DayLevelHoursApproval` für die Firma aktiv) sieht der Mitarbeiter keine Frist mehr, sondern
  einen **Grund**, heute unterschreiben zu lassen. Erreichbar auf beiden Wegen: mandantenweit über
  `manage-settings` (Gruppe `time_tracking_hours_approval`) und pro Firma über
  `manage-record-settings` (`0-3`, Präfix `timesheet.`) — praktisch ist fast immer die Firma
  gemeint. Der Fatigue-Cap ist absichtlich brechbar: „Einsatz endet heute" und „letzte Schicht vor
  dem Periodenschnitt" ignorieren ihn.

  Nachtrag: Beim Verifizieren fehlten die vier im `AppSettingsSchema` von `TimeTrackingApp`, aus
  dem sowohl die Einstellungsseite als auch die `manage-settings`-Allowlist abgeleitet werden —
  `AppRegistrySweepTest` war deshalb auf `main` rot. Nachgezogen in alluvo#4486; dieser Eintrag
  beschreibt den Zustand **nach** dessen Deploy, weshalb dieser Drift-PR erst danach landen darf.

### Changed — 2026-08-31 `invite-user` weist das Postfach eines verbundenen Posteingangs ab (alluvo#4472)

Die Adresse hinter einem verbundenen Inbox-Kanal (`anfrage@`, `verwaltung@`, `hallo@` … —
das unter Einstellungen → Inbox verbundene Gmail-/Outlook-Konto) kann kein persönliches
Benutzerkonto mehr werden: der `InboxMailboxGuard` lässt die **Erst-Einladung** mit einem
422 scheitern, der den Posteingang beim Namen nennt. Ein geteiltes Postfach gehört dem Team,
und seine Login-Codes landen zurück in genau dem Posteingang, den alluvo synchronisiert —
lesbar für jedes Mitglied.

- **onboard-new-employee** — neuer Callout in Schritt 5. Die drei Punkte, die eine
  Wiederholung verhindern: (1) **Es warnt nichts vorher** — die Prüfung gehört nicht zu den
  Gate-Status, `operation: "list"` zeigt `invite-user` ohne `unavailable_reason` als
  verfügbar und `confirmed: false` liefert eine saubere Vorschau; die Ablehnung kommt erst
  bei `confirmed: true`. (2) **Kein transienter Fehler** — nicht erneut versuchen, sondern
  die eigene Adresse der Person erfragen und das `email`-Feld des Employees per
  `manage-model` (`0-2`) korrigieren; auch der Weg über Einstellungen → Benutzer ist kein
  Ausweg, dort greift derselbe Guard. (3) **Resends sind nicht betroffen** (der Guard läuft
  nur auf dem Erst-Einladungs-Pfad), und ein **Weiterleitungsziel** der Inbox ebenso wenig —
  das ist bewusst ausgenommen, weil es regelmäßig die Adresse einer echten Person ist.

### Added — 2026-08-29 Meta-Leads sind MCP-lesbar und als Workflow-Trigger zugelassen (alluvo#4456)

`MetaLead` (`0-313`) hat zum ersten Mal eine MCP-Fläche: der Typ steht in `availableForMcp()`,
taucht also in `list-model-types` als **`read_only`** auf, und `search-model` / `query-model` /
`get-model` akzeptieren ihn. Schreiben bleibt gesperrt (kein Form Request, `editEnabled()` ist
`false`) — Leads schreiben nur der leadgen-Webhook, der Pull-Command und der `MetaLeadProcessor`.
Weil `availableForWorkflowTrigger()` aus derselben Liste abgeleitet ist, nimmt `manage-workflow`
jetzt `trigger_model_type: "0-313"`. Dazu kommen drei angehängte Felder — `lead_name`,
`lead_email`, `lead_phone` —, die aus Metas positionaler `field_data`-Liste gelesen werden.

- **build-automation-agent** — neuer Abschnitt *Trigger on an incoming Meta-Lead (`0-313`)*.
  Kernpunkt, und der Grund für den Abschnitt: **`trigger_event: "created"` feuert mit leerem
  Bewerber.** Auf dem Webhook-Pfad wird die Zeile *vor* dem Abruf der Payload gespeichert
  (capture-before-map, damit eine Einreichung nie an einem fehlenden Mapping verloren geht) —
  zum `created`-Zeitpunkt ist `status` also `pending`, `raw_data` leer und `{{lead_name}}` /
  `{{lead_email}}` / `{{lead_phone}}` rendern **leer**; auf dem Pull-Pfad dagegen nicht. Für
  Der Pfad-Unterschied ist api-seitig als alluvo#4458 gemeldet; bis dahin gilt: für
  alles, was den Bewerber benennt, ist `field_changed` auf `status` (`to: "processed"`, bzw.
  `"skipped"` für „Lead ohne aktives Mapping") die richtige Wahl. Ebenfalls dokumentiert:
  `Candidate:created` ist **kein** Ersatz (der Mapper macht `firstOrCreate` auf `contact_id`,
  ein wiederkehrender Bewerber erzeugt gar kein `created`), die vier `status`-Werte, der Record-
  Root-Key `meta_lead`, dass die drei Antwortfelder **keine Spalten** sind (nicht filter-, sortier-
  oder bedingungsfähig, aber als Platzhalter renderbar), dass eine eigene Qualifizierungsfrage gar
  keinen Platzhalter hat (`{{raw_data}}` rendert leer), und dass `record_actions`-Buttons hier
  nicht greifen.
- **manage-meta-ads** — neuer Abschnitt *Reading the stored leads directly*: wann `query-model`
  auf `0-313` besser ist als `query-meta-ads` `resource: "leads"` `action: "list"` (die Liste
  zeigt IDs und Status, keine Namen), was filterbar ist (`status`, `meta_page_id`, `created_at`)
  und was ausdrücklich nicht (die drei Antwortfelder), dass `search-model` auf `leadgen_id` und
  `error_message` greift, und dass Mapping/`reprocess` weiterhin `manage-meta-ads`-Aktionen
  bleiben. Plus Querverweis auf `build-automation-agent`.
- **using-alluvo-operator** — die Meta-Lead-Routing-Zeile nennt jetzt auch „wer hat sich diese
  Woche über eine Anzeige beworben" und den Typ `0-313`; eine neue Zeile führt „Slack-Meldung,
  wenn ein neuer Meta-Lead reinkommt" nach `build-automation-agent`, mit der `created`-Warnung.

### Changed — 2026-08-29 Timesheet-Status: fünf Werte, „open" ist zwei Situationen (alluvo#4404)

`TimesheetStatus` (`0-426`) hat nur noch **fünf** Werte — `open`, `pending_employee`, `mediation`,
`approved`, `invoiced` (Offen / Wartet auf Mitarbeiter / In Klärung / Freigegeben / Abgerechnet).
`upcoming` und `pending_client` sind zu **`open`** geworden, `disputed`, `escalated` und
`mediating` zu **`mediation`**. Die Skills dokumentierten durchgehend das alte Vokabular, und das
ist die teuerste Sorte Drift: ein `query-model` auf `0-426` mit `status: "pending_client"` liefert
eine **leere Menge statt eines Fehlers**, also liest jede so gebaute Backlog-Zahl still Null.

Der Punkt, an dem die reine Umbenennung nicht reicht: **`open` deckt zwei Situationen ab** — „noch
nichts an den Kunden vorgelegt" und „vorgelegt, die Frist läuft". Die Unterscheidung steht im
Stempel **`submitted_to_client_at`**, nicht im Status. Ein Filter auf `status: open` allein zählt
also laufende Wochen, auf die niemand wartet, mit Wochen zusammen, die tatsächlich beim Kunden
liegen. Beides ist jetzt in `approve-stundenfreigabe` und `head-of-disposition` benannt, samt der
Ansage, den Stempel mitzufiltern und zu sagen, welche der beiden Zahlen berichtet wird.

Neu beschrieben sind außerdem die drei **abgeleiteten** Lesarten neben dem Status: die
materialisierte `lifecycle_phase` (`upcoming` ▸ `in_approval` ▸ `approved` ▸ `invoiced` — `upcoming`
ist damit eine Phase und nie ein Status), die nie gespeicherte **Wartepartei** (`client`,
`time_tracking`, `employee`, `mediation`, `nobody` — ein `open` Zeitraum ohne freigebbaren Tag
wartet auf die **Zeiterfassung**, nicht auf den Kunden) und der **Freigabefortschritt**
(`none` / `partial` / `complete`, nach einer Teilfreigabe als „Kunde (teilweise)"). Wartepartei und
Fortschritt sind pro Anfrage abgeleitet und haben keine Spalte — sie lassen sich nicht filtern oder
gruppieren, und das steht jetzt dabei, damit niemand einen Report darauf verspricht.

Die Gates der vier Aktionen sind auf den neuen Stand gebracht: `approve_by_operator` und
`revoke_release` laufen nur solange der Zeitraum **`open`** ist, „Zur Vermittlung" nur bei
**`mediation`**, `revoke_approval` führt von `Approved` zurück nach **`open`** — und lässt
`submitted_to_client_at` dabei ausdrücklich stehen, die Woche *war* ja beim Kunden. Ebenfalls
korrigiert: die Fristen-Eskalation setzt den Zeitraum auf `mediation` und stempelt `escalated_at`
(einen Status `escalated` gibt es nicht mehr), der Kundenportal-Badge zählt Wochen mit einem
*jetzt* zeichenbaren Tag statt eines Status, und der Hub frischt genau die noch nicht vorgelegten
`open`-Zeiträume auf.

Betroffen: `approve-stundenfreigabe`, `head-of-disposition`, `record-absence`,
`using-alluvo-operator`.

### Added — 2026-08-29 Abwesenheitsarten führen jetzt `description` + `ai_instructions` (alluvo#4437)

Der MCP-Lesepfad hat ein Konzept dazugewonnen: einzelne Datensätze können Anweisungen **an den
Assistenten** tragen. Träger ist der Trait `HasAiInstructions`; erster und bislang einziger
Teilnehmer ist **AbsenceType (`0-14`)**, das zusätzlich eine für Menschen gedachte `description`
bekommen hat. `search-model` blendet für solche Modelltypen beide Spalten automatisch ein, und
`get-model-schema` hängt an Beziehungsfelder, deren Zielmodell den Trait nutzt (heute:
`absence_type_id` im Create-/Update-Schema von AbsencePeriod `0-13`), einen Hinweissatz an.
AbsenceType bleibt schreibgeschützt — die beiden Felder sind über MCP nur lesbar.

Das ist deshalb mehr als Kosmetik, weil **mehrere Abwesenheitsarten sich einen `key` teilen** und
das Label allein nicht auseinanderhält, was arbeitsrechtlich verschieden ist: *Beschäftigungsverbot
(generell)* (behördlich/Arbeitgeber, §§ 11/12 MuSchG, § 31 IfSG, kein Attest) gegen
*Beschäftigungsverbot (individuell)* (§ 16 MuSchG, Attest zwingend), und *Krank bei Eintritt
(Wartezeit, § 3 Abs. 3 EFZG)* gegen die reguläre Krankmeldung. Genau diese Zeilen sind mit
Beschreibung und Anweisung befüllt ausgeliefert worden.

- **record-absence** — Schritt 1 liest die Katalogzeile jetzt vollständig statt nur `label` und
  `requires_immediate_call`: `ai_instructions` ist bindend und schlägt die eigene Lesart des Labels,
  `description` geht an den Operator. Dazu die Falle, die man sonst erst im Betrieb bemerkt —
  **die beiden Spalten erscheinen nur, wenn kein `fields`-Parameter gesetzt ist**; wer `fields`
  mitgibt, muss sie ausdrücklich aufführen, sonst wählt er blind. Die drei Verwechslungspaare stehen
  ausgeschrieben da, samt der Ansage, bei fehlendem Attest-Hinweis nachzufragen statt die
  individuelle Variante zu raten. Ist keine der Spalten gefüllt, wird nach `label`, `key`,
  `medical_certificate_requirement` und Operatorwortlaut entschieden — und offengelegt, woraufhin.
  Die Vorschau in Schritt 5 nennt die Art jetzt mit Label **und** Beschreibung, weil der Operator
  eine Abwesenheitsart bestätigt und keine ID. Gepflegt werden beide Felder in der Oberfläche unter
  *Einstellungen → Abwesenheitsarten*.

Kein anderer Skill spricht den Abwesenheitskatalog an; ausgeliefert wird genau eine Datei.

### Changed — 2026-08-29 `commission_as_agreed`: Wer beauftragt hat ≠ wer die Auftragsbestätigung bekommt (alluvo#4438)

`manage-assignment-contract action=commission_as_agreed` behandelt `contact_id` nicht mehr als
beides zugleich. **`contact_id`** beantwortet jetzt nur noch *wer beauftragt hat* — die Person wird
als Unterzeichner des Vertrags festgeschrieben (`signer_full_name` / `signer_email`) und in den
Signaturblock der AÜV-Dokumente gerendert. **`recipient_contact_ids`** ist neu auf dieser Action
und beantwortet *wer die Auftragsbestätigung bekommt*: TO ist der Hauptempfänger des Vertrags,
sofern er unter den Genannten ist, sonst der erste Genannte; der Rest geht in CC. Die Liste ist
**additiv** — wer noch kein Empfänger ist, wird dauerhaft angehängt, und kein bestehender Empfänger
wird je entfernt.

Der teure Teil ist das Weglassen: **ohne `recipient_contact_ids` geht die Mail an den
beauftragenden `contact_id` allein** — sie fällt ausdrücklich *nicht* auf die bestehenden Empfänger
des Vertrags zurück. Auf einem AÜV, der längst an den Einkauf zur Unterschrift ging, schickt eine
Beauftragung gegen den Geschäftsführer, der telefonisch zugesagt hat, die Unterlagen also
ausschließlich an den Geschäftsführer. Genau die Zeile im Ablauf-Skill behauptete bisher das
Gegenteil („unchanged — the contract's recipients … are resolved automatically"), und das ist eine
Aussage, die ein Operator ungeprüft an den Kunden weitergibt.

`manage-contract-lifecycle` stellt die beiden Fragen deshalb jetzt getrennt (*wer hat beauftragt* /
*wer soll die Auftragsbestätigung bekommen*), nennt die Verlinkungs-Regel für beide Eingaben, weist
darauf hin, dass ein neu genannter Empfänger dauerhaft angehängt wird und damit auch eine
Portal-Zugangs-Entscheidung ist, und benennt die neuen Preview-Zeilen — `**Commissioned by:**` und
`**Auftragsbestätigung to:**` (Erfolg: `**Order confirmation sent to:**`) statt des weggefallenen
`Confirming Contact:`. Ergänzt ist außerdem, dass auf diesem Weg der eingefrorene Unterzeichner die
beauftragende Person ist und nicht der Hauptempfänger — Person A im Signaturblock und Person B im
Postfach ist seit der Trennung ein korrekter Zustand, kein Fehler.

### Changed — 2026-08-28 Persönliche KI-Anweisungen sind ein eigener Baustein am Agenten (alluvo#4440)

Die persönliche Anweisung ist keine Spalte auf `users` mehr, sondern ein **user-owned
`InstructionBlock`**, der an **genau einen Agent** hängt — und die firmenweite Anweisung ist
ebenfalls ein ganz normaler Baustein am `activity-takeover`-Agenten. Damit verschiebt sich die
MCP-Oberfläche an vier Stellen, und zwei davon waren in den Skills als Tatsache dokumentiert.

- **build-automation-agent** — `ai_takeover.instruction_snippet` **existiert nicht mehr** (weder
  in der Allowlist noch im Feld-Katalog); ein `update` damit wird als „Unknown field(s)"
  abgelehnt. Der Satz über die drei additiven Ebenen nennt es folglich nicht mehr, und der
  Abschnitt zu den beiden settings-gestützten Blöcken hält jetzt ausdrücklich fest, dass in der
  Gruppe `ai_takeover` **kein** Freitextfeld mehr steckt. Neu dokumentiert: `manage-automation-agent`
  meldet unter `instruction_block_ids` nur noch **tenant-owned** Blöcke und trägt beim `update`
  jede angehängte persönliche Anweisung unverändert nach — der übliche `get` → ändern → `update`
  hängt also niemandem mehr die eigenen Anweisungen ab (umgekehrt kann man sie von hier auch nicht
  lösen). Bei `manage-agent-prompt` gilt dasselbe für `attach-baustein` / `detach-baustein` /
  `reorder-bausteine`: eine user-owned ID verhält sich wie „nicht gefunden", damit der Assistent
  weder fremden Privattext für alle sichtbar anhängt noch jemandem seine Anweisungen abhängt. Ganz
  neu ist der Abschnitt *Personal instructions* zu **`manage-ai-preferences`** — optionaler
  Parameter `agent` (agent_key oder Row-ID, Default `activity-takeover`, jeder bestehende Aufruf
  bleibt gültig), leerer String **löscht**, ein Agent ohne persönliche Anweisungen wird namentlich
  abgelehnt, und `list` bedeutet jetzt „jede persönliche Anweisung an **diesem** Agenten" statt
  „jeder Tenant-User" — die dort gemeldete User ID ist nicht die, die andere Werkzeuge für
  Tenant-Nutzer nennen. Eigene Anweisung braucht keine Berechtigung, fremde und `list` brauchen
  `settings.manage`. Die Terms-Tabelle trennt Baustein (tenant-weit, geteilt) und persönliche
  Anweisung (privat) sauber, und die `description` triggert auf die neuen Formulierungen.
- **using-alluvo-operator** — `instruction_snippet` ist aus der Ebenen-Aufzählung raus (die
  Aussage selbst stimmt weiter: keine additive Ebene sticht die Rückruf-/Zuständigkeitsregeln
  aus). Die Baustein-Zeile sagt jetzt dazu, dass die Aktionen von `manage-agent-prompt`
  tenant-only sind, und eine neue Routing-Zeile führt „meine persönliche Anweisung für die KI /
  persönliche Anweisung eines Kollegen / wer hat eigene Anweisungen hinterlegt" nach
  `manage-ai-preferences` — mit dem Hinweis, dass „firmenweit" stattdessen ein Baustein ist.
- **call-summary** unverändert: die dort genannten Felder (`callback_*`,
  `task_routing_instructions`) liegen weiterhin in `manage-settings` group `ai_takeover`.

### Changed — 2026-08-29 Ticket-Lebenszyklus schreibt ins Gmail-Postfach zurück, `mark_as_spam` ist entweder/oder (alluvo#4444)

Das Postfach ist jetzt ein Spiegel des Vorgangs: Schließen **archiviert** den Gmail-Thread
(Wiedereröffnen hebt das auf), Löschen legt ihn in den **Papierkorb** (Wiederherstellen holt
ihn zurück), und `mark_as_spam: true` meldet ihn **statt** ihn zu löschen — beides zusammen
feuert nie, weil ein Thread im Papierkorb den Spamfilter nichts lehrt. Bisher fasste ein
Löschen Gmail überhaupt nicht an.

- **clean-inbox** — neuer Abschnitt *The Gmail mailbox mirrors the ticket* mit der Tabelle
  Ticket-Aktion → Thread-Wirkung (archive / unarchive / trash / untrash) und den vier Punkten,
  die dabei zählen: nur Gmail-Tickets (WhatsApp, Web-Chat und Telefon werden wie bisher ohne
  Postfach-Schreibzugriff gelöscht), der Schreibzugriff ist **eingereiht, nicht synchron** —
  also den Gmail-Zustand danach nicht auslesen und berichten, sondern sagen, was eingereiht
  wurde —, die Mandanten-Schalter liegen unter **Einstellungen → Posteingang → Kanäle →
  „Postfach spiegeln"** und sind über `manage-settings` **nicht** erreichbar (die Gruppe
  `inbox_sync` steht nicht in dessen Gruppenliste), und die Spam-Meldung ignoriert diese
  Schalter bewusst, weil sie eine ausdrückliche Anweisung ist und keine automatische
  Spiegelung. Der Checkpoint in Schritt 5 deckt jetzt auch `delete` / `bulk_delete` ab: beide
  haben **keinen** Preview-Parameter und keine Begründung, also wird vorher benannt, welche
  Tickets es trifft und ob der Thread in den Papierkorb wandert oder als Spam gemeldet wird.
  Der Cluster *Newsletter / Werbung* nennt `bulk_delete` mit `mark_as_spam: true` als den
  stärkeren Zug bei **unverlangter** Post — ein einmal abonnierter Newsletter ist kein Spam.
  Der Purpose-Absatz sagt entsprechend nicht mehr pauschal „nichts wird gelöscht", sondern
  „ein echter Vorgang wird nie gelöscht".
- **build-automation-agent** — beim Schritt `close_ticket` steht jetzt, dass ein genehmigter
  Abschluss auf einer Gmail-Inbox den Mail-Thread mit archiviert (und ein Wiedereröffnen das
  zurücknimmt).
- **using-alluvo-operator** — neuer Routing-Eintrag „Ticket löschen / als Spam melden / den
  Newsletter-Absender loswerden" → `clean-inbox`, samt der Entweder-oder-Regel und dem
  Hinweis, dass weder `delete` noch `bulk_delete` eine Vorschau kennen.
### Changed — 2026-08-28 Stundenfreigabe: Split mitten in der Periode, Tages-Rebuild, Abweichungs-Null, Zurückziehen-Guard (alluvo#4450)

Vier Änderungen am Stundenfreigabe-Flow. Kein MCP-Tool, kein Parameter und kein Schema hat sich
bewegt — aber drei davon ändern, was ein Skill über eine Periode, einen Tag und den Tagesabschluss
behaupten darf.

- **approve-stundenfreigabe** — *„Offene Tage in die Folgeperiode schieben"* ist keine
  Nachzügler-Aktion mehr. Das Readiness-Gate („die Periode muss vorbei sein", Absage *„Diese
  Periode wird noch gearbeitet …"*) ist ersatzlos weg: die Aktion erscheint, sobald **ein** Tag
  freigegeben ist, also auch mitten in der laufenden Periode — offene Tage mit geplanten künftigen
  Diensten wandern einfach mit. Der Abschnitt heißt jetzt entsprechend *Splitting a period so the
  signed days can be billed*, nennt als Status-Gate „noch offen" statt `PendingClient` (mit der
  Absage, die die Aktion tatsächlich ausgibt) und ersetzt die falsche Folgeperioden-Bedingung: die
  Folgeperiode blockiert nicht mehr, sie entscheidet nur noch zwischen **Merge** (zusammenhängend,
  noch offen, noch nicht vorgelegt, bleibt im Monat) und **Split** (alles andere, Folgeperiode wird
  nicht angefasst) — und keine der beiden Varianten überschreitet je eine Monatsgrenze.
- **approve-stundenfreigabe** — neu: *Tracked time and the Tagesabschluss rebuild the period too*.
  Ein `TimesheetDay` wurde bisher einmal beim Anlegen geschrieben; geheilt hat die Periode nur,
  wenn jemand die Mitarbeiter-Stundenfreigabe öffnete. Jetzt stößt jeder Ist-Schreiber
  (Mitarbeiter-App, zvoove-Import, Operator-Korrektur, generischer `manage-model`-Write auf `0-6`)
  und jeder Tagesabschluss/Neuabschluss/Zurückziehen denselben Rebuild an. Jeder
  „warte, bis der Mitarbeiter die Freigabe öffnet"-Workaround ist damit obsolet — mit den drei
  Fußnoten, die dranhängen: der Rebuild ist **queued**, er fasst nur offene Perioden an und
  überspringt jeden kundenunterschriebenen Tag, und auf einem unfreigegebenen Tag leitet er
  `agreed_*` neu aus der Erfassung ab (eine Korrektur dort ist also nicht dauerhaft). Dieselbe
  Zusage steht jetzt auch bei `close_tracked_day_for_employee`.
- **approve-stundenfreigabe** — neu bei `0-427`: eine gespeicherte `deviation_minutes: 0` ist
  nicht immer ein Urteil. Für einen *entschuldigten* Tag (geplantes Ende noch nicht vorbei, oder
  Abwesenheit) schreibt der Builder `0`/`none`, und die **Tage**-Karte rendert das nicht mehr als
  grünes ✓ „Keine Abweichung", sondern als Strich, sobald der Tag kein bindendes Ist hat. Geändert
  hat sich nur das Karten-Payload — `query-model` auf `0-427` und der Tätigkeitsnachweis lesen
  weiterhin `0`, also nie „keine Abweichung" aus einer Null melden, ohne zu prüfen, ob der Tag
  überhaupt fällig ist.
- **approve-stundenfreigabe** — das Zurückziehen des Tagesabschlusses ist enger: gesperrt ist es
  jetzt nicht nur, wenn der **Kunde** den Tag unterschrieben hat, sondern auch, wenn ein Operator
  ihn in der Stundenkontrolle freigegeben hat (`operator_approved_at`) oder der Zeitraum die
  offenen Status verlassen hat (`PendingEmployee`, Klärung, freigegeben, abgerechnet) — Absage
  *„Dieser Tag wurde bereits freigegeben …"*. Der Satz „der Status der Periode spielt keine Rolle"
  war damit falsch und ist ersetzt; was bleibt: eine offene Periode beim Kunden blockiert das
  Zurückziehen **nicht**.
- **using-alluvo-operator** — der Navigator-Eintrag zu `push_open_days_to_next_period` nennt die
  neuen Bedingungen (offener Zeitraum, ein freigegebener Tag, zusammenhängendes Ende, auch mitten
  in der Periode; Folgeperiode entscheidet nur die Form), und der Tagesabschluss-Eintrag hält
  fest, dass auch der Mitarbeiter nicht mehr zurückziehen kann, sobald ein Operator freigegeben
  hat oder der Zeitraum weiter ist.

### Changed — 2026-08-27 Tätigkeitsnachweis: § 17c-Kasten entfällt, Verleiher-Hinweis rückt unter die Unterschrift (alluvo#4401)

Das PDF hat seine Form geändert (alluvo#4400), ohne dass ein MCP-Werkzeug, ein Parameter, ein
Enum-Wert oder ein Gate sich bewegt hätte — die Skills beschrieben das Dokument aber so genau, dass
drei Stellen jetzt falsch waren, und zwei davon sind Sätze, die ein Operator einem Kunden
weitererzählt. **Der § 17c-Bestätigungskasten zwischen Tabelle und Unterschriften ist entfallen:** er
wiederholte Untertitel, Mitarbeiter/in, Entleiher und Zeitraum, die alle schon im Seitenkopf und im
Metablock stehen. Seine einzige eigene Aussage — dass bei einer Freigabe durch den Verleiher **keine**
Bestätigung des Entleihers vorliegt — steht jetzt als Zeile **unter** „Datum, Freigabe durch den
Verleiher", also unter der Zeile, auf die sie sich bezieht. Der Metablock läuft außerdem
**zweispaltig**, und die AÜV-Nummer sitzt dort statt im Seitenkopf.

- **approve-stundenfreigabe** — „What the Tätigkeitsnachweis actually puts in front of the client"
  nennt jetzt die tatsächliche Reihenfolge der Seite und hält ausdrücklich fest, dass zwischen
  Tabelle und Unterschriften **nichts** mehr steht: wer einen Operator an „den Absatz über den
  Unterschriften" schickt, schickt ihn ins Leere. *Kopf* beschreibt fünf statt vier Fakten und die
  Zweispaltigkeit (Mitarbeiter/in · Entleiher · Einsatzort links, Abteilung · AÜV rechts) — „unter
  Entleiher" ist die falsche Ansage, die beiden stehen rechts daneben. *Seitenkopf* trägt den
  Dokumenttitel, den Namen und den Zeitraum, **nicht** die AÜV-Nummer; der Satz „die AÜV-Nummer steht
  ausschließlich im Seitenkopf" ist umgedreht. Die Klausel „der § 17c-Satz unter der Tabelle nennt
  denselben Zeitraum" ist raus — der Zeitraum steht jetzt nur noch im Seitenkopf, was den Punkt
  darüber (gedruckt wird der erste und letzte **tatsächlich gearbeitete** Tag, nie die
  Vertragslaufzeit) eher stärkt. Die Tabelle der Unterschrifts-Zusätze hat eine Zeile für
  `operator_release` bekommen; der Warnhinweis zur Operator-Freigabe verweist auf die
  Unterschriftenzeile statt auf den Kasten.
- **using-alluvo-operator** — Die Navigationsantwort auf „wo finde ich die AÜV-Nummer" zeigte auf den
  Seitenkopf und zeigt jetzt auf den zweispaltigen Metablock; die Liste der Unterschrifts-Zusätze
  kennt den Verleiher-Fall; und die Einordnung der Verleiher-Freigabe sagt, **wo** auf dem Dokument
  die fehlende Kundenbestätigung festgehalten wird.

Keine Änderung an Werkzeugaufrufen: `timesheets.approve_by_operator`, der zweistufige
Bestätigungsvertrag, die Freigaben-Tabelle und die Layout-Einstellungen für leere Tage und
Abwesenheitstage sind unberührt.

### Changed — 2026-08-26 Ein Zeitraum ist jetzt vom Operator freigebbar und zurücknehmbar (alluvo#4379)

Der Stundennachweis-Zeitraum (`0-426`) trägt zwei neue, operator-eigene Aktionen über
`manage-record-action`. **`approve_by_operator`** („Ohne Kunden freigeben") gibt einen Zeitraum
stellvertretend für den Kunden frei — für den Kunden, der nicht unterschreibt, obwohl die Stunden
abgestimmt sind. **`revoke_approval`** („Freigabe zurücknehmen") nimmt die Freigabe eines bereits
freigegebenen Zeitraums zurück — der Fall, für den es gebaut wurde, ist die falsche unterschreibende
Person. Damit ist `Approved` kein Endzustand mehr, und die alte Aussage „es gibt kein MCP-Werkzeug,
das einen Stundenzettel freigibt" ist überholt.

- **approve-stundenfreigabe** — Der `## Limitation`-Block ist ersetzt durch „What MCP reaches — and
  what it still does not": drei Schreib-Aktionen statt einer, plus eine Tabelle gegen die
  Namenskollision (`revoke_approval` auf der Woche vs. `revoke_release` auf dem Tag tragen **dieselbe**
  deutsche Bezeichnung „Freigabe zurücknehmen", `approve_by_operator` heißt „Ohne Kunden freigeben").
  Neuer Abschnitt „Releasing and un-releasing the whole period" mit beiden Aufrufen, ihren
  Statusfenstern, Rechten (`timesheets.approve_by_operator` / `timesheets.revoke_approval`, per
  Default keiner Rolle zugewiesen) und Wirkungen. Zwei Punkte ausdrücklich benannt:
  `approve_by_operator` verlangt, dass **jeder** Tag freigebbar ist, und nennt bei Absage die
  blockierenden Tage samt Grund (`2026-05-27 (not_closed)`) — das ist die Ansage, welchen
  Tagesabschluss man nachhält; und es landet **nicht immer** auf `Approved`: bei Abweichung zwischen
  vereinbarter und erfasster Zeit geht der Zeitraum nach `PendingEmployee`, der Status ist also
  zurückzulesen, bevor „freigegeben" gemeldet wird. Dazu, dass der Kanal `operator_release`
  ausdrücklich **keine** Kundenbestätigung ist: der Tätigkeitsnachweis hält § 11 AÜG-konform fest,
  dass keine Bestätigung des Entleihers vorliegt, und zeichnet Mandant plus handelnden Nutzer statt
  einer Kundenunterschrift. Schritt 4 führt jetzt zuerst den regulären Weg (Kundenunterschrift,
  Frist) und die Operator-Freigabe als Ausnahme; `revoke_release` verweist für einen `Approved`
  Zeitraum auf `revoke_approval`. Neue Trigger für beide Fälle.
- **using-alluvo-operator** — „Nichts an einem Zeitraum ist schreibbar" stimmte nicht mehr: die
  Einordnung nennt jetzt beide Zeitraum-Aktionen, die Statusfenster, die doppelte deutsche
  Bezeichnung und die `PendingEmployee`-Falle, und hält fest, dass eine Verleiher-Freigabe nie als
  „der Kunde hat freigegeben" berichtet wird.
- **head-of-disposition** — Die Backlog-Notiz sagt „nicht schreibbar" jetzt nur noch über
  `manage-model`, und ein neuer Hinweis grenzt die beiden Aktionen als Delegations-, nicht als
  Backlog-Werkzeug ab: ein Backlog, der schrumpft, weil jemand ohne den Kunden freigegeben hat, ist
  kein abgearbeiteter Backlog — dazu die beiden Zahlenfallen (Tagesabschluss zuerst,
  `PendingEmployee` bei Abweichung).

### Changed — 2026-08-26 Abrechnungszeiträume entstehen nur noch mit Substanz und ab Go-Live (alluvo#4369)

Ob ein Stundenfreigabe-Zeitraum überhaupt **existiert**, entscheidet jetzt der Materialisierer,
nicht mehr erst die Anzeige. Zwei Erzeugungs-Gates sind dazugekommen: ein Zeitraum wird nur
angelegt, wenn er eine **wirksame Schicht oder einen abgeschlossenen Zeiteintrag** enthält, und
**nichts vor dem Go-Live des Mitarbeiters** wird noch materialisiert — Letzteres gilt nun für
alle schreibenden Pfade, nicht mehr nur für die Mitarbeiter-Liste. Ein toter Einsatz (storniert,
nie unterschrieben, `end_date` hat den Storno überlebt) meldet damit keine leeren Wochen mehr,
und Lücken in den Wochen eines Mitarbeiters sind eine Antwort statt eines Datenfehlers. Beide
Gates greifen nur beim **Anlegen** — ein bereits unterschriebener, freigegebener oder
abgerechneter Zeitraum bleibt unberührt.

- **approve-stundenfreigabe** — „Which periods the employee actually sees" trennt jetzt zwei
  Ebenen: welche Zeiträume überhaupt materialisiert werden (Einsatz-Clamp, Substanz, Go-Live-Boden)
  und welche der vorhandenen dem Mitarbeiter zur Freigabe angeboten werden (Ist > 0 oder
  `agreed` > 0). Neu benannt ist die Asymmetrie — eine reine Dienstplan-Woche **hat** einen
  Datensatz mit Soll und Frist, ist aber nicht freigebbar. „Kein Zeitraum" ist ausdrücklich als
  gültige Antwort („nichts abzurechnen") ausgewiesen, nicht als Eskalationsgrund; dazu der
  Hinweis, dass ein Zeitraum abgeleitet ist und von selbst zurückkommt. Der Absatz „Your MCP
  figures do not see the cutoff" war für Zeiträume falsch geworden und ist aufgeteilt: `0-426`
  stimmt jetzt mit der Mitarbeiter-Sicht überein (vor-Go-Live-Zeiträume wurden einmalig entfernt,
  unterschriebene nie), während `TimeEntry`, Einsatzmitteilungen und AUs den Zeitraum davor
  weiterhin mitzählen. Neue Trigger für „Zeitraum fehlt / Lücke in den Wochen".
- **head-of-disposition** — Die Backlog-Regeln in 1e stimmen wieder: der laufende Zeitraum ist
  nur materialisiert, wenn er Substanz hat; leere Zeiträume sind nicht bloß unsichtbar, sondern
  gar nicht erst vorhanden; und die Go-Live-Warnung („deine Zahl sieht den Schnitt nicht") gilt
  nur noch für die Stunden darunter, nicht mehr für die `0-426`-Zählung. Dazu, wie man über
  Stunden vor dem Go-Live berichtet: alluvo hält die Zeiträume ab Go-Live, davor lag das
  Vorsystem (zvoove/Landwehr).
- **onboard-new-employee** — Schritt 6 unterscheidet jetzt beim Setzen des Go-Live-Datums
  zwischen „Zeiträume entstehen nicht mehr" (und fallen damit auch aus den eigenen Zählungen)
  und „Einsatzmitteilungen/AUs werden nur ausgeblendet". Die Zusage „kein Datensatz wird
  angefasst" ist auf das Belastbare zurückgeführt: nichts wird in jemandes Namen unterschrieben,
  und Unterschriebenes/Abgerechnetes wird nie entfernt.
- **using-alluvo-operator** — Die Go-Live-Routing-Zeile nennt den Unterschied zwischen „gar nicht
  angelegt" und „nur ausgeblendet"; neue Routing-Zeile für „Der Zeitraum fehlt komplett / Lücke
  in den Wochen".
### Added — 2026-08-26 Operator-seitiger Tagesabschluss: `close_tracked_day_for_employee` auf `0-427` (alluvo#4362)

„Tag abschließen" (Feierabend) gab es bisher **nur** in der Mitarbeiter-App, die den Mitarbeiter
aus dem eingeloggten Benutzer auflöst und deshalb nie für jemand anderen handeln konnte. Ein
erfasster, aber nie abgeschlossener Tag blockierte damit die ganze Stundenfreigabe-Woche, ohne
dass die Disposition einen Weg heraus hatte. `TimesheetDay` (`0-427`) trägt jetzt die
MCP-ausführbare Record-Aktion **`close_tracked_day_for_employee`**, erreichbar über
`manage-record-action`.

- **approve-stundenfreigabe** — Neuer Abschnitt „Closing a day for the employee —
  `close_tracked_day_for_employee` on `TimesheetDay` (`0-427`)": zweistufige Aufrufform mit
  `record_id`, warum `operation: "list"` **vor** dem Schreiben steht (die Aktion fragt nur die
  Felder ab, die *dieser* Tag wirklich braucht — auf einem sauberen Tag gar keine), die
  unveränderten Prüfungen (§ 4 ArbZG: `no_break_reason` plus `is_one_off` /
  `support_requested` / `prevention_measures`; Abweichung: `deviation_reason_code` **und**
  `deviation_reason`, ≥ 10 Zeichen, richtungsgeprüft aus dem Mandantenkatalog), die benannten
  Ablehnungsgründe (bereits abgeschlossen, laufender Timer, nichts erfasst, Zukunftstag,
  fehlende Berechtigung), die Berechtigung `timesheet_days.close_tracked_day` (per Default an
  keine Rolle vergeben), die deklarierten Effekte (Abschluss, Benachrichtigung der
  Einsatzverantwortlichen bei Pausenverstoß, Aufgabe bei `support_requested`) und die
  `closed_by_operator`-Stempelung. Ausdrücklich: **keine Lockerung** — die Aktion delegiert an
  denselben Mitarbeiter-Abschluss, statt die Prüfungen zu kopieren; nie einen Grund erfinden,
  um ein Gate zu räumen; und wenn der Mitarbeiter selbst abschließen kann, soll er das tun.
- **approve-stundenfreigabe** — **Korrektur:** Der Abweichungsgrund-Abschnitt behauptete, der
  Tagesabschluss sei „an employee-app act only; there is no MCP write for it". Das stimmt so
  nicht mehr. Ebenso präzisiert: `TimeTrackingDayClosure` (`0-422`) bleibt von der
  MCP-Allowlist ausgenommen (kein Lesen, kein Zurückziehen) — angelegt wird eine Closure
  jetzt aber über die Aktion am *Tag*.
- **approve-stundenfreigabe** — Neuer Punkt unter „Changing a closed day": das **Zurückziehen**
  eines Abschlusses hat weiterhin keinen Operator-Weg (nicht auf `0-427`), die Asymmetrie ist
  gewollt. Einem Operator nie zusagen, einen Tagesabschluss rückgängig machen zu können.
- **approve-stundenfreigabe** — **Korrektur:** Das `revoke_release`-Beispiel benutzte
  `model_id`; bei `manage-record-action` heißt der Parameter `record_id`.
- **using-alluvo-operator** — Der Stundenfreigabe-Wegweiser routet „der Mitarbeiter hat den Tag
  nie abgeschlossen / Tag stellvertretend abschließen" jetzt auf die neue Aktion und sagt
  dazu, dass das Zurückziehen Mitarbeiter-App bleibt. Der Satz „die eine per MCP ausführbare
  Schreib-Aktion ist `revoke_release`" ist entsprechend eingegrenzt.
- **head-of-disposition** — „A period stuck in `Upcoming` is often one unclosed day": nennt den
  stellvertretenden Abschluss als **Ausnahmeweg**, wenn der Mitarbeiter nachweislich nicht
  selbst kann — nicht als Standardantwort auf einen langsamen Mitarbeiter.
### Changed — 2026-08-26 Workflow-Trigger: Aktions-Trigger auf Abwesenheiten, und der Auslöser hat wieder einen Namen (alluvo#4370)

Zwei Aussagen in den Skills waren nicht mehr wahr. Erstens: `action_performed` war als
„noch nicht nutzbar" dokumentiert, weil keine Aktion in der API dafür freigegeben war — jetzt
sind es **sechs**, alle auf AbsencePeriod (`0-13`). Zweitens: `{{trigger.actor_name}}` galt als
leer, sobald ein Lauf über die Queue ging. Der Auslöser wird inzwischen beim Anlegen der
Enrollment festgehalten und wandert mit ihr mit, ist also auch nach Tagen Wartezeit noch da —
leer ist er nur noch, wenn wirklich niemand geklickt hat.

- **build-automation-agent** — Die Warnung „`action_performed` ist noch nicht nutzbar" ist durch
  die tatsächliche Lage ersetzt: legal auf AbsencePeriod (`0-13`) mit den Schlüsseln `submit`,
  `approve`, `reject`, `request-revision`, `cancel`, `reset-to-draft`; überall sonst leer und
  abgelehnt, wobei die Fehlermeldung die legalen Schlüssel nennt (kein MCP-Call listet das Flag,
  `manage-record-action` `list` zeigt es nicht). Die `{{trigger.*}}`-Liste hat `actor_id` und
  `action` dazubekommen, und die Leer-Regel für `actor_name` ist korrigiert — ein Slack-Klick,
  eine Kundenportal-Aktion und die Mitarbeiter-App benennen den Menschen dahinter sehr wohl.
  Die Herkunftszeile nennt auf einem Aktions-Trigger zusätzlich die Aktion
  (`Aktion „Genehmigen" ausgeführt von …`) — das Einzige im Post, das Genehmigung von Ablehnung
  unterscheidet. Dazu neu benannt: Slack-Buttons und Workflow-Trigger sind **zwei verschiedene**
  Flags — Buttons gibt es weiterhin nur für `approve`/`reject`.
- **record-absence** — Neuer Abschnitt „Automatisieren rund um eine Abwesenheit": der
  Aktions-Trigger auf `0-13` (der einzige Ort, an dem er überhaupt funktioniert) und die
  Herkunft. Eine in der **Mitarbeiter-App** eingereichte Abwesenheit trägt jetzt
  `record_source = external_panel` statt `manual` — für „nur Selbstmeldungen aus der App" ist das
  die Bedingung; jeder andere Weg (Backend, MCP, Web-Mitarbeiterportal) schreibt weiterhin
  `manual`.
- **using-alluvo-operator** — Neuer Router-Eintrag „Slack-Meldung/Aufgabe, wenn eine Abwesenheit
  eingereicht/genehmigt/abgelehnt wird" → `build-automation-agent` mit Aktions-Trigger.
### Added — 2026-08-26 Sammel-Reisekostenabrechnung: eine Index-Action auf `0-20` (alluvo#4321)

`Reimbursement` (`0-20`) hat eine **Index-Action** bekommen: `generate-period-statements`
("Sammelabrechnung erzeugen"). Sie fasst zu einem `cutoff_date` alle genehmigten oder
ausgezahlten Erstattungen pro Mitarbeiter zu einer PDF-Reisekostenabrechnung zusammen, legt
diese als `EmployeeDocument` vom neuen Typ `reimbursement_period_statement` in der Personalakte
ab und mailt den Lauf als ZIP an die in den Einstellungen hinterlegten Empfänger. Sie läuft
asynchron, hängt am Pennant-Flag `ReimbursementPeriodStatements` (standardmäßig **aus**) und
wird über `operation: "execute_index"` aufgerufen — nicht über `execute`.

- **approve-stundenfreigabe** — Neuer Abschnitt „Sammel-Reisekostenabrechnung — one statement
  PDF per employee (index action)": Aufrufform, warum die Vorschau bei einer Index-Action kein
  Dry-Run ist (`cutoff_date` wird dort noch nicht geprüft), die Auswahlregeln
  (`approved`/`paid`, noch nicht gebatcht, **Leistungsdatum** ≤ Stichtag — kein
  `created_at`-Fenster, ein spät erfasster Beleg fällt also nicht heraus), die Idempotenz über
  `statement_batch_id` (ein zweiter Lauf ist gefahrlos — nicht davon abraten), das abgelegte
  Dokument (GoBD, 10 Jahre, **HrOnly** — der Mitarbeiter sieht es nicht), die zehn festen
  Formularzeilen (`ReimbursementStatementPosition`, ausdrücklich **nicht** die Belegkategorien)
  und der Zustellweg. Dazu der genaue Fehlertext, wenn das Flag aus **oder** die Berechtigung
  `reimbursements.export` fehlt — eine Meldung für beide Fälle, also nicht als „Berechtigung
  fehlt" diagnostizieren. Ebenso: fehlt die Aktion in `operation: "list"`, ist das kein Beleg
  dafür, dass es sie nicht gibt.
- **approve-stundenfreigabe** — Die Aufzählung der `0-20`-Lifecycle-Aktionen sagt jetzt, dass
  das die **Record**-Aktionen sind und `0-20` daneben diese eine Index-Action trägt.
- **approve-stundenfreigabe** — **Korrektur:** Der Wegstreckenpauschalen-Abschnitt behauptete,
  der mandantenweite Schalter und der Standardsatz hätten „No MCP surface at all". Beide sind
  über `manage-settings` Gruppe `reimbursements` les- und schreibbar
  (`commute_allowance_enabled`, `commute_allowance_rate_cents`), zusammen mit
  `default_payout_method`, `employee_requestable`, `car_km_rate_cents`,
  `commute_allowance_wage_type_id` und den beiden neuen Schlüsseln
  `statement_recipient_emails` / `statement_show_empty_positions`. Ein leeres
  `statement_recipient_emails` ist **kein Fehler**: der Lauf legt die Dokumente trotzdem ab,
  nur die Mail nach außen entfällt. Nur die *berechnete* Monatssumme bleibt ohne MCP-Surface.
- **using-alluvo-operator** — Neuer Routing-Eintrag für „Sammelabrechnung erzeugen / Reisekosten
  an die Lohnbuchhaltung schicken" und ein erweiterter Skill-Index-Eintrag.

**Nicht geändert:** Die neue Belegkategorie `training` („Fortbildung") und der neue
`ExportKind` werden von keinem Skill aufgezählt — die Skills lesen Kategorien und Dokumenttypen
konsequent über `manage-employee-document` `action: "list-types"` bzw. die Schema-Tools statt
sie hart zu hinterlegen, es gab also nichts zu korrigieren.
### Added — 2026-08-26 Rückrufzeiten und Aufgaben-Zuständigkeiten der KI-Nachbearbeitung sind Tenant-Einstellungen (alluvo#4312)

Die Settings-Gruppe `ai_takeover` hat drei neue schreibbare Felder —
`callback_same_day_cutoff_hour` (int, 0–23, Default 16), `callback_retry_after_hours`
(int, 1–12, Default 3) und `task_routing_instructions` (string|null, ≤ 2000 Zeichen). Sie
rendern die beiden neuen Bausteine `callback-timing` (nicht abwählbar) und `task-routing`
(abwählbar) auf `call-action-classifier` und `inbound-email-classifier`. Anders als
`instruction_snippet`, `set-instructions` oder ein Baustein sind sie **nicht additiv**: sie
*sind* die Regel des Klassifikators. Bestehende Aufrufe brechen nicht — die Defaults
reproduzieren exakt die bisher hartverdrahteten Werte.

- **build-automation-agent** — Der `set-blocks`-Absatz sagt jetzt, dass die Block-Schlüssel
  **pro Agent** deklariert werden (die vier Namen im Tool-Text sind der Conversational-Satz)
  und dass eine nie konfigurierte Auswahl (`null`) bei einem Code-Agenten *alle* deklarierten
  Blöcke einschaltet statt keinen. Neuer Abschnitt „The call-notes classifiers' two
  settings-backed blocks" beschreibt beide Blöcke, ihre Felder, warum ein leeres
  `task_routing_instructions` eine gültige Wahl ist, dass `callback-timing` nur umnummeriert
  und nie abgeschaltet werden kann, und dass `ai_takeover` zwar nicht `confirmed`-gated ist,
  der Live-Prompt aber trotzdem vorher gezeigt gehört.
- **call-summary** — Neuer Callout vor Schritt 4: was der „Recommended Follow-ups"-Block
  vorschlägt und was nicht — kein Rückruf bei dokumentiertem Desinteresse (der Text schlägt
  `outcome: "no_answer"`), keine Aufgabe, die nur festhält, was gerade geschrieben wurde
  (das ist eine `manage-model`-Änderung), und das `due_at` folgt den Tenant-Einstellungen
  statt einer festen Uhrzeit. Dazu `suggest_follow_ups: false` fürs Bulk-Logging und ein
  Querverweis auf `→ build-automation-agent`.
- **using-alluvo-operator** — Neuer Routing-Eintrag für „Rückrufzeiten ändern / wer ist wofür
  zuständig / die Aktionsvorschläge passen nicht" mit dem Hinweis, dass die additiven Ebenen
  diese Regeln nicht überschreiben können.

**Gemeldet (alluvo#4380):** `manage-agent-prompt` `get` und das Agent Studio leiten die
deklarierten Blöcke aus der *gespeicherten* Auswahl ab. Bei einem Task-Agenten ohne eigene
Auswahl — dem Normalfall — fehlen beide Abschnitte deshalb in der Vorschau, obwohl der echte
Lauf sie rendert. Bis dahin gilt `manage-settings(action: "get", group: "ai_takeover")` als
verlässliche Quelle; beide Skills sagen das.
### Changed — 2026-08-26 Outreach-Profilvorschau ist verlässlich — Handarbeits-Warnung entfällt (alluvo#4289)

Die Requirement-Vorauswahl beim Anlegen eines Enrollments und das Matching zur Draft-Zeit
benutzen jetzt beide dieselbe Filterung: Mitarbeiter mit laufendem Einsatz kommen gar nicht
erst in die Auswahl (`includeAssigned(false)` in `EnrollmentEmployeeIdsResolver` **und** im
Requirement-Zweig von `StaffingOutreachService`). Die Vorschau sagt damit exakt voraus, was
rausgeht. Tool- und Parameternamen bleiben unverändert.

- **enroll-outreach** — Die Warnung aus Schritt 4, der Requirement-Zweig könne einen bereits
  besetzten Mitarbeiter zeigen und der Operator müsse die Profile zurücklesen und aussortieren,
  ist **falsch geworden und ersetzt**: die Vorschau enthält nur verleihfreie Mitarbeiter und
  stimmt mit dem Versand überein. Neu festgehalten ist stattdessen die tatsächlich verbliebene
  Einschränkung: eine bereits auf dem Enrollment gespeicherte Profilliste (Zweig 1) ist zur
  `create`-Zeit eingefroren und wird von späteren Touchpoints unverändert gerendert — wer eine
  ältere Sequenz wiederbelebt oder verlängert, prüft die Liste, wer einen frischen Entwurf
  freigibt, nicht. Die übrige Dokumentation aus alluvo#4270 (Vier-Zweig-Präzedenz, `none` plus
  verknüpftes Requirement, Requirement-Enrollment sendet wieder) bleibt unverändert gültig.

Kein Skill beschrieb den ebenfalls behobenen Verlust des gepinnten Haupt-Mitarbeiters beim
Neuerzeugen der Entwürfe (alluvo#4218) — `recreateDrafts` ist über `manage-outreach-enrollment`
gar nicht erreichbar, daher gibt es dort nichts zu korrigieren.
### Changed — 2026-08-26 Erstattungs-Aktionen nennen den echten Blocker statt „falscher Status" (alluvo#4234)

Die Zustandsprüfung der Reimbursement-Aktionen lag bisher nur in der Policy, die der
`is_platform_admin`-Gate überspringt — auf einem Vorgang waren dadurch elf Aktionen
gleichzeitig verfügbar, von denen drei zulässig waren. Die Prüfung sitzt jetzt
berechtigungsunabhängig in den Aktionen selbst. Die Tool- und Parameternamen bleiben
identisch; was sich ändert, ist **welchen Grund** `manage-record-action` nennt, wenn eine
Aktion nicht verfügbar ist.

- **approve-stundenfreigabe** — Die Zustandstabelle im Abschnitt „reimbursement review" stimmte
  bereits; ergänzt ist, dass drei Aktionen jetzt einen **konkreten** Unavailable-Grund liefern
  statt des allgemeinen „falscher Status"-Textes: `confirm_authorization` /
  `decline_authorization` („wartet auf keine Freigabe"), `resolve_clarification` („keine offene
  Rückfrage") und `mark_as_paid` („nur eine genehmigte Erstattung"), jeweils mit DE- und
  EN-Wortlaut. Der bisherige Hinweis, der Zustandsblock lese sich *immer* als der eine generische
  Satz, war damit veraltet — die Anweisung lautet jetzt, den zurückgegebenen Grund zu zitieren
  statt auf einen festen String zu matchen. Neu festgehalten ist außerdem, dass bei diesen drei
  der **Zustand vor der Berechtigung** gemeldet wird (dieselbe Vorbedingung steht jetzt auch in
  der Policy), und dass ein Vorgang **ohne benannten Freigeber** kein `confirm_authorization` /
  `decline_authorization` kennt — `authorization_status` ist dort null, auch für Mandanten-Admins.
  Dort ist `approve` bzw. `reject` direkt der richtige Schritt.

### Added — 2026-08-26 Meta-Lead-Zuordnung ist jetzt vom Assistenten aus bedienbar (alluvo#4373)

Die Meta-Lead-Ads-Oberfläche hat eine **Mapping-Ebene** bekommen: `manage-meta-ads`
`resource: "leads"` kann jetzt `create_mapping`, `update_mapping`, `delete_mapping` und
`reprocess`, `query-meta-ads` `resource: "leads"` dazu `list_mappings`. Ein Lead-Formular
ohne aktives Mapping erzeugt **keine** Datensätze — jede Einreichung wird gespeichert und
als `skipped` markiert. Neu ist dabei, dass der **vollständige Payload mitgespeichert**
wird, bevor das Mapping gesucht wird: ein übersprungener Lead ist damit über `reprocess`
wiederherstellbar statt nach Metas ~90-Tage-Aufbewahrung endgültig verloren.

- **manage-meta-ads** — Die Tool-Tabelle führt die vier neuen Schreib- und die eine neue
  Leseaktion. Der Native-Lead-Ad-Ablauf hat einen neuen Schritt 2 („Mapping"), damit ein
  Formular nicht ohne Zuordnung live geht. Neuer Abschnitt „Lead intake" beschreibt
  `list_mappings` als erste Anlaufstelle, wenn Leads ankommen aber keine Kandidaten
  entstehen, die Parameter aller vier Schreibaktionen (zweistufig wie üblich, `form_id` +
  `mapper` `Candidate`/`Contact`, `field_mappings` weglassen = aus den Formularfragen
  abgeleitet, `reprocess` mit `form_id`/`lead_id`/`limit`, Default 200) und die
  Mapper-Felder inklusive des neuen **`full_name`**, das Metas `FULL_NAME`-Frage entspricht
  und beim Schreiben in Vor-/Nachname geteilt wird. Der Callout zu „sync liefert 0 Leads"
  grenzt jetzt gegen den Mapping-Fall ab. Festgehalten ist außerdem, dass
  `action: "describe"` für `leads` die neuen Aktionen noch nicht kennt — die Skill-Angaben
  gehen dort vor (an das alluvo-Team gemeldet).
- **using-alluvo-operator** — Der Eintrag zu `manage-meta-ads` nennt die Lead-Zuordnung als
  eigene Fähigkeit; neue Routing-Zeile für „Leads kommen an, werden aber keine Kandidaten".

### Changed — 2026-08-25 Rahmenverträge werden jetzt eigenständig zur Unterschrift nachgefasst — zweiter, opt-in Schalter (alluvo#4316)

Der tägliche Unterschrifts-Reminder hat seit alluvo#3786 **zwei unabhängige Hauptschalter**.
`signature_reminders_enabled` (Default **true**) steuert ab sofort nur noch Einsatzverträge;
neu daneben steht `framework_signature_reminders_enabled` — Default **false**, also bewusst
opt-in, damit kein Mandant, der die AÜV-Erinnerungen abgeschaltet hatte, ungefragt eine zweite
Erinnerungsstrecke an seine Kunden bekommt. Die Rahmenvertrags-Strecke läuft mit einem flachen
Intervall (`framework_signature_reminder_interval_days`, Default 7) ab `marked_as_sent_at` und
gibt nach `framework_signature_overdue_days` (Default 30) auf: Kundenmails stoppen, der
Vertragsinhaber wird einmal alarmiert, eine Folgeaufgabe geht auf. Beide Schalter sind auch in
der App unter **Einstellungen → Allgemein → Verträge** erreichbar.

- **manage-contract-lifecycle** — Schritt 1 (Rahmenvertrag) hält die neue Nachfass-Strecke
  fest: den opt-in Schalter, das flache Intervall statt der AÜV-Eskalationsstufen, die
  Aufgeben-Schwelle samt Folgeaufgabe, und die Bedingungen, unter denen ein Rahmenvertrag
  überhaupt angefasst wird (`sent`, kein `signed_at`, `marked_as_sent_at` gesetzt, Owner und
  ein erreichbarer Empfänger vorhanden). Schritt 4 stellt klar, dass die eskalierende Kadenz
  die Einsatzvertrags-Strecke ist und `signature_reminders_enabled` nicht mehr „die
  Unterschrifts-Erinnerungen" insgesamt meint. Neu dokumentiert: die Eskalations-Aufgabe
  („nicht rechtzeitig unterschrieben" bzw. „nicht unterschrieben zurückgekommen")
  **schließt sich selbst**, sobald `signed_at` geschrieben wird — eine offene Aufgabe ist
  also nie ein veralteter Fehlalarm, und sie von Hand gegen `signed_at` zu prüfen oder
  abzuhaken entfällt.

### Changed — 2026-08-24 `reply` / `reply-all` / `forward` nehmen jetzt Anhänge an — Nachweise und Profil-PDFs gehen direkt an der Antwort mit (alluvo#4300)

`manage-1on1-email` verwarf `employee_document_ids`, `profile_pdf_employee_ids`,
`profile_pdf_candidate_ids` und `profile_pdf_show_assignments` auf den Antwort-Actions
bisher still — eine Antwort auf eine Kundenrückfrage wurde ohne Anhang gedraftet, obwohl der
Text sie versprach. Die vier Schlüssel werden auf `reply`, `reply-all` und `forward` jetzt
genauso ausgewertet wie auf `draft` und `update`, und ein nicht anhängbarer Typ lehnt den
ganzen Aufruf ab, statt einen anhanglosen Entwurf zu hinterlassen. `forward` übernimmt
zusätzlich die Anhänge der Ursprungsmail.

- **profilvertrieb** — Schritt 6b nennt `reply` / `reply-all` als den Weg, auf eine
  Kundenrückfrage zu antworten (kein frisches `draft`, kein Umweg über `update`), und
  dokumentiert `forward` samt Übernahme der Original-Anhänge. Die Aufzählung der Actions, die
  `employee_document_ids` bzw. die Profil-PDF-Parameter annehmen, ist um die drei
  Antwort-Actions ergänzt; neu ist die Regel, dass eine einzige abgelehnte ID den kompletten
  Aufruf verwirft. Ebenfalls festgehalten: `forward` startet ohne Empfänger und das Tool hat
  auf keiner Action einen To-Parameter außer `draft` (dort aus `contact_id`) — ein hier
  gedrafteter Forward ist nur in der App adressier- und versendbar (alluvo#4320).
- **call-summary** — dieselbe Ergänzung der Action-Listen für Nachweis und Profil-PDF, plus
  der Hinweis, die Nachfass-Mail als `reply` zu schreiben, wenn das Telefonat an einer
  bestehenden Mail hing.

### Changed — 2026-08-24 WhatsApp-Einwilligung ist erfassbar und auslesbar — und `manage-record-action` nennt die Formularfelder (alluvo#4298)

Eine außerhalb von alluvo erteilte WhatsApp-Einwilligung hatte bisher keinen Schreibweg: Die
Quelle `manual` existierte im Enum, aber nichts in der App und nichts über MCP konnte sie
setzen — ein Kontakt kam nur dann in eine Kampagnen-Zielgruppe, wenn er selbst zuerst
geschrieben hatte. Die neue Contact-Action `record-whatsapp-consent` (`0-105`) erfasst sie mit
Pflicht-`reason` (10–1000 Zeichen, die Rechtsgrundlage nach DSGVO / UWG § 7) und optionalem
`opt_in_at` (`YYYY-MM-DD`, Default heute, kein Zukunftsdatum). Sie ist gesperrt, sobald bereits
eine Einwilligung **oder** ein Widerspruch vorliegt — mit zwei unterschiedlichen Texten, die
gegensätzliche nächste Schritte bedeuten. Die `whatsapp_*`-Spalten bleiben über `manage-model`
bewusst nicht schreibbar.

- **enrich-contacts-from-activities** — neuer Abschnitt zu `record-whatsapp-consent`: Parameter
  und ihre Grenzen, die Regel „nur erfassen, was belegt ist" (kein Beleg → keine Aktion, erst
  recht nicht, um einen Versand freizuschalten), und die Unterscheidung der beiden
  Sperr-Gründe — eine bestehende Einwilligung heißt „nichts zu tun", ein Widerspruch heißt
  „stopp", nie eine korrigierbare Datenlücke. Die Liste der über MCP **nicht** schreibbaren
  Felder ist um den kompletten `whatsapp_*`-Block ergänzt; die `description` triggert jetzt
  auch auf „WhatsApp-Einwilligung erfassen" und „darf ich diesen Kontakt per WhatsApp
  anschreiben".
- **using-alluvo-operator** — zwei querschnittliche Korrekturen. `search-model` lehnt ein Feld
  nicht mehr als unbekannt ab, nur weil es keine Tabellenspalte ist: ein Feld, das
  `get-model-schema` (Kontext `list`) führt und das `filter_groups` längst annahm, liefert in
  `fields` jetzt seinen Wert — die sieben `whatsapp_*`-Consent-Felder des Kontakts sind damit
  aus einer Listenabfrage lesbar statt nur per `get-model` pro Datensatz. Und
  `manage-record-action` `operation: "list"` druckt **mit** `record_id` jetzt einen
  `Form fields:`-Block (Name, Typ, `(required)`, Label) statt die Felder von Step-Formularen zu
  verschweigen; ohne `record_id` steht dort weiterhin nur `Has form: Yes`. Also die Parameter
  vorab lesen, statt eine Aktion blind aufzurufen und sie aus dem Validierungsfehler
  abzuleiten.

### Changed — 2026-08-24 `submit_beleg` ist über MCP ausführbar geworden — Draft-Auslage, Auto-Commit und Stellvertretung beim Einreichen (alluvo#4294)

Die Action `submit_beleg` auf Employee (`0-2`) hatte bisher nur ein echtes Datei-Feld und war
über MCP damit nie ausführbar; die Skill dokumentierte sie folgerichtig als „geht nicht".
Sie nimmt den Beleg jetzt zusätzlich als `beleg_base64` entgegen (JPEG/PNG/PDF, Format über
Magic Bytes erkannt), legt sofort eine **Draft-Auslage** (`0-20`, `type: auslagen`,
`status: draft`, `amount: 0`) an und lässt die Extraktion den Beleg danach automatisch
einhängen.

- **`approve-stundenfreigabe`** — der Abschnitt „Filing a Beleg for an employee" ist von
  „a real action, but not one you can run" auf den tatsächlichen Aufruf umgeschrieben:
  `beleg_base64` statt `beleg`, die drei Fehlermeldungen (keine Datei, ungültiges Base64,
  Mitarbeitende:r ohne auflösbaren Owner) und die drei Ausgänge der Extraktion. Zwei davon
  lassen die Draft-Auslage **leer** — eine Warnung (Dublettenverdacht oder mehrere Belege auf
  einem Scan) blockiert das automatische Einhängen bewusst, ebenso ein Extraktionsfehler; in
  beiden Fällen wird die handelnde Person benachrichtigt. „Beleg hochgeladen ≠ Auslage fertig"
  bleibt also richtig, aber aus einem anderen Grund als bisher beschrieben.
- Ebenda korrigiert: **direkt nach dem Aufruf existiert die Auslage schon** (vorher stand dort,
  `query-model` auf `0-20` zeige zu Recht nichts) — sie ist nur noch ohne Beleg. Und der
  Entwurf ist für die Mitarbeitenden **sichtbar**: `submit_beleg` bucht ihn auf sie als
  Ersteller:in, anders als ein per `manage-model` angelegter Entwurf, der weiter verborgen
  bleibt.
- **Einreichen in Stellvertretung ist jetzt erlaubt** — `submit` verlangt für Nicht-Eigentümer
  die gescopte `reimbursements.edit`-Berechtigung. `cancel` bleibt bewusst Eigentümer-only
  (sonst wäre Submitted → cancel → ändern → erneut einreichen ein Umgehungsweg ohne Prüfspur)
  und darf nicht als Operator-Fähigkeit beschrieben werden. Dazu neu dokumentiert: `submit`
  prüft Pflichtfelder, die eine belegbasierte Auslage gar nicht trägt (`purpose`,
  `reimbursement_category_id`, `start_date`, `end_date`) — erst per `manage-model` füllen.
- **`using-alluvo-operator`** nennt in der Skill-Liste jetzt auch die Erstattungsseite von
  `approve-stundenfreigabe` samt Beleg-Erfassung für Mitarbeitende.

### Changed — 2026-08-24 „Gib X Zugriff auf Y" ist jetzt ein Tool-Aufruf statt Raterei (alluvo#4277)

`manage-permission-set` hat eine dritte `resource`: **`access`**. Sie beantwortet die Frage von
der Seite her statt vom Berechtigungsschlüssel — „welche Berechtigung sperrt den Teamkalender,
und hat Melissa sie?". Das war vorher nirgends beantwortbar: Die Sidebar kennt Label und
Nav-Gate, der Router kennt sein `can:`-Middleware-Gate, der Berechtigungskatalog kennt die
Schlüssel, und niemand führte die drei zusammen. Eine Seite ist **zweifach** gesperrt
(Sidebar-Link + Route), und keiner der beiden Schlüssel ist aus dem Seitennamen ableitbar.
`explain` liest die Gate-Kette (mit `user_id` zusätzlich ✅/❌ pro Schlüssel für diese Person),
`grant` schließt die Lücke. Beides ist ausschließlich für Super-Administratoren. `set` und
`assignment` sind unverändert.

- **using-alluvo-operator** — neuer querschnittlicher Abschnitt; die `description` triggert jetzt
  zusätzlich auf „gib X Zugriff auf Y" und „warum sieht X die Seite nicht". Die Kernpunkte, die
  eine Skill nicht übergehen darf: `grant` schreibt in eine **Rolle**, ist also selten eine
  Änderung für eine einzelne Person — die Vorschau nennt, wie viele **andere** Nutzer dieselbe
  Berechtigungsgruppe halten, und diese Zeile gehört wörtlich zurück an den Operator, bevor jemand
  bestätigt (nur diese eine Person: duplizieren, Kopie zuweisen, auf der Kopie granten). Ein
  mehrdeutiger Seitenname liefert eine Kandidatenliste statt eines Treffers — „Kalender" trifft
  Teamkalender, Dienstplan und Buchungskalender —, die Auswahl trifft der Operator, nie die erste
  Zeile. Der vorgeschlagene Scope spiegelt den dominanten Scope der Rolle und greift nie
  stillschweigend nach `all`: Eine filialgebundene Gruppe, die unbemerkt eine `all`-Berechtigung
  bekommt, wird zu einer filialübergreifenden Rolle — ein AÜG-Datentrennungsproblem, kein
  Bedienungsdetail. Zweistufig wie überall: Vorschau, ausdrückliches Ja, dann `confirmed: true`.
  Dazu die Verweigerungsgründe von `grant` (keine Gruppe / nur Systemgruppen / mehrere
  editierbare) mit dem jeweils nächsten Schritt, und der Hinweis, dass „angewendet" noch nicht
  „sichtbar" heißt — effektive Berechtigungen reisen mit der Seiten-Payload, ein Reload kann nötig
  sein. Mit dokumentiert: `describe-permissions` druckt jetzt den zuweisbaren **Schlüssel**
  (`employees.view`) statt des Anzeigelabels („View") und hängt je Schlüssel ein
  `unlocks: <Seiten>` an.

### Changed — 2026-08-23 Outreach-Enrolment mit Personalbedarf sendet jetzt wirklich — Profil-Anhängung nach Vorrang, nicht nach Modusnamen (alluvo#4270)

Der Zweig „Enrolment mit `staffing_requirement_id`" in `resolveEmployeesForEmail()` rief
`->load()` auf einer `Support\Collection` auf und warf damit für **jedes** nicht-leere
Match-Set eine `BadMethodCallException` — der Sendejob scheiterte, die Mail ging nie raus.
Bedarfsgetriebenes Outreach hat auf diesem Weg also nie gesendet. Der Pool kommt jetzt als
`Eloquent\Collection` zurück, der Eager Load funktioniert, und der Zweig sendet. Die
Auswahl-Logik selbst ist unverändert.

- **`enroll-outreach`** bekommt die vollständige Vorrangkette, mit der ein Draft seine Profile
  auflöst — handverlesene Liste (`explicit_employee_ids` bzw. die von `create` abgeleitete)
  → gepinnter Primary allein (**genau ein** Profil, der verknüpfte Bedarf wird hier *nicht*
  herangezogen) → Bedarf (bis zu **3** Matches, jedes mit eigenem Stundensatz) → Segment.
  Dazu drei Fallen, die vorher nirgends standen:

  - `advanced` **ohne** `staffing_requirement_id` fällt still auf Segment-Matching zurück —
    kein Fehler. Wer Bench-Profil *und* Bedarfs-Matches in einer Mail will, braucht
    `advanced` **plus** `primary_employee_id` **plus** `staffing_requirement_id`; `create`
    legt dann Primary + 2 Matches als handverlesene Liste ab.
  - `attach_profiles_mode: "none"` unterdrückt Profile **nicht**, wenn ein Bedarf verknüpft
    ist: ohne Primary greift trotzdem der Bedarfszweig und hängt bis zu 3 Profile an. Eine
    reine „wir stellen uns vor"-Mail lässt `staffing_requirement_id` ebenfalls leer.
  - Der Bedarfszweig filtert zum Draft-Zeitpunkt **keine** bereits eingesetzten Mitarbeiter
    heraus (die Vorauswahl in `create` tut das) — Preview zurücklesen und jeden, der nicht
    mehr verleihfrei ist, vor der Freigabe entfernen.

  Außerdem korrigiert: die Parameterzeile für `create` nannte ein `sequence_id`, das die
  MCP-Schnittstelle nicht kennt — es ist `selling_profile_id`.

- **`profilvertrieb`** §6a hält fest, dass das Pinnen des Bench-Profils allein keine
  Bedarfs-Matches mitpitcht, und verweist für die vollständige Kette auf `enroll-outreach`.


### Changed — 2026-08-23 Reisekosten/Auslagen: Statusgate auf den Übergängen, Duplikatsprüfung beim Einreichen (alluvo#4225)

> **Nachtrag.** Die erste Fassung dieses Eintrags beschrieb `resolve_clarification`,
> `confirm_authorization` und `decline_authorization` als dauerhaft **nicht** gegatet. Das war
> beim Schreiben korrekt und ist es nicht mehr: der Befund aus diesem Drift-Review hat
> alluvo#4243 ausgelöst, das die drei nachzieht. Die Matrix unten beschreibt den Stand nach
> #4243 — neun gegatete Aktionen, nicht sechs.

`Submit`, `Approve`, `Reject`, `MarkAsPaid`, `MarkAsNeedsRevision` und
`CancelReimbursementAction` haben jetzt ein `stateAllows()`. Vorher hing die Statusbedingung
allein an der `ReimbursementPolicy`, und der `Gate::before`-Kurzschluss für Plattform-Admins
hat jede Policy-Prüfung übersprungen — die Oberfläche und `manage-record-action` boten
Übergänge an, die längst passiert waren (Reisekosten 27 war bereits eingereicht und bot
weiterhin „Zur Genehmigung einreichen"; ein zweiter Lauf hätte `review_note` gelöscht und eine
zweite Freigabeaufgabe erzeugt). Parallel prüft der Einreichen-Endpunkt der Mitarbeiter-App über
`DuplicateReceiptDetector::liveClaimDuplicateFor()`, ob daraus ein **zweiter Live-Anspruch** auf
einen schon abgerechneten Beleg würde.

- **`approve-stundenfreigabe`** bekommt die vollständige Matrix aller **neun** gegateten
  Aktionen (`submit` → `draft`/`needs_revision`, `cancel` → `submitted`/`needs_revision`,
  `approve`/`reject`/`request_revision` → `submitted`, `mark_as_paid` → `approved`,
  `confirm_authorization`/`decline_authorization` → `submitted` **und**
  `authorization_status: pending`, `resolve_clarification` → `needs_clarification: true`) plus
  den entscheidenden Lesehinweis: die Aktion **verschwindet nicht** aus `list`, sie steht dort
  mit `**Available:** No` und dem Status-Grund — das ist **keine fehlende Berechtigung**,
  sondern der falsche Status, und die Antwort an den Operator ist der Status selbst, kein
  erneuter Versuch.

  Die Freigabe-Paarung hängt an `authorization_status`, nicht nur am Status: ein zweites
  `confirm_authorization` hätte den Datensatz erneut in die Owner-Queue geleitet und eine
  zweite Freigabeaufgabe erzeugt. Keine Einbahnstraße — jedes (erneute) Einreichen setzt
  `authorization_status` auf `pending` zurück, ein abgelehnter und neu eingereichter Datensatz
  ist also wieder bestätigbar.
- **`approve-stundenfreigabe`, Belege:** neue Passage zur **Duplikatsprüfung beim Einreichen**
  (120 Tage, gleiche Mitarbeiterin, Gegenstück mit Status `submitted`/`approved`/`paid`,
  Treffer über Datei-Hash oder `document_date` + `amount_gross`, geschärft durch
  `document_number`). Zwei Konsequenzen für den Assistenten: die Prüfung sitzt am
  **App-Endpunkt, nicht an der `submit`-Aktion** — ein `submit` über `manage-record-action`
  umgeht sie vollständig, also vorher selbst über den `receipts`-Include vergleichen; und ein
  eingereichter Datensatz ist **nicht** als duplikatfrei zertifiziert (entweder kein Treffer
  oder die Mitarbeiterin hat bestätigt).
- **`using-alluvo-operator`** benennt im Abschnitt zu `manage-record-action` `list` jetzt die
  vier festen `Unavailable reason:`-Strings (Status / Berechtigung / Stellvertretermodus /
  generisch, DE und EN) und den `Current record status: <status>`-Zusatz, den `execute` an
  denselben Grund hängt — damit ein Statusblock nicht länger als fehlendes Recht gemeldet wird.

### Changed — 2026-08-21 Abteilungen sind archivierbar: `archive`/`unarchive` auf `0-107` (alluvo#4202)

`CompanyDepartment` (`0-107`) nutzt jetzt den `Archivable`-Mechanismus, und
`CompanyDepartmentResource::actions()` registriert die generischen `ArchiveRecord`/
`UnarchiveRecord`. `manage-record-action` `list` auf `0-107` liefert damit `archive`/
`unarchive`, und der Assistent kann eine Abteilung stilllegen statt zu löschen — der Ausweg aus
der Lösch-Sackgasse, weil eine Abteilung mit Einsätzen/Verträgen nie löschbar ist. Im
Kundenportal hat die Abteilungsliste (`/objects/company-departments`) eine Zeilen-Aktionsleiste
und einen **„Archiviert"**-Tab; die alte handgebaute `/departments`-Seite ist weg (Redirect), und
archivierte Abteilungen fallen aus dem Portal-Buchungs-Picker.

- **Neuer übergreifender Abschnitt in `using-alluvo-operator` — „Retiring a record instead of
  deleting it (`archive` / `unarchive`)"**: die zwei generischen MCP-Aktionen, zweistufig wie
  immer, gegenseitig exklusiv (`archive` verschwindet, sobald archiviert). `archived_at` steht in
  **keinem** `update`-Schema — `manage-model`/`bulk-manage-model` verwerfen es still, die Aktion
  ist der einzige Weg. Und der Punkt, der wirklich beißt: **es gibt keinen Global Scope**,
  archivierte Datensätze kommen bei `search-model`/`query-model`/`get-model` normal zurück, und
  `archived_at` ist keine Default-Anzeigespalte — also explizit anfordern
  (`fields: [… , "archived_at"]`) oder filtern (`is_null` = aktiv, `is_not_null` = archiviert),
  bevor ein Treffer als aktuell dargestellt wird.
- **`intake-personalbedarf`** dokumentiert das Stilllegen einer Abteilung und trennt die **zwei
  unabhängigen Flags**: `is_active` (mit `manage-model` schreibbar, der Hebel des Operators —
  nimmt die Abteilung aus dem Einsatz-/Dienstplan-Kandidatenpool) gegen `archived_at`
  (nur per Aktion, das „raus aus meiner Liste"-Flag des Kunden — Portal-Liste, „Archiviert"-Tab,
  Buchungs-Picker). Beschreibung um die Trigger „Abteilung archivieren", „Station stilllegen",
  „Abteilung lässt sich nicht löschen" erweitert.
- **`manage-contract-lifecycle` + `match-bench-to-clients`:** eine **archivierte Abteilung wird
  weiterhin als Station akzeptiert** — `manage_einsatz` prüft nur Existenz und Zugehörigkeit zum
  Einsatzort (api#4210). Beim Auflösen einer Abteilung nach Namen deshalb `archived_at`
  mitanfordern und den Operator bestätigen lassen: die Abteilung steht im unterschriebenen AÜV
  und in der Einsatzmitteilung nach § 11 Abs. 2 AÜG.
- **`account-research`:** archivierte Abteilungen im Company-Brief als stillgelegt kennzeichnen,
  nicht als aktive Stationen listen.

### Changed — 2026-08-21 Slack-Aktion: Kanal per **Name**, Kanalliste aus `describe-action` (alluvo#4201)

`send_slack_message` nimmt jetzt `channel_name` entgegen (`"alluvo-stundenfreigabe"`, mit oder
ohne `#`, Groß-/Kleinschreibung egal). Der Name wird **beim Speichern** des Workflows zur
Kanal-ID aufgelöst, gespeichert wird die ID — ein späteres Umbenennen in Slack kann den
Workflow also nicht mehr zerreißen. `channel_id` bleibt gültig und gewinnt, wenn beides
angegeben ist.

- **`build-automation-agent`, *Slack delivery*:** Config-Zeile um `channel_name` ergänzt und
  ein neuer Absatz „Name the channel, don't hunt for its id". Der Umweg „ID aus einem
  bestehenden Workflow abschreiben" ist ausdrücklich abgeräumt — `describe-action` mit
  `action_type: "send_slack_message"` liefert jetzt zusätzlich **die echten Kanäle des
  Mandanten** (Name + ID, markiert `private` bzw. `bot not a member`), die dem Operator per
  Name angeboten werden statt ihn nach einer ID zu fragen.
- Ein unbekannter Name wird beim Speichern abgelehnt und nennt dabei die existierenden Kanäle.
  Ein privater Kanal, in den alluvos Slack-Bot noch nicht eingeladen wurde, taucht in der Liste
  gar nicht erst auf — die Einladung passiert in Slack, außerhalb von MCP.

### Changed — 2026-08-20 Aktions-Katalog: `list` ohne `record_id` ist verlässlich, Degradations-Zeilen lesen (alluvo#4142)

`manage-record-action` `operation: "list"` **ohne** `record_id` (der statische Aktions-Katalog
eines Modelltyps) riss bei 11 Modelltypen — darunter `0-3`, `0-30`, `0-31`, `0-105`, `0-426` —
den ganzen Katalog mit, weil eine einzelne Aktion sich ohne Datensatz nicht beschreiben ließ.
Das ist behoben; Signatur, Parameter, Enums und Modelltypen sind unverändert. Neu ist, dass
eine nicht beschreibbare Aktion zu **einer Zeile** degradiert, statt die Antwort zu verlieren —
und genau diese Zeile liest sich wie eine Fehlermeldung, ist aber keine.

- **Neuer übergreifender Abschnitt in `using-alluvo-operator` — „Discovering an action before
  you run it (`manage-record-action` `operation: "list"`)"**: die zwei Gestalten von `list`
  (mit `record_id` = Verfügbarkeit am Datensatz, ohne = statischer Katalog des Modelltyps), und
  dass Verfügbarkeit im Katalog per Definition nicht beantwortet wird (`Note: Availability is
  per-record`).
- **Die beiden Degradations-Zeilen ausdrücklich als *keine* Fehlermeldung dokumentiert.**
  `_Details unavailable without a record — pass record_id for this action._` (Katalog) und
  `_Could not be described for this record (reported); the action itself is unaffected._`
  (pro Datensatz) heißen „dieser eine Eintrag ließ sich hier nicht rendern" — nicht „die Aktion
  existiert nicht", nicht „die Aktion ist gesperrt", nicht „das Tool ist kaputt". Der Name der
  Aktion steht in der Zeile darüber, der Rest der Antwort ist intakt; die richtige Reaktion ist
  ein zweiter Aufruf **mit** `record_id` bzw. ein `execute` mit `confirmed: false`. Dieselbe
  Nachsicht-Kehrseite wie „eine fehlende Spalte ist kein leerer Wert".
- **Abgegrenzt, was wirklich „nicht ausführbar" heißt:** `**MCP-exposed:** No` (kein
  `#[McpExposed]`, also App-Aufgabe für den Operator) gegen `**Available:** No` (Status- oder
  Rechte-Sperre auf einer ausführbaren Aktion, immer mit Begründung).
- **Katalog-Label ist das *deklarierte* Label.** Eine Aktion mit datensatzabhängigem Label
  (Pause/Aktivieren-Umschalter) zeigt im Katalog ihr generisches — gelegentlich leeres — Label.
  Labels dem Operator aus dem Aufruf **mit** `record_id` zitieren und nie den Zustand eines
  Datensatzes aus einem Katalog-Label ableiten.

### Changed — 2026-08-20 Stundenfreigabe am Gerät: Unterzeichner-Auswahl (alluvo#4148)

Der on-device Signaturfluss der Stundenfreigabe hat die Auswahl der unterschreibenden Person
umgebaut. Kein MCP-Tool, kein Schema und kein Enum ändert sich — was sich ändert, ist der Rat,
den ein Operator geben kann.

- **`approve-stundenfreigabe`, Empfangsmail:** Ein handgetippter Unterzeichner ist jetzt vor der
  Unterschrift korrigierbar („Angaben bearbeiten" / „Edit details") — die E-Mail lässt sich
  nachtragen, ohne Name und Telefon neu zu tippen. Damit hat „warum hat XY keine Bestätigung
  bekommen" eine neue, gangbare Antwort. Mit den zwei Grenzen dokumentiert: nur für einen
  selbst getippten Unterzeichner (ein bestehender Firmenkontakt ist Stammdaten →
  `manage-model` `update` auf `0-105`), und nicht rückwirkend — nach dem Absenden wird die
  Quittung für diese Unterschrift nicht nachträglich verschickt.
- **`approve-stundenfreigabe`, neuer Abschnitt „The signer picker":** Kontakte mit dem
  Pivot-Label **`timesheet_approver`** stehen oben in der Auswahlliste und tragen jetzt sichtbar
  das Badge „Ansprechpartner". Wichtig für Operatoren: das Badge hängt an genau dieser
  Zeichenkette — das freundliche `label: "Ansprechpartner"` im `manage-association`-Beispiel
  erzeugt es **nicht**. Ebenfalls neu dokumentiert: alluvo schreibt das Label nach jeder
  Vor-Ort-Unterschrift selbst und **überschreibt** dabei ein von Hand gesetztes.
- **`merge-duplicate-companies`:** Die abgeschaltete iOS-Autokorrektur im Suchfeld als Herkunft
  von Kontakt-Dubletten auf Kundenfirmen aufgenommen — inklusive Erkennungsmuster und dem
  Hinweis, dass der überlebende Kontakt `timesheet_approver` und den Approver-Grant behalten
  muss. Quer verlinkt in beide Richtungen.

### Changed — 2026-08-20 Tags: elf weitere Modelle taggbar, und eine Person hat EIN Tag-Set (alluvo#4137)

Die Skills behaupteten, `Agent` sei der einzige taggbare Datensatz und `tags` auf jedem anderen
Modelltyp sei stillschweigend wirkungslos — richtig zum Zeitpunkt von alluvo#4080, seit
alluvo#4136 falsch, und falsch in der Richtung, in der der Assistent Arbeit ablehnt, die er
erledigen kann.

- **Neuer übergreifender Abschnitt in `using-alluvo-operator` — „Tagging a record (`tags`)"**:
  die **zwölf** taggbaren Modelltypen mit ihren IDs (Company `0-3`, Contact `0-105`, Employee
  `0-2`, Candidate `0-81`, StaffingDemand `0-415`, Task `0-5`, Ticket `0-300`, KnowledgeBase
  `0-180`, KnowledgeBasePage `0-181`, NewsArticle `0-187`, Workflow `0-365`, Agent `0-400`), das
  überall identische Feldverhalten (Namen statt IDs, vollständiges Ersetzen statt Anhängen,
  unbekannte Namen werden angelegt, `[]` leert, `tags_colors` beim Lesen) und die
  tenant-weite Vokabelverwaltung über `0-443`.
- **Die eine Regel, die ein Skill nicht falsch haben darf:** *eine Person hat EIN Tag-Set, nicht
  eines pro Rollen-Datensatz*. Employee und Candidate führen keine eigenen Tags — ihre liegen am
  verknüpften **Kontakt**. Mitarbeiter und Bewerber am selben Kontakt sehen dieselbe Liste. Kein
  Skill darf Mitarbeiter-Tags und Kontakt-Tags als zwei Dinge beschreiben oder zum „zusätzlich
  den Kontakt taggen" auffordern — das ist derselbe Schreibvorgang zweimal.
- **Schreibwege pro Typ benannt**, statt sie zu raten: `manage-model` `update` für Company,
  Contact, Task, StaffingDemand, KnowledgeBase, KnowledgeBasePage, NewsArticle (zweistufig wie
  jeder generische Write); Agent je nach Agententyp (siehe `build-automation-agent`); Ticket und
  Workflow sind zwar taggbar, **über MCP aber nicht schreibbar** — beide sind nicht generisch
  verwaltbar und kein dediziertes Tool führt `tags`.
- **Employee/Candidate schreiben auf den Kontakt.** `manage-model` `update` mit `tags` am
  Mitarbeiter oder Bewerber funktioniert und landet am verknüpften Kontakt — dort liegen die
  Tags. Direkt an Contact `0-105` zu schreiben ist derselbe Vorgang mit demselben Ergebnis.
  (Der ursprüngliche Befund alluvo#4138 — Erfolgsmeldung ohne Write — ist gefixt und live.)
- **Filtern nach Tag dokumentiert:** jeder taggbare Typ ist auf **oberster Ebene** von
  `query-model` / `search-model` über einen `tags`-Beziehungsfilter mit Unterbedingung auf `name`
  oder `color` filterbar (z. B. alle Mitarbeiter mit Tag „Nachtschicht"); eine Relation tiefer
  wird er nicht angeboten.
- **Tag-Änderungen sind auditierbar:** sie stehen als Event **`tagged`** mit Vorher/Nachher in der
  Änderungshistorie des Datensatzes — `get-field-history` mit `field: "tags"`. Bei einer Person
  am Kontakt, an den geschrieben wurde.
- **`build-automation-agent`** korrigiert an zwei Stellen (Glossar-Zeile `Tag (0-443)` und der
  Abschnitt *Tags*): Agent ist einer von zwölf taggbaren Typen, nicht der einzige; die
  übergreifenden Regeln stehen jetzt in `using-alluvo-operator`, die agentenspezifischen
  Schreibwege bleiben hier.

Nebenbefund beim Verifizieren: der Issue-Text nannte Workflow `0-410` — auf `origin/main` ist
Workflow `0-365`; die Skills führen die verifizierte ID.

### Changed — 2026-08-20 MCP-Konsolidierung 103 → 81 Tools: Meta, Profile, Verfügbarkeit (alluvo#4134)

Der MCP-Werkzeugkasten wurde von 103 auf 81 Tools zusammengeführt (`tools/list` −18 %). Die
alten Namen sind **entfernt**, nicht deprecated — ein Aufruf endet in „Tool not found". Die
Skills, die sie beim Namen nannten, sind auf die neue `resource`/`action`-Form umgestellt.

- **Meta: neun Tools → zwei.** `manage-meta-ads` (alle Schreibvorgänge) und `query-meta-ads`
  (alle Lesevorgänge), jeweils `resource` + `action`. Die Tool-Tabelle in `manage-meta-ads`
  ist eine Resource-×-Aktion-Matrix (`campaign`, `ad_set`, `ad`, `creative`, `leads`,
  `audiences`, `conversions`, `automation_rules`, `campaign_insights`, `reach`,
  `ad_library`); jeder Aufruf im Skill — Lead-Ads-Flow, Creatives-Workflow, UTM,
  Verify-then-launch — nennt jetzt Tool + `resource` + `action`.
  - **`entity_type` ist weg**: `resource` sagt bereits, worauf `entity_id` zeigt. `entity_id`
    ist außerdem die Ziel-ID für `get_adset`/`update_adset` (vorher `adset_id`),
    `update_ad_creative` (vorher `ad_id`) und `configure` (vorher `campaign_id`).
    Eltern-IDs bleiben: `create_ad` nimmt weiter `adset_id`, `create_adset` weiter
    `campaign_id` + `ad_account_id`.
  - **Feld-Dokumentation nur noch über `action: "describe"`** — die Parametermatrix steht
    nicht mehr in der Tool-Beschreibung.
- **`get-employee-availability` → `manage-employee-availability`** (Parameter unverändert) in
  `bench-check`, `profilvertrieb`, `match-bench-to-clients`, `head-of-disposition`,
  `record-absence`, `clean-inbox`. Lesen (`calendar`, `unassigned`, `explain`,
  `vacation-balance`, `list-shifts`) braucht kein `confirmed`; nur die Schreibaktionen sind
  zweistufig.
- **`get-profile-url` und `get-profile-completeness` → `get-profile`** mit
  `resource: "url"` bzw. `"completeness"`; `"profile"` ist der alte `get-profile`-Fall und
  jetzt **Pflichtparameter**, also an jedem bestehenden Aufruf ergänzt. Bei `resource: "url"`
  heißt der alte `action`-Parameter `link_type` (Werte `public_url` / `completion_link`
  unverändert) — und dieser Aufruf **schreibt** (Token-Zeile), ist also kein reiner Lookup.
  Betrifft `profilvertrieb`, `match-bench-to-clients`, `enroll-outreach`,
  `onboard-new-employee`, `bench-check`, `triage-data-quality`, `prospect-companies`.
- **Neu in `using-alluvo-operator`: „Fetching docs on demand"** — `action: "describe"` (jetzt
  auf zehn Tools), das neue **`get-tool-guidance(tool_names)`** (Langform-Anleitung für
  `manage-model`, `search-model`, `query-model`, `manage-record-action`,
  `manage-association`, `bulk-manage-model`; max. 10 Namen) und `get-model-schema`'s neues
  `fetch_options` (`description`, `read_guidance`, `write_guidance`, `default_fields`).
- **`list-model-types` verschweigt nichts mehr.** Es listet alle Modelltypen mit Status
  (`available` / `read_only` / `requires_permission` / `requires_feature` / `not_available`)
  und Begründung. „Steht nicht in der Liste, also gibt es das nicht" ist damit kein gültiger
  Schluss mehr — in `build-automation-agent` (`0-422`, `0-433`) und
  `approve-stundenfreigabe` korrigiert, die genau so argumentiert hatten.
- **Unverändert und bewusst so:** `get-booking-availability` und
  `get-notification-preferences` bleiben eigene Tools — ihr `#[AutomationSafe]` +
  `#[IsReadOnly]` ist das Fail-closed-Tor für Automations-Agents, eine Zusammenlegung hätte
  denen still den Lesezugriff genommen. Kein Skill musste dafür angefasst werden.

### Changed — 2026-08-20 Stundenfreigabe: „Meine Freigaben" im Menü, Bestätigung nennt Inhalt, `lastRelease` (alluvo#4129)

Der Mitarbeiter hatte nach der Unterschrift keine Fläche, die „ist angekommen" beantwortet — die
Erfolgsmeldung war nach drei Sekunden weg, der Wizard zeigt nur Offenes. Das ist jetzt an drei
Stellen behoben; `approve-stundenfreigabe` beschreibt sie, damit der Operator die Rückfrage
beantworten kann, statt sie selbst nachzuschlagen.

- **Neuer Abschnitt in `approve-stundenfreigabe`** — „Ist meine Unterschrift angekommen?": der
  dauerhafte Menüeintrag **„Meine Freigaben"** (Gruppe *Stunden & Auslagen*, nur bei aktiver
  Zeiterfassung) neben dem bestehenden Eintrag *Stundenfreigabe* — der eine zeigt die Zeiträume,
  der andere öffnet den Batch-Sign-Dialog.
- **Zwei Grenzen benannt**, bevor man einem Mitarbeiter eine lückenlose Historie verspricht: die
  Seite reicht nur ~42 Tage zurück (dasselbe Fenster wie die Freigabeliste), und sie führt nur
  `PendingEmployee` / `Approved` / `Disputed` (plus Zeiträume mit offener Kundenkorrektur). Ältere
  Zeiträume stehen in der operatorseitigen Stundennachweis-Liste, sie sind nicht verloren. Es ist
  außerdem kein reines Archiv — Bestätigen, Widersprechen und Vor-Ort-Unterschrift laufen dort.
- **Die Bestätigung nach der Sammelunterschrift nennt Inhalt** — Anzahl Zeiträume · Anzahl Tage,
  Datumsspanne, „Unterschrieben von", Button „Zu meinen Freigaben", Auto-Close 3 s → 6 s. Die
  Zahlen stammen aus der abgeschickten Auswahl, bei einer **Teilfreigabe** also die tatsächlich
  freigegebenen Tage — vier Tage auf einer Fünf-Tage-Woche sind richtig, kein verlorener Tag.
- **Der Leerzustand des Wizards unterscheidet „nichts zu tun" von „schon freigegeben"** — „Alles
  freigegeben" mit Datum/Uhrzeit, Zeitraum und Unterzeichner. Gespeist aus der jüngsten **noch
  stehenden** `TimesheetRelease` (`0-435`, mindestens ein nicht zurückgenommener Tag), über die
  Zeiträume des Mitarbeiters — der genannte Name ist der **Kundenvertreter**, nicht der
  Mitarbeiter. **Freigaben per Fristablauf zählen bewusst mit** (`signer_label` liefert das „wer").
- **Keine MCP-Änderung.** Kein Tool, kein Parameter, kein Enum — reine Produktfläche, die der
  Operator beschreiben können muss. Prüfen lässt sie sich weiterhin über `0-435`.

### Changed — 2026-08-20 Agenten umbenennen und taggen ohne Spezialtool (alluvo#4126)

Die Schreibfläche für Agenten (`Agent`, `0-400`) hat sich an zwei Stellen geöffnet — die
Leitplanken bleiben, aber "Agenten sind über `manage-model` read-only" stimmt nicht mehr.

- **Neue Aktion `set-tags` auf `manage-agent-prompt`** (`build-automation-agent`) — taggt
  einen **konversationellen oder Task-Agenten**: `agent_id` + `tags` (volle Namensliste,
  ersetzt den bisherigen Satz, legt unbekannte Tags tenant-weit neu an, `[]` löscht alle).
  Als einziger Schreibvorgang dieses Tools **einstufig, ohne `confirmed`** — ein Tag ändert
  nichts an dem, was der Agent sagt. Automatisierungs-Agenten werden hier abgewiesen und
  bleiben beim `tags`-Parameter von `manage-automation-agent`.
- **`manage-model` `update` erreicht jetzt `0-400`** — über eine bewusst winzige Allowlist:
  `name`, `display_name`, `tags`. Mehr nicht. `create` wird komplett abgewiesen (ein generisch
  erzeugter Agent hätte weder `type` noch `agent_flow_key`).
- **Neuer Abschnitt "Renaming and tagging an agent" in `build-automation-agent`** mit der
  vollständigen Aufteilung: Verhaltens- und Lifecycle-Felder (`system_prompt`, `instructions`,
  `blocks`, `instruction_block_ids`, `capabilities`, `enabled_tools`, `output_schema`,
  `is_active`, `greeting_message`, `initial_message`) werden mit einem Hinweis auf das
  zuständige Tool abgelehnt; `type`, `agent_flow_key`, `agent_key`, `is_system`, `owner_id`
  sind unveränderlich; alles Übrige (`language`, `model_name`, `quick_replies`, …) fällt
  stillschweigend raus und taucht nur im Ignored-Field-Report auf.
- **`using-alluvo-operator`** und die Tags-Sektion von `build-automation-agent` nennen jetzt
  drei Schreibwege für Agenten-Tags statt einem, jeweils nach Agententyp.

### Changed — 2026-08-19 Vorlaufzeit pro Terminart, Operator-Bypass und `meeting.owner_assigned` (alluvo#4093)

Die Buchungs-Vorlaufzeit ist keine reine Personeneinstellung mehr: eine **Terminart**
(`MeetingType`, `0-348`) trägt jetzt ein eigenes `min_notice_minutes`, das die Vorlaufzeit des
Gastgebers übersteuert. Dazu kommt eine dritte Termin-Benachrichtigung.

- **Neuer Abschnitt in `clean-inbox`** — "Vorlaufzeit (booking lead time): per person, or per
  Terminart": `manage-booking-availability` für die Vorlaufzeit *einer Person*,
  `manage-model` auf `0-348` für die *einer Terminart* (`null` = keine Übersteuerung, sonst
  gewinnt sie). Die Führerscheinkontrolle ist die System-Terminart `driving-licence-check` —
  gefunden wird sie über eine Liste von `0-348`, nicht über einen Slug-Filter: filterbar sind
  nur `category` und `is_active`.
- **System-Terminarten sind für dieses eine Feld schreibbar.** Sonst unveränderlich (Slug,
  Label, Kategorie hängen an Code), aber `min_notice_minutes` und `is_active` gehen durch —
  jedes weitere Feld im selben `update` lässt den ganzen Aufruf scheitern.
- **Der Operator-Buchungsweg ignoriert die Vorlaufzeit.** Wird eine Führerscheinkontrolle
  ohne Mitarbeiter im Scope gebucht (Buchungspanel der Disposition), fällt das Notice-Fenster
  weg: Slots darin sind sichtbar und buchbar, während sie in der Mitarbeiter-App verborgen
  bleiben. Ein Slot ist für den Operator also nie "zu kurzfristig".
- **Geschäftszeiten-Abschnitt korrigiert** — nur die *Zeiten* fallen auf die Inbox zurück, die
  Vorlaufzeit nie: ohne persönliche Einstellung gilt der Systemwert von 240 Minuten. Eine
  Änderung der Geschäftszeiten verschiebt keine Vorlaufzeit.
- **`meeting.owner_assigned`** ergänzt in `clean-inbox` (Kanäle) und im Navigator
  (`using-alluvo-operator`): feuert, wenn jemand **anderes** einen Termin auf den Operator
  bucht oder verschiebt. Bewusst still, wenn der Eigentümer selbst gehandelt hat, bei
  Terminen, die nicht `Scheduled` sind, und bei KI-Buchungen (`meeting.agent_booked`) — mit
  diesen dreien ist die Liste der Termin-Benachrichtigungen vollständig.
- **Neuer Navigator-Eintrag** für "Vorlaufzeit für eine Terminart setzen" — weder
  `manage-settings` noch `manage-booking-availability`, sondern die Terminart selbst.

### Changed — 2026-08-19 `fields` verzeiht falsche Namen, Record-ID-Parameter haben Synonyme (alluvo#4085)

Ein geratener Feldname bricht einen Lesecall nicht mehr ab. Der Navigator
(`using-alluvo-operator`) erklärt jetzt, was stattdessen zurückkommt — und warum eine
fehlende Spalte kein leerer Wert ist.

- **Alias statt Fehler in `fields`** — `search-model` und `query-model` (Wurzel-`fields`
  ebenso wie jede `include[].fields`-Ebene) schreiben die bekannten Fehlgriffe um: am Vertrag
  `start_date`/`end_date` → `valid_from`/`valid_until` und `contract_number` → `identifier`,
  an der Abwesenheit → `starts_at`/`ends_at`, dazu `personnel_number` → `employee_number` und
  `contact_name` → `full_name`. Jede Umschreibung wird als `ℹ️ Note`-Zeile ausgewiesen.
- **Ein weiterhin unbekanntes Feld ist eine Warnung** — es fällt aus der Projektion und kommt
  als `⚠️ Unknown field(s) requested: [...] — omitted from the result.` samt gültiger
  Feldliste zurück. Daraus die neue Leseregel im Navigator: erst den Warnblock lesen, bevor
  aus einer fehlenden Spalte "nicht erfasst" wird.
- **Hart scheitern nur noch zwei Formen** — kein einziges der angefragten Felder existiert am
  Modell, oder die unbekannten Namen sind **Relations**namen (dann `get-model` statt engerer
  Projektion). `get-model-schema` (`context: list`) bleibt der günstigere Weg, ist aber keine
  Vorbedingung mehr — kein defensiver Schema-Call vor jedem Read.
- **Neuer Abschnitt "Addressing a record across tools"** — `id` / `record_id` / `model_id` /
  `subject_id` bzw. `model_type` / `record_type` / `subject_type` sind jetzt Synonyme: ein Tool
  füllt einen von ihm deklarierten, leer gelassenen Parameter aus dem gesendeten Synonym.
  Reines Umbenennen, kein Wert wird umgedeutet — geschrieben wird weiterhin der Name, den das
  Tool deklariert.
- **`enrich-contacts-from-activities/references/mcp-recipes.md`** — der Hinweis
  "`subject_type`/`subject_id`, NOT model_type/model_id" an `get-timeline` war zu streng und
  nennt jetzt die Synonyme.

### Changed — 2026-08-19 `manage-settings` bekommt `describe`, `group` wird optional (alluvo#4083)

Die Feld-Dokumentation von `manage-settings` steht **nicht mehr in der Toolbeschreibung** —
sie wird jetzt auf Anfrage über die neue Aktion `describe` geliefert. Wer eine Einstellung
ändert, muss die Gruppe vorher lesen, statt sich auf eine mitgelieferte Feldliste zu verlassen.

- **Neuer Abschnitt im Navigator** (`using-alluvo-operator`) — "Reading a settings group
  before you change it": `get` / `describe` / `update` als die drei Aktionen, `describe` als
  statische Doku ohne Settings-Recht, `get` als Tenant-Daten. Dazu die Regel, vor jedem
  `update` erst `describe` (oder `get`) zu rufen — gepaarte Felder wie
  `candidate_requirements` ↔ `soft_requirements` widersprechen sich sonst.
- **`group` ist optional — aber nur für `describe`.** `manage-settings(action: "describe")`
  ohne Gruppe listet, welche Gruppen Langform-Doku haben und welche nicht (eine Gruppe ohne
  Prosa ist trotzdem real; `get` und `update` funktionieren auf ihr). Für `get` und `update`
  bricht der Call mit einer Fehlermeldung ab, die alle gültigen Gruppen nennt.
- **`onboard-new-employee` (Schritt 2g, `pension_providers`)** — die Behauptung
  "`manage-settings` hat keinen `confirmed`-Parameter" war falsch: der Parameter existiert,
  gilt aber ausschließlich für `candidate_flow_prompts`. Auf `contract` wird er ignoriert und
  `update` schreibt sofort — das Ja des Operators muss also **vor** dem Call fallen. Der
  `describe`-Pfad für die Feldliste steht jetzt daneben.
- **`build-automation-agent`** — der feldnahe Pfad auf `candidate_flow_prompts` nennt
  `describe` mit; die Paarungs-Warnung lebt dort und nicht mehr in der Toolbeschreibung.

Ohne Skill-Änderung, der Vollständigkeit halber: `manage-framework-contract` hat sechs
Parameter-Beschreibungen dazubekommen (keine Schema-Änderung), und `manage-task` /
`manage-ticket` liefern Validierungsfehler jetzt als echte JSON-RPC-Fehler statt als Text mit
`Error managing task:` / `Error managing ticket:` — auf diese Präfixe matcht kein Skill.

### Added — 2026-08-19 Tags: tenant-weites Vokabular (`0-443`) und `tags` am Automation-Agenten (alluvo#4080)

Datensätze lassen sich erstmals frei taggen — bisher war die Antwort auf "wie kennzeichne ich
das?" immer ein Custom Field mit fester Optionsliste.

- **Neuer Modelltyp `Tag` (`0-443`)** — das tenant-weite Tag-Vokabular, voll les- und
  schreibbar über die generischen Modell-Tools (`query-model` / `search-model` / `get-model` /
  `manage-model` / `delete-model`). Schreibbar sind `name` und `color`
  (`gray`, `blue`, `indigo`, `purple`, `success`, `warning`, `danger`); `slug` wird beim
  Speichern aus `name` abgeleitet und ist bewusst **nicht** schreibbar.
- **`tags` am Automation-Agenten** — `manage-automation-agent` `create`/`update` nimmt jetzt
  `tags: [...]`: eine flache Liste von Tag-**Namen**, die den bisherigen Satz **ersetzt**
  (sync, nicht append) und unbekannte Namen **selbst anlegt** — kein Nachschlagen, kein
  Vorab-Anlegen. `[]` löscht alle. `get` liefert die aktuellen `tags` mit.
- **Nur Agenten sind taggbar.** `Agent` (`0-400`) ist derzeit das einzige Modell mit Tags; ein
  `tags`-Feld an einem anderen Modelltyp ist stillschweigend kein Feld — dort bleibt das
  Custom Field die richtige Antwort. In `build-automation-agent` und `using-alluvo-operator`
  ausdrücklich so dokumentiert, damit die Skills es nicht anderswo anbieten.
- **Zwei Fallstricke dokumentiert:** Umbenennen oder Löschen eines Tags wirkt auf **alle**
  Datensätze mit diesem Tag (tenant-weit) — gehört in die Vorschau; und `tags` ist eine
  Relation, keine Spalte: es taucht in keiner Spaltenliste auf, `get-model-schema` weist es
  aber aus und die Schreibpfade beachten es. Gelesen kommt zusätzlich eine
  `tags_colors`-Begleitmap (Name → Farbe) zurück.

### Changed — 2026-08-19 Agentenverwaltung: `manage-agent-prompt`, `candidate_flow_prompts` jetzt zweistufig (alluvo#4095)

Die MCP-Oberfläche für Agenten deckt erstmals mehr als Automation-Agenten ab. Bisher sahen die
Skills nur die 5 Automation-Agenten; die 4 konversationellen und die Task-Agenten waren über
MCP unsichtbar.

- **Neues Tool `manage-agent-prompt`** — zuständig für **konversationelle und Task-Agenten**
  (`list`, `get`, `set-instructions`, `set-blocks`, `attach-baustein`, `detach-baustein`,
  `reorder-bausteine`, `enable`, `disable`, `list-flow-sections`, `set-flow-section`,
  `reset-flow-section`). Automation-Agenten sind dort lesbar, jeder Schreibzugriff wird mit
  Verweis auf `manage-automation-agent` abgelehnt. Kein `create`/`delete`. `get` liefert den
  **komponierten Prompt abschnittsweise** (Tier, Label, Quelle, editierbar) — der einzige Weg
  zu sehen, was ein Agent tatsächlich sagt.
- **`candidate_flow_prompts` schreibt nur noch mit `confirmed: true`** — das ist die
  Bruchstelle. Ein `update` ohne das Flag gibt eine Vorschau zurück und **schreibt nichts**.
  `get` bleibt frei. Es ist die einzige Settings-Gruppe mit dieser Absicherung.
- **Acht statt sechs Bewerber-Flow-Abschnitte** — neu `agent_persona` (der allererste Satz des
  Prompts: wer der Agent ist und für welche Firma er schreibt) und `hard_rules` (was er nie
  zusagen oder verraten darf: Lohn, Prämien, Firmenwagen, Fahrtkosten, Unterkunft,
  Vertragskonditionen).
- **Zweistufigkeit an den Live-Prompt-Pfaden** — jeder Prompt-Write an einem konversationellen
  Agenten und jeder Flow-Abschnitt braucht `confirmed: true` und liefert sonst einen **Diff des
  komponierten Prompts**. Task-Agenten und `enable`/`disable` bleiben einstufig.
- **Flow-Abschnitte liegen pro Mandant, nicht pro Agent** — eine Änderung schreibt den Prompt
  jedes konversationellen Agenten um, dessen Flow den Abschnitt rendert. `list-flow-sections`
  nennt die Mitbetroffenen unter `shared_with`; die Skills sagen es dem Operator vor dem
  Schreiben.
- **Baustein-Semantik unterscheidet sich je Tool** — `manage-automation-agent` synchronisiert
  die ganze Menge über `instruction_block_ids`, `manage-agent-prompt` arbeitet inkrementell und
  `reorder-bausteine` sortiert nur um, hängt nie ab.
- **`Agent` (`0-400`) und `AgentRun` (`0-441`) sind read-only sichtbar** —
  `query-model`/`get-model`/`search-model` funktionieren, `manage-model` create/update nicht.
- Betroffen: **`build-automation-agent`** (neuer Abschnitt zur Zuständigkeitsteilung, Terms,
  `candidate_flow_prompts` auf acht Abschnitte und zweistufig), **`using-alluvo-operator`**
  (Navigator: neue Fähigkeit, veraltete „nur im Studio"-Aussage korrigiert), **`clean-inbox`**
  (Abgrenzung: der Vapi-Telefonassistent ist kein Agent-Record und bleibt bei
  `update-vapi-instructions`).

### Changed — 2026-08-19 Erstattungen: `grand_total` statt `amount`, `title` als Bezeichner (alluvo#4100)

Die Erstattungs-Oberfläche hat sich an drei Stellen gedreht, die die Skills über MCP lesen.

- **`approve-stundenfreigabe`** — der Abschnitt „reimbursement review" sagte
  „`amount` ist in EUR, niemals Cent" und ließ damit offen, dass `amount` gar nicht die Summe
  ist. Der auszuzahlende Betrag ist **`grand_total`** (Tagegelder, Transport, Belege, Positionen
  *und* der manuelle Zuschlag zusammengerechnet); `amount` ist nur dieser **manuelle Zuschlag**
  („Manueller Zuschlag") und ist auf jeder Auslage aus der Mitarbeiter-App `0` — wer ihn zitiert,
  meldet „0,00 €" für echtes Geld. Beide weiterhin in EUR, nie Cent.
- **Der Bezeichner ist `title`, nicht `purpose`.** `title` ist abgeleitet und nie leer
  („Stadt Köln · 14.08.2026" / „Reisekosten Köln · 03.–05.08.2026"); `search-model` auf `0-20`
  gibt ihn als Identitätsspalte zurück. `purpose` ist auf jeder beleggetriebenen Auslage NULL.
  Weil `title` keine Spalte hinter sich hat, lässt sich darauf **nicht** filtern oder sortieren.
- **Filter- und Sortierliste ergänzt.** Die fünf Chips sind `status`, `employee_id`, `type`,
  `needs_clarification`, `authorization_status`; zusätzlich filterbar sind u. a. `grand_total`,
  `amount`, `assignment_id`, `approver_id`, `authorized_by_id`, `payout_method`, `approved_at`,
  `paid_at`, `destination`, `end_date`. Warnung dazu: `start_date`/`end_date` setzen **nur
  Reisekosten** — darauf zu filtern oder zu sortieren wirft jede Auslage still aus der Liste.
  Für „die neuesten" nach `created_at` sortieren, das ist auch die Default-Ordnung.
- **Belege sind nur als Relation erreichbar.** `ReimbursementReceipt` (`0-26`) steht nicht auf
  der MCP-Allowlist — `search-model`/`query-model` auf `0-26` werden abgewiesen. Der Weg ist
  `query-model` auf `0-20` mit `include: { receipts: … }` (`title`, `vendor_name`,
  `document_date`, `amount_gross`). Auch beim Beleg ist `title` das Label, nicht `vendor_name`.
- **Doppelte Belege werden gewarnt, nicht blockiert.** Neu dokumentiert im Beleg-Abschnitt: die
  Extraktion prüft jeden Upload gegen die eigenen Belege der letzten 120 Tage (identische Datei
  per Hash, sonst gleiches Belegdatum + gleicher Bruttobetrag, geschärft durch die Belegnummer).
  Der Treffer ist eine überschreibbare Warnung **am Upload**, nicht am Datensatz: es gibt kein
  Duplikat-Flag auf `0-20` und keine MCP-Oberfläche dafür.

### Changed — 2026-08-19 Bewerber-WhatsApp-Agent: K.O.-Kriterium Einsatzumgebung, Leitungsausnahme entfernt (alluvo#4079)

Die Code-Defaults der Kandidaten-Prompt-Sections haben sich geändert — die sechs Feldnamen und
das `manage-settings`-Verhalten nicht, wohl aber der Inhalt, den ein Operator beim `get` sieht.

- **`build-automation-agent`** — der Abschnitt zu `candidate_flow_prompts` beschrieb
  `candidate_requirements` als „harte Deal-breaker **mit numerischen Schwellen**". Das ist seit
  dem neuen **K.O.-Kriterium 7 (ausgeschlossene Einsatzumgebungen)** unvollständig: Es greift
  erst, wenn jemand *alle* Einsatzumgebungen ausschließt, in die überlassen wird (Pflege:
  Altenheim UND Krankenhaus; Pädagogik: Kita) — ein einzelner Ausschluss bleibt bewusst kein
  K.O. und wird nur im Profil festgehalten. Entsprechend heißt die „beide Felder tragen dieselben
  Zahlen"-Regel jetzt „dieselben Regeln, numerisch wie qualitativ" — hart in
  `candidate_requirements`, weich in `soft_requirements`, immer gemeinsam ändern.
- **Die Ausnahme für Leitungs-/Führungsrollen ist raus.** PDL, stellv. PDL, WBL, Heimleitung und
  nicht-bettennahe Fachrollen (QM, Hygiene) laufen durch dieselben Gates wie alle anderen,
  inklusive 3-Schicht-K.O. Der Skill kann das jetzt erklären, statt eine Ausnahme zu
  beschreiben, die es nicht mehr gibt.
- **Neuer sichtbarer Baustein.** Jeder Tenant hat einen deaktivierten `0-442`-Baustein
  „Ausnahme für Leitungs-/Führungsrollen (archiviert)" mit dem Wortlaut der drei entfernten
  Passagen. Beide Baustein-Stellen des Skills sagen jetzt, was das ist — und dass ein Baustein
  **additiv unterhalb der Precedence** rendert: bloßes Anhängen holt das alte Verhalten *nicht*
  zurück, dafür müssten zusätzlich `candidate_requirements` + `qualification_profile` angepasst
  werden.
- **`using-alluvo-operator`** — die Routing-Zeile zum Bewerber-Flow nennt „Regeln, numerisch wie
  qualitativ" statt „Schwellen" und leitet die Frage nach dem Archiv-Baustein auf denselben
  Skill.

### Changed — 2026-08-19 automatisches Personalbedarf-Matching abgeschaltet (alluvo#4082)

Das autonome Matching eines `StaffingDemand` (`0-415`) liegt hinter dem Pennant-Flag
`App\Features\AutomaticDemandMatching` und ist **standardmäßig aus** — der Shortlist schlug
Kandidaten vor, die sich selbst als nicht verfügbar gemeldet hatten, und übersah die fachlich
passende Person, weil höherwertige Nachbarrollen nicht mitgesucht wurden. Vier Skills
beschrieben bis hier einen automatischen Folgeschritt, den es so nicht mehr gibt.

- Solange das Flag aus ist, entstehen zu einem Bedarf **keine** `StaffingDemandMatch`-Zeilen
  (`0-416`), **kein** „Personalbedarf prüfen"-Task, **kein** „Anschlusseinsatz prüfen"-Task,
  **keine** vorbereitete Kandidaten-Vorschlagsmail und in Slack **kein** „⏳ Matching läuft"-
  Platzhalter bzw. „✅ Matching abgeschlossen"-Antwort (die Bedarfs-Karte im Kanal bleibt) —
  also auch kein Thread, in dem „biete 1 und 2 an" beantwortet werden könnte. Ein Bedarf wird
  außerdem **nicht mehr automatisch auf `NotCoverable`** gesetzt; er bleibt in seinem
  Eingangsstatus, i. d. R. `Qualified`.
- **`intake-personalbedarf`** — der Satz „Matching läuft automatisch" ist raus. Neuer Schritt 6
  „Find the candidates yourself": aktiv selbst suchen statt auf einen Vorschlag warten, mit den
  offenen Wegen (`→ match-bench-to-clients`, `→ bench-check`, `search-model` auf `0-126`, der
  Matching-Arbeitsplatz) und der Ansage, dem Operator **keine** kommende Vorschlagsmail zu
  versprechen. Die Scoring-Hinweise (Level, Fachrichtung) bleiben — sie beschreiben jetzt
  ausdrücklich, was der Arbeitsplatz auf Anfrage rechnet.
- **`match-bench-to-clients`** — vorangestellter Hinweis, dass eine leere `0-416`-Liste der
  Normalfall und **kein** Befund „niemand passt" ist; die Abschnitte zu Vorschlagsmail und
  „Anschlusseinsatz prüfen" gelten nur noch für Zeilen, die tatsächlich existieren.
- **`head-of-disposition`** — „Personalbedarf prüfen"-Tasks sind **nicht** der Arbeitsvorrat;
  der Rückstand sind die offenen `0-415` selbst. Ein Bedarf wird danach beurteilt, ob jemand
  **gesucht** hat, nicht ob eine Shortlist da ist.
- **`bench-check`** — Schritt 6 prüft die Tasks weiterhin, liest ihr Fehlen aber nicht mehr als
  „kein passender Bedarf": stattdessen die offenen `0-415` selbst gegenprüfen, bevor auf
  `→ profilvertrieb` / `→ prospect-companies` ausgewichen wird.
- **Nicht** betroffen und weiterhin nutzbar: der Matching-Arbeitsplatz (`/staffing/matching`,
  `/staffing/company-matching`) samt gemeinsamer Scoring-Engine sowie das nächtliche
  `EmployeeStaffingOpportunity`-Scoring (`0-126`) — beides ist nicht hinter dem Flag.

### Changed — 2026-08-19 Fuhrpark-Prüfarten, Fristen nach Datum ODER Kilometern (alluvo#4056)

`VehicleInspection` (`0-69`) stand in den Skills als ein Halbsatz („trägt HU/UVV-Daten") und
beschrieb damit einen Stand, den es nicht mehr gibt.

- **`onboard-new-employee`** — Schritt 2d bekommt einen eigenen Block zu `0-69`. Die Prüfart
  zerfällt in **zwei Familien**: gesetzlich und rein datumsgebunden (`hu`, `au`, `sp_uvv`, mit
  `certificate_number`) und Werkstatt-Services ohne Plakette (`inspection_small`,
  `inspection_large`, `oil_change`, `air_conditioning`) — ein einzelner Wert „Inspektion"
  existiert nicht mehr. Dokumentiert sind die beiden neuen Felder `defects` (Mängel gehören
  dorthin, nicht mehr in den Freitext `notes`) und `next_due_mileage` (absoluter Zielstand, nur
  bei `inspection_small` / `inspection_large` / `oil_change` — `air_conditioning` ist trotz
  Werkstatt-Familie datumsgetrieben), das Ableiten leerer Fristen aus Intervall (24/12 Monate
  bzw. 15.000/30.000 km, ein gesetzter Wert gewinnt immer), `due_on` als Monatsletzter, und dass
  über MCP immer die **absoluten** Werte geschrieben werden — die relative Eingabe („in 15.900 km
  oder 648 Tagen") ist eine Formular-Komponente.
- **Fälligkeit ist der schlechtere der beiden Befunde**, nicht mehr das Datum allein: `overdue` /
  `due_soon` (1 Monat oder 1.000 km) / `upcoming` (2 Monate oder 2.500 km) / `ok`. Ein
  vielgefahrenes Fahrzeug kann bei einem Service überfällig sein, dessen Datum noch Monate weg
  ist — beim Melden von Fristen also `next_due_mileage` gegen den aktuellen Kilometerstand lesen.
- **Zwei Datensätze je Prüfart sind der Normalfall:** eine abgeschlossene Prüfung (mit
  `performed_on`, Frist noch in der Zukunft, keine offene ihrer Art) legt die Folgeprüfung
  automatisch als offenen Datensatz an. Die Skill sagt jetzt, dass der Operator sie **nicht**
  selbst anlegt und dass die *jüngste* Zeile je Art die lebende Frist ist. Ebenfalls neu benannt:
  ein `mileage_at_inspection` auf einer durchgeführten Prüfung schreibt selbst eine
  VehicleMileageReading (`0-424`, `source: operator`) — kein zweiter Datensatz von Hand.
- **`using-alluvo-operator`** — neuer Routing-Eintrag („HU / TÜV / AU / UVV eintragen /
  Inspektion erfassen / welche Prüfungen sind fällig") und `0-69` in der Fuhrpark-Zeile der
  Skill-Übersicht.

### Changed — 2026-08-19 Tagesübernahme in die Folgeperiode + Unterschriftenblock ohne Handzeichen (alluvo#4055)

Zwei Änderungen an der Stundenfreigabe, die beide beschreiben, was ein Operator mit einer
Periode tun kann, die nicht fertig wird.

- **`approve-stundenfreigabe`** — neuer Abschnitt „A trailing open day no longer strands the
  period". Der Zeitraum (`0-426`) trägt jetzt die Aktion `push_open_days_to_next_period`
  („Offene Tage in die Folgeperiode schieben"): sie verschiebt die **Grenze** zwischen beiden
  Perioden — `date_until` der laufenden und `date_from` der folgenden wandern zurück, die offenen
  Tagesdatensätze werden umgehängt — und die verkürzte Periode läuft danach durch dieselbe
  Kaskade wie eine Schlussunterschrift (Tätigkeitsnachweis wird erzeugt, Beleg geht an die
  zuletzt freigebende Person). Dokumentiert sind alle fünf Sichtbarkeits-Guards (`PendingClient`;
  mindestens ein offener Tag, wobei freie und abwesenheitsgedeckte Tage nicht zählen; mindestens
  ein bereits freigegebener Tag; offene Tage als zusammenhängender Lauf am Periodenende; eine
  Folgeperiode, die `Upcoming` ist oder noch nicht existiert und lückenlos anschließt), dazu
  `timesheets.edit` und dass verschobene Tage ihre IDs, Korrekturen und Feldhistorie behalten.
  Bisher kannte die Skill als einzigen Hebel `revoke_release`.
- **Diese Aktion ist nicht MCP-ausführbar.** Sie trägt kein `McpExposed`, also weist
  `manage-record-action` sie auf `0-426` ab — die Fähigkeits-Box der Skill sagt das jetzt
  ausdrücklich, damit sie nicht angeboten wird. In derselben Box korrigiert: die beiden
  Link-Aktionen („Tätigkeitsnachweis öffnen", „Zur Vermittlung") sind sehr wohl über
  `manage-record-action` erreichbar, geben aber nur die URL zurück und schreiben nichts.
- **`approve-stundenfreigabe`** — neuer Absatz „Unterschriftenblock". Eine Freigabe mit Namen,
  aber ohne gespeichertes Handzeichen druckt den Namen jetzt kursiv an der Stelle der Marke plus
  eine Provenienz-Zeile („Digital im Kundenportal freigegeben" · „Freigegeben per Fristablauf —
  keine Unterschrift" · neutral „Freigabe erfasst ohne gespeicherte Unterschrift", wenn der Kanal
  nicht belegt ist). Vorher stand dort ein leeres Kästchen über einem gedruckten Namen, was sich
  wie ein unterschriebenes Dokument *nicht* liest. Mit der Regel, die neutrale Zeile nie zu einer
  Kanal-Aussage aufzuwerten — der Nachweis ist Beleg nach § 11 AÜG.
- **`using-alluvo-operator`** — zwei neue Routing-Einträge („Zeitraum wird nicht fertig / offener
  Tag blockiert alles" und „Unterschriftsfeld leer / Name in Schreibschrift") sowie die
  Präzisierung, dass `revoke_release` die eine *per MCP ausführbare* Schreib-Aktion ist.

### Changed — 2026-08-19 Profileinträge sind je Ausgabefläche ausblendbar (`hidden_on` / `ProfileSurface`) (alluvo#4030)

Lizenzen, Ausbildungen, Sprachen sowie Fachbereiche und Fortbildungen tragen jetzt eine
Sichtbarkeits-Angabe je Ausgabefläche. `hidden_on` listet die Flächen, auf denen ein Eintrag
**nicht** erscheint — `profile` (öffentliches Profil, Kundenportal, Profil-PDF) und
`contract` (AÜV, Einzel-AÜV). `null`/`[]` heißt überall sichtbar, Bestandsdaten ändern ihr
Verhalten also nicht. Über `manage-model` schreibbar auf `0-183` (ContactEducation), `0-185`
(ContactLanguage) und `0-186` (ContactLicense).

- **`triage-data-quality`** (Schritt 3g, jetzt „hide an entry instead of deleting it"): die
  volle Recipe — Modelltypen, beide Flächen, und die Leitregel **ausblenden statt löschen**
  bei einer falsch geparsten oder unpassenden Qualifikation (`delete-model` bleibt für eine
  schlicht falsche Zeile). Dazu die Grenzen: die primäre Ausbildung und jede von der
  Einsatzrolle als erforderlich geführte Lizenz lassen sich **nicht** aus dem Vertrag
  ausblenden (§ 12 AÜG), `get-profile` zeigt die Personalakte und nicht die Kundensicht (der
  Flag steht dort gar nicht drin — über `get-model`/`query-model` zurücklesen), und die auf
  der Pivot-Zeile liegende Variante bei Fachbereichen/Fortbildungen ist über MCP nicht
  schreibbar.
- **`manage-contract-lifecycle`** (Schritt 3): der Qualifikationsblock im AÜV druckt bewusst
  weniger als das Profil. Neben `hidden_on: ["contract"]` fallen jetzt auch Lizenzen außerhalb
  ihres Gültigkeitsfensters und widerrufene (`revoked_at`) Lizenzen heraus — vorher druckten
  sie sich als gültige Berechtigung. Eine fehlende Berechtigung ist deshalb zuerst ein Blick
  auf Gültigkeitsdatum und Widerruf, nicht auf den Vertrag.
- **`profilvertrieb`**: ein dünner Profilabschnitt kann eine Entscheidung sein statt einer
  Datenlücke — vor dem „Auffüllen" den Flag zurücklesen. Der `staffing_roles`-Block ist davon
  nicht betroffen. Und: „das gehört da nicht rein" ist `hidden_on: ["profile"]`, kein Löschen.
- **`onboard-new-employee`**: `hidden_on` als Geschwister zu `position` und
  `profile_visibility` bei den CV-Schreibvorgängen — eine unsichere Qualifikation aus einem
  CV-Import wird ausgeblendet, nicht verworfen.

### Changed — 2026-08-19 Personennamen kommen im Tenant-Format aus den MCP-Tools (alluvo#4031)

`Employee/Contact/User/Candidate/CompanyContact::titleField()` liefert jetzt `display_name`
statt `full_name` — also die Tenant-Einstellung `name_display_format` statt roh
"Vorname Nachname". Die Skills gingen bisher stillschweigend von der rohen Form aus.

- **Neuer Querschnitts-Abschnitt „Reading a person's name out of a tool result"** in
  `using-alluvo-operator`: welche Tools formatierte Labels liefern (`get-model`,
  `search-model`, `query-model`, `bulk-manage-model` für Relations-Labels und Suchtreffer;
  `manage-task`, `get-open-tasks`, `get-timeline`, `get-field-history`, `manage-apps` für
  Subjekt-/Datensatz-Labels; `manage-association` für verknüpfte Personen), die vier Werte
  (`FirstLast` · `LastFirst` · `LastFirstNoComma` · `FirstLastInitial`), und dass der rohe
  Name unverändert als `full_name` im selben Payload liegt. Dazu die Regeln: das Label nie in
  Vor-/Nachname zerlegen und nie gegen die Eingabe des Operators diffen ("Müller, Anna" ist
  dieselbe Person wie "Anna Müller"); für die Bestandteile `first_name`/`last_name` lesen (bei
  Employee/Candidate am verknüpften Kontakt); `display_name` ist ein Accessor und damit weder
  filter- noch sortierbar (Freitextsuche bleibt unberührt). Die Einstellung selbst:
  `manage-settings`, Gruppe `brand_identity`, Feld `name_display_format` — der früher
  dokumentierte Wert `"LastOnly"` existiert nicht.
- **`manage-contract-lifecycle`** ("Whose name the contract prints as customer signer"): das
  Dokument druckt weiterhin den rohen vollen Namen — ein im Tool-Ergebnis umgestelltes Label
  ist kein Beleg dafür, dass der Vertrag den falschen Namen druckt.
- **`build-automation-agent`**: `{{…employee.display_name}}` in Platzhaltern rendert ebenfalls
  das Tenant-Format ("Müller, Anna" auf einem `LastFirst`-Tenant) — für eine Anrede stattdessen
  `…employee.contact.first_name`.

Verträge, PDFs und Payroll-/DATEV-Exporte sind bewusst unverändert.

### Changed — 2026-08-18 Automation-Agenten: `capabilities` (execute/propose) ersetzt `enabled_tools` (alluvo#3815)

`manage-automation-agent` hat ein vereinheitlichtes Fähigkeiten-Modell bekommen; `build-automation-agent`
baute Payloads noch mit dem alten `enabled_tools`-Array. Jetzt:

- **`capabilities` statt `enabled_tools`** in allen Schritten (Vorschau, `create`, `update`,
  Referenzbeispiel, Output): ein Objekt `{key: "execute" | "propose"}`. `execute` = läuft
  unbeaufsichtigt als Tool im eigenen Lauf; `propose` = darf als Schritt auf der Run-Card
  eines Posteingang-Deployments vorgeschlagen werden (ob der Schritt dann pausiert oder von
  selbst läuft, bleibt pro Schritttyp fest — die Tool-Description überzeichnet das als „immer
  freigabepflichtig"). Ausgelassener Schlüssel = aus.
  `capabilities` ist auf `update` ein Voll-Ersatz — vorher `get` lesen. `enabled_tools` ist ein
  veralteter Alias (wird auf `{name: "execute"}` gemappt, ignoriert sobald `capabilities`
  mitgeschickt wird) und taucht in `get`/`list` nicht mehr auf.
- **`describe-tools` listet jetzt den vollen Katalog** (~35 Einträge, snake_case): Lauf-Tools
  (`query_employee_sick_days`, `query_model`, `manage_model` **(WRITE)**, …) **und** alle
  Klassifizierer-Schritte (`create_note`, `send_ticket_reply`, `close_ticket`, …), jeweils mit
  unterstützten Modi. Read-Tools sind `[execute]`-only, die meisten Schritte `[propose]`-only,
  `create_task`/`manage_model` beides. Die Validierungsmeldungen (unbekannter Schlüssel → Liste
  gültiger Schlüssel; nicht unterstützter Modus) sind dokumentiert.
- **Neuer Abschnitt „Capabilities"** in `build-automation-agent` mit der Ceiling-Regel für
  Deployments: die Agent-Map ist eine Obergrenze (Deployment darf nur herabstufen), Schlüssel
  ohne Agent-Meinung liefert das Deployment selbst — leere Deployment-Map = Default-Set
  (`create_task`, `create_note`, `manage_model`, `enrich_relationship`,
  `create_staffing_requirement`) in `propose`.
- **`enabled_steps` auf `deploy` ist zur Laufzeit derzeit wirkungslos** — wird validiert,
  gespeichert und in Preview/`list-deployments` zurückgegeben, aber der Laufzeit-Filter liest
  nur `AgentDeployment.capabilities`, das `deploy` nicht schreibt. Jedes über MCP angelegte
  Deployment läuft auf dem Default-Set. Als alluvo#4027 gemeldet; die Skill sagt das dem
  Operator und verweist für alles jenseits des Default-Sets auf den Capability-Picker der
  Deployment-Form im Agent Studio („Einsatzorte").
- Navigator (`using-alluvo-operator`): Automation-Zeile nennt `capabilities`/`describe-tools`.

### Changed — 2026-08-18 Bausteine, Baustein-Reihenfolge und die Bewerber-Flow-Prompts sind über MCP steuerbar (alluvo#4017)

`build-automation-agent` kannte die Prompt-Ebene eines Agenten bisher gar nicht — weder die
System-Blöcke noch die mandanteneigenen Bausteine noch die neuen Bewerber-Flow-Abschnitte. Jetzt:

- **Neuer Abschnitt „Prompt building blocks"** in `build-automation-agent`: die feste
  Kompositions-Reihenfolge (Datum → System-`blocks` → Rangfolge → `instructions` →
  Deployment-Anweisungen → Bausteine), die acht Block-Schlüssel mit deutschen Labels
  (`describe-tools` listet sie; vier sind als `(always on — not deselectable)` markiert), und
  die **tatsächliche** Render-Regel für Automation-Agenten: `blocks` weggelassen oder `[]` →
  **kein** System-Block rendert; erst ab einem wählbaren Block (`brand-voice`, `formality`,
  `icp`, `selling-profile`) rendern `agency-location` und `ai-disclosure` mit. Die
  Tool-Description behauptet für den Weglassen-Fall das Gegenteil — als alluvo#4026 gemeldet,
  die Skill dokumentiert das Verhalten aus dem Composer/Test.
- **Bausteine (`InstructionBlock`, `0-442`) sind über die generischen Modell-Tools erreichbar**
  (`query-model`/`get-model`/`manage-model`, Felder `name`, `content`, `is_active`; zweistufig
  wie jeder Write). Anhängen über `manage-automation-agent` `create`/`update` mit
  `instruction_block_ids` — **Voll-Ersatz (sync), nicht Anhängen**, und die
  **Array-Position ist die Render-Reihenfolge** (`sort_order`, identisch mit dem Studio).
  Vorher `get` lesen und die komplette Liste zurückschicken. Ein deaktivierter Baustein bleibt
  angehängt, rendert aber nicht. Deployment-Bausteine sind Studio-only (`deploy` hat keinen
  `instruction_block_ids`-Parameter). `list`/`get` sehen nur Automation-Agenten — Chat-,
  Voice- und Bewerber-WhatsApp-Agenten bleiben über MCP unsichtbar (alluvo#4016).
- **Neue Settings-Gruppe `candidate_flow_prompts`** in `manage-settings` (sechs Felder:
  `company_model`, `candidate_requirements`, `qualification_profile`, `sector_focus`,
  `soft_requirements`, `sector_vocabulary`) mit den drei Regeln, die ein Operator hören muss:
  `null` = Code-Default (zurücksetzen heißt `null`, nie `""`); `candidate_requirements` und
  `soft_requirements` tragen dieselben Schwellenwerte und werden immer zusammen geändert; es
  ist der Live-Prompt eines Agenten, der gerade mit echten Bewerbern schreibt — erst `get`,
  dann `update`. Dazu `company_city`/`company_state` (Gruppe `general`) als Quelle des
  Blocks „Standort der Agentur".
- `using-alluvo-operator`: Automation-Eintrag und Quick-Decision-Guide um „Baustein anlegen /
  anhängen / Reihenfolge", „was der Bewerber-Agent auf WhatsApp sagt" und „Standort der Agentur"
  ergänzt — der Telefonassistent bleibt bei `clean-inbox`.

### Changed — 2026-08-18 Foto-Pflicht beim Kilometerstand ist eine Tenant-Einstellung (alluvo#4022)

Was seit #4015 als Produktverhalten in den Skills stand, ist jetzt ein Schalter — und er
steht per Default **aus**:

- **Neues Feld in `manage-settings`, Gruppe `fleet`: `require_mileage_photo`** (bool, Default
  `false`). Es entscheidet **nur**, ob ein Fahrer eine `request_mileage`-Anfrage in der
  Mitarbeiter-App ohne Tacho-Foto absenden darf. **Aus** heißt nicht „kein Feld": die App
  bietet den Upload weiterhin an und speichert ein freiwillig angehängtes Foto, sie blockiert
  das Absenden nur nicht. Der Operator-Pfad (Formular oder `manage-model` auf `0-424`) ist in
  **beiden** Zuständen foto-optional — die Einstellung berührt ihn nie.
- **`onboard-new-employee` (Schritt 2d) sagt nicht mehr, das Foto sei Pflicht.** Die Aussage
  ist jetzt konditional, mit dem ausdrücklichen Hinweis, die Einstellung zu lesen, bevor man
  einem Fahrer eine Pflicht ankündigt. Auch die Herkunftsregel ist korrigiert: `source:
  employee` garantiert einen Beleg nur bei eingeschalteter Einstellung — ob eine Ablesung
  belegt ist, steht in `has_odometer_photo`, nicht in `source`.
- **Der Fuhrpark-Einstellungsblock führt jetzt drei Felder** statt zwei, samt Beispielaufruf.
  Nebenbei korrigiert: `mileage_request_due_days` ist **nicht** MCP-only — alle drei Felder
  sind auch unter *Einstellungen → Apps → Fuhrpark* pflegbar.
- **`using-alluvo-operator`** führt `require_mileage_photo` in der Feldliste der Gruppe
  `fleet` und routet Formulierungen wie „Foto beim Kilometerstand verpflichtend machen",
  „Fahrer sollen den Tacho fotografieren", „Foto-Pflicht abschalten" dorthin.

### Changed — 2026-08-18 Tacho-Foto an der VehicleMileageReading (`0-424`) (alluvo#4015)

Ein Kilometerstand kann jetzt ein Foto des Tachos tragen — und auf dem Weg, der für die
Beweisführung zählt, trägt er es zwingend:

- **`0-424` hat ein Feld mehr: `odometer_photo`** (Einzeldatei, jpeg/png/heic/heif, max
  12 MB). Wie die Schadensfotos an `0-67` ist es Web-Formular/Mitarbeiter-App-only — über
  `manage-model` **nicht** befüllbar. `onboard-new-employee` (Schritt 2d) nennt das jetzt
  ausdrücklich, damit die Skill nicht anbietet, was der MCP-Pfad nicht kann.
- **Antwortet der Fahrer über die Mitarbeiter-App auf eine `request_mileage`-Anfrage, ist
  das Foto Pflicht** (und die App weist eine Zahl **unter** dem letzten bekannten Stand ab).
  Daraus folgt die Regel, die beide Skills jetzt führen: eine Ablesung mit `source: employee`
  hat einen Beleg, eine mit `source: operator` in aller Regel nicht — relevant überall dort,
  wo der Kilometerstand gegenüber Leasing begründet werden muss. Wer die Zahl vom Fahrer
  braucht, fragt sie per Action an, statt sie selbst einzutragen und die Anfrage damit ohne
  Beleg zu schließen.
- `using-alluvo-operator` führt dieselbe Unterscheidung in der Fuhrpark-Routing-Zeile.

### Changed — 2026-08-18 CompanyContact Big Bang: `0-361` ist weg, die Verknüpfung IST der Ansprechpartner (alluvo#3969)

Der Umbau der Portal-Zugehörigkeit fasst drei Tabellen zu **einer** Zeile pro (Firma, Kontakt)
zusammen — und räumt damit zwei Flächen ab, auf die die Skills sich verlassen haben:

- **`CompanyContactPerson` (`0-361`) existiert nicht mehr.** Der Model-Type wurde entfernt;
  `query-model`, `count-model`, `search-model` und `manage-model` gegen `0-361` schlagen fehl.
  Ersatz ist **PortalMembership (`0-430`)** (Slug `company-contacts`) — eine Zeile pro (Firma,
  Kontakt), die zugleich CRM-Verknüpfung, Eintrag in der Kontaktliste des Kundenportals und
  Portal-Mitgliedschaft ist. Sie filtert direkt auf `company_id`, `contact_id`, `status` und
  `grants.role`. `account-research`, `head-of-sales`, `prospect-companies`, `enroll-outreach`
  und `profilvertrieb` lesen die Ansprechpartner einer Firma jetzt darüber.
- **Die Actions `list-as-portal-contact-person` / `unlist-as-portal-contact-person` sind
  entfallen**, ebenso das `is_contact_person`-Konzept dahinter: die Kontaktliste im Kundenportal
  zeigt schlicht *alle* mit der Firma verknüpften Kontakte. Damit ist „jemanden als
  Ansprechpartner listen" ein gewöhnlicher `manage-association`-Schreibvorgang (Contact `0-105` ↔
  Company `0-3`, Label `Ansprechpartner`), der die Mitgliedschaft anlegt bzw. löscht;
  `function_title` wird danach per `manage-model` auf `0-430` gepflegt.

`approve-stundenfreigabe` beschreibt den Zugang deshalb nicht mehr in drei, sondern in **zwei**
Stufen (verknüpft → login-fähig): Sichtbarkeit in der Kontaktliste sagt nichts über Zugang aus,
und Zugang bleibt allein `send-portal-invitation` / `assign-portal-roles`. Verknüpfen verschickt
weiterhin nichts und vergibt keine Rolle; **Detach ist kein Lockout** — es entfernt die ganze
Mitgliedschaft samt Rollen, reversibel aussperren geht nur über `assign-portal-roles`
(`portal_access_active: false`). `using-alluvo-operator` routet die Frage „Kontakt im Portal
listen / freischalten" entsprechend um.

### Added — 2026-08-18 Gespräche selbst eröffnen: `manage-ticket` `create` per Mail und in der Mitarbeiter-App (alluvo#3942)

`manage-ticket` hat eine neue Action **`create`** — die erste Möglichkeit, aus alluvo heraus ein
Gespräch zu *eröffnen* statt nur auf eines zu antworten. Zwei Modi über `mode`, beide zweistufig
(Preview ohne `confirm` → Versand mit `confirm: true`), genau wie `reply` und `forward`:

- **`mode: "email"`** — verschickt eine neue Mail über den verbundenen E-Mail-Kanal einer Inbox und
  eröffnet dafür ein E-Mail-Ticket. Pflicht: `inbox_id`, `contact_id`, `subject`, `body`; `priority`
  optional (Default `medium`). Der Empfänger ist **immer ein bestehender Contact** — freie
  Adressen werden abgelehnt (Identity-Root), also den Kontakt vorher über `search-model` auf `0-105`
  auflösen oder anlegen. Fehlt der Inbox ein aktiver E-Mail-Kanal, meldet das schon der Preview.
- **`mode: "employee_app"`** — eröffnet ein Gespräch mit einem Mitarbeiter in dessen
  Self-Service-App. Pflicht: `employee_id`, `subject`, `body`. **Kein Mailversand**; die Nachricht
  erscheint unter „Nachrichten" plus In-App-Benachrichtigung und Web-Push. Kein `inbox_id` —
  das Ticket landet automatisch in der konfigurierten Mitarbeiter-Support-Inbox, der einzigen, in
  der die App danach sucht. Voraussetzung ist ein App-Zugang des Mitarbeiters.

Das neue Ticket ist ein ganz normaler Vorgang: Ersteller und Owner ist der Operator, Status
`waiting_on_user`, und die Antwort landet **im selben Ticket**. `clean-inbox` beschreibt das jetzt
als eigenen Abschnitt (inklusive `[TKT-…]`-Betreffpräfix und Abgrenzung zum Akquise-Mailpfad),
`onboard-new-employee` bekommt einen Schritt 7 für die Rückfrage an den Mitarbeiter (Abgrenzung zum
digitalen Personalfragebogen, der die Antworten selbst zurückschreibt), `profilvertrieb` und
`enroll-outreach` stellen klar, wann welcher der drei Mailwege gilt (Sequenz vs. 1-zu-1-Pitch mit
Profilblock und Tracking vs. schlichtes, im Ticket nachverfolgtes Gespräch), und
`using-alluvo-operator` führt „jemanden proaktiv anschreiben" als eigenen Job.

**`manage-ticket` bleibt bewusst nicht automationsfähig** (kein `#[AutomationSafe]`): ein
headless Automations-Agent eröffnet keine Gespräche mit Menschen. Jeder `create`-Aufruf hat einen
Operator dahinter, der den Preview freigibt.

### Fixed — 2026-08-18 `manage-shift-plan` heißt jetzt `manage-shift-schedule`; `list-model-types` nennt die deutschen Begriffe (alluvo#3966)

Der Englisch-Rename der Identifier hat ein Tool umbenannt, das die Skills namentlich aufrufen —
ein harter Bruch, kein Alias: **`manage-shift-plan` → `manage-shift-schedule`** (Klasse
`ManageShiftScheduleTool`, Titel „Manage Shift Schedule"). Der alte Name existiert auf der
MCP-Oberfläche nicht mehr. Alle 25 Nennungen in sechs Skills sind umgestellt:
`build-dienstplan`, `manage-contract-lifecycle`, `head-of-disposition`, `record-absence`,
`build-automation-agent`, `using-alluvo-operator`.

**Am Verhalten hat sich nichts geändert.** Actions (`create`, `list`, `add-shift`,
`update-shift`, `remove-shift`, `publish`), Parameter, die zweistufige Bestätigung, der harte
§-3-ArbZG-Block über 10 h/Tag, die weichen Warnungen (§ 5 Ruhezeit, § 7 Wochengrenze,
§ 9/§ 10 Sonntag), die menschlich freigebbare Verfügbarkeitsprüfung
(`availability_override_reason`) und der Nachtrags-Flag `past_date_acknowledged` sind
unverändert. Es war ausschließlich der Name.

**`list-model-types` hat eine vierte Spalte „Also known as".** Jeder Modelltyp führt dort seine
Aliase — das deutsche Vokabular, das ein Disponent tatsächlich sagt, abgebildet auf den
englischen Typ: Dienstplan/Schichtplan → SchedulePeriod, Stundenzettel/Tätigkeitsnachweis →
Timesheet, Rahmenvertrag/AÜV → FrameworkContract, Konkretisierung/Einsatzvertrag →
AssignmentContract, Einsatzmitteilung → Assignment, Beleg → ReimbursementReceipt, Reisekosten →
Reimbursement, Personalfragebogen → Employee, Ansprechpartner → Contact, Kunde/Auftraggeber →
Company. `using-alluvo-operator` beschreibt das jetzt als übergreifende Regel: den Typ aus der
Alias-Spalte lesen, statt ihn aus einem ähnlich klingenden englischen Label zu erraten.

Die Zuordnung ist **bewusst locale-unabhängig** — die Aliase aller Sprachen werden vereinigt,
ein englischer Begriff greift also auch in einer deutschen Sitzung und umgekehrt. Die Spalte ist
**dünn besetzt**: nur zehn Typen führen heute Aliase, alle anderen zeigen `—`. Ein Strich sagt
nichts darüber aus, ob der Typ der richtige ist. Es sind Aliase des **Typs**, keine Spitznamen
eines einzelnen Datensatzes. Die Modelltyp-**IDs sind unverändert** (`0-2` Employee, `0-3`
Company, `0-105` Contact …) — die Spalte kommt hinzu, sie ersetzt nichts.

**Ebenfalls unverändert und daher ohne Skill-Änderung:** die Action-Werte `manage_einsatz` und
`send_konkretisierung`, alle `ExtractionKind`-Werte (`beleg`, `reisekosten`, `stundenzettel`,
`dienstplan`), die `EmployeeAppFeature`-Werte und die Settings-Keys. Englisch wurden nur die
Identifier; persistierte und von außen aufgerufene Strings sind geblieben. Deutsch ist auch aus
MCP nicht verschwunden — die Tool-Beschreibungen führen den deutschen Begriff weiter neben dem
englischen, und genau davon lebt die Zuordnung von Operator-Vokabular auf ein Tool. Skills reden
also weiterhin Deutsch mit dem Disponenten.

### Fixed — 2026-08-17 Abweichungsgrund ist ein pflegbarer Katalog, kein Enum mehr (alluvo#3950)

Die Kategorie, mit der ein Mitarbeiter beim Feierabend eine Abweichung vom Dienstplan erklärt, war
eine feste Liste aus acht Werten. Sie ist jetzt ein **vom Mandanten pflegbares Modell**
(`ShiftDeviationReason`): Zeilen lassen sich anlegen, umbenennen, umsortieren und deaktivieren —
in den Einstellungen und über die generischen Modell-Tools. Ein eigenes Tool gibt es bewusst nicht.

**Was die Skills bisher falsch gesagt haben.** `approve-stundenfreigabe` und `head-of-disposition`
haben die acht Codes als geschlossenes Enum (`TimesheetDeviationReason`) beschrieben. Dieses Enum
ist gelöscht. Die acht Codes existieren weiter — als **vorgesetzte Systemzeilen**, nicht als die
Liste. Beim Berichten heißt das: den Katalog zur Laufzeit lesen, statt die acht zu nennen, und
einen Code, der nicht mehr im Katalog steht, als deaktivierte oder umbenannte Zeile lesen, nicht
als Datenfehler.

**Was gleich geblieben ist — und deshalb keine Altdaten kaputtgehen.**
`timesheet_days.deviation_reason_code` speichert weiterhin den `code`-String, ohne Fremdschlüssel.
Auch der Freitext behält seine Untergrenze (10 Zeichen, zwei Wörter).

**Vier Regeln, die der Server durchsetzt** — `approve-stundenfreigabe` beschreibt sie jetzt
ausführlich: `code` ist nach dem Anlegen unveränderlich; eine Systemzeile ist umbenennbar und
deaktivierbar, aber **nicht löschbar** (wer sie loswerden will, deaktiviert sie); `direction`
(`over`/`under`/`both`) ist die fachliche Regel, die verhindert, dass ein zu langer Tag als „früher
gegangen" auf einem vom Kunden unterschriebenen § 17c-AÜG-Nachweis landet — nie aufweichen, nur um
einen Code auswählbar zu machen; und ein umbenanntes Label ändert rückwirkend, wie vergangene Tage
gelesen werden.

**Modelltyp nicht hart verdrahten.** Der Typ wird über `list-model-types` aufgelöst — das bleibt
so, auch wenn die id inzwischen feststeht (`0-440`), weil ein Katalog, der jederzeit umgezogen
werden kann, keine Skill-Beschreibung wert ist, die diese Auflösung umgeht.

### Fixed — 2026-08-17 Rechnungs-Bankkonto: pflegbar über MCP, verknüpfbar nur in der App (alluvo#3932)

Die eigenen Bankkonten des Verleihers — die, auf die der Kunde seine Rechnung zahlt — sind neu
über MCP les- und schreibbar. Zwei Dinge daran führen sonst in die Irre.

**1. Zwei Modelltypen heißen „Bankkonto".** `list-model-types` zeigt `0-323` schlicht als
**„Bank Account"** (die Konten der Agentur) und `0-21` als **„Employee Bank Account"** (das
private Konto des Mitarbeiters, auf das Lohn und Auslagen gehen). Wer „Bankkonto" über den
Namen auflöst, landet auf `0-323` — und legt im schlimmsten Fall die private IBAN eines
Mitarbeiters in der Zahlungsempfänger-Liste des Mandanten ab. `onboard-new-employee` nennt
jetzt ausdrücklich `0-21`, `manage-contract-lifecycle` ausdrücklich `0-323`.

**2. Das Konto ist pflegbar, die Verknüpfung nicht.** `manage-model` auf `0-323` legt Konten an
und korrigiert sie (`label`, `account_holder_name`, `payment_system`, `bank_name` sind Pflicht;
welches Detailfeld zusätzlich Pflicht wird, entscheidet `payment_system` — `sepa` → `iban`,
`ach` → `routing_number` + `account_number`, `bacs` → `sort_code` + `account_number`, `wire` →
`swift` + `account_number`). **Welches** Konto an einem Vertrag hängt, ist über MCP dagegen
nicht setzbar: `manage-framework-contract` / `manage-assignment-contract` führen
`bank_account_id` bewusst nicht und weisen das Feld mit einem Fehler zurück, und auf der Firma
(`0-3`) wird es still verworfen. Also: Konto über MCP anlegen, Auswahl am Vertrag in der App —
und das auch so sagen, statt einen Schreibversuch zu starten.

Dazu, was die Skills bisher nicht wussten:

- **Die IBAN kommt auch hier maskiert zurück** (`DE89********3000`). Die Maskierung greift pro
  Feldname an der MCP-Grenze, nicht pro Modell — das eigene Konto ist davon genauso betroffen
  wie das des Mitarbeiters. Eine Übertragung also nicht per Rücklesen prüfen. Der Titel eines
  `0-323`-Datensatzes ist sein `label`, nicht die IBAN.
- **`is_tenant_default` ist serverseitig exklusiv** und in **beide** Richtungen gesperrt: ein
  inaktives Konto lässt sich nicht als Standard setzen, und das aktuelle Standardkonto lässt
  sich nicht deaktivieren (*„The invoice fallback account must stay active"*). Erst das Flag
  auf das Nachfolgekonto umziehen, dann deaktivieren.
- **Die Auflösungskette** ist spezifisch-zuerst: Einsatzvertrag → Rahmenvertrag → Firma →
  Mandanten-Standard. Eine Ebene mit inaktivem oder gelöschtem Konto fällt durch, statt zu
  blockieren — ein nicht-Standard-Konto zu deaktivieren nimmt es damit überall auf einmal
  aus dem Verkehr.
- `company_id` auf `0-323` ist tot: nicht fillable, ein mitgesendeter Wert wird verworfen.

### Fixed — 2026-08-17 Dienstplan: Mitarbeiter-Änderungen brauchen eine Begründung — und der Vorschlag ist jetzt lesbar (alluvo#3915)

Zwei Dinge auf dem Mitarbeiter-Pfad, die `build-dienstplan` bisher nicht kannte.

**1. Begründungspflicht.** Jede Änderung eines Mitarbeiters an einem Dienstplan, der den Entwurf
verlassen hat (`published`, `locked`, `pending_approval`), wird ohne angegebene Begründung mit 422
auf dem Feld `reason` abgelehnt — Einzelschicht wie Ganzplan-Sync. Auf `draft` und `needs_revision`
ist das Feld optional: dort wird keine Change-Log-Zeile geschrieben, die Begründung hätte also
keinen Platz. Der Guard läuft **nach** allen anderen Ablehnungen (Periode nicht editierbar, harte
ArbZG-Findings, `max_hours`), also bedeutet diese Meldung: der Plan selbst war schon in Ordnung.

- Die Begründung hängt **pro Änderung** an der Change-Log-Zeile (`reason`, `reason_by_user_id`) und
  erscheint als *„(Grund: …)"* an der jeweiligen Zeile des §-11-Abs.-2-Satz-4-Digests — pro Zeile,
  nicht pro Digest. Eine dreimal verschobene Schicht behält drei Begründungen.
- **Operator-Schreibzugriffe erfassen keine Begründung.** `manage-shift-plan` hat keinen solchen
  Parameter (`availability_override_reason` / `past_date_acknowledgement_reason` sind andere Gates).
  Die Skills sagen darum explizit: eine Zeile ohne *„(Grund: …)"* ist eine Operator-Änderung, kein
  Mitarbeiter, der sich die Begründung gespart hat — und „ich trage es eben für ihn ein" ist keine
  Hilfe, weil dann gar nichts erklärt wird.
- `build-automation-agent`: `{{reason}}` und `{{reason_by_user_id}}` sind neue Platzhalter auf dem
  `0-433`-Trigger, bei `record_source = external_panel` gefüllt, bei Operator-Zeilen leer.

**2. Der geparkte Vorschlag ist lesbar — die Begründung dazu nicht.** Die Box „Du kannst den
Vorschlag über MCP nicht lesen" war überholt (alluvo#3660 ist behoben, alluvo#3827). `get-model` auf
`0-110` liefert jetzt `shift_proposal_diff_table` (eine Zeile pro **materieller** Änderung: Art,
Datum, aktuell → vorgeschlagen), `pending_proposal_updated_at` und `pending_proposal_version`. Damit
ist `data.proposal_version` selbst zu lesen, statt es beim Operator zu erfragen — die
Stale-Prüfung muss also nicht mehr übersprungen werden. Bei `query-model` nur, wenn in `fields`
benannt.

Nicht lesbar bleiben `pending_shift_proposal` (Rohdaten, in keinem Schema) und
**`pending_proposal_reason`**: die Begründung, die der Mitarbeiter angeben *musste*, wird gespeichert
und nirgends angezeigt — kein Infolist-Eintrag, kein MCP-Feld, keine Benachrichtigung
(API-seitige Lücke alluvo#3925). Das Skill dokumentiert das tatsächliche Verhalten: Diff vorlesen,
Begründung erfragen, und den Vorschlag nie als „kam ohne Erklärung" darstellen.
### Fixed — 2026-08-17 Dienstplan: veröffentlichte Schicht ist stornierbar, nicht löschbar — plus zwei Benachrichtigungs-Schalter (alluvo#3924)

`manage-shift-plan` `remove-shift` hat sich in zwei Punkten geändert, die `build-dienstplan`
bisher wörtlich anders beschrieben hat.

**1. Harte Löschung wird abgelehnt, sobald der Dienstplan draußen ist.** `cancel: false` (bzw.
weggelassen) wird verweigert, wenn die Periode der Schicht `published`, `locked` oder
`pending_approval` ist — der Mitarbeiter hält eine §-11-Abs.-2-Satz-4-Einsatzmitteilung über
diesen Tag, der Kunde sieht ihn im Portal, also muss eine stornierte Zeile zurückbleiben (sie ist
die Audit-Spur, aus der Änderungs-Digest, Tätigkeitsnachweis und Umbesetzungs-Historie lesen).
Der Fehler kommt als Validierung auf `shift_id`. Nichts hebelt ihn aus — kein `confirmed`, keine
Berechtigung, kein Grund. Auf `draft`, `provisional`, `needs_revision`, `rejected` und ohne
Periode löscht es weiterhin. Faustregel im Skill: **hat der Plan den Entwurf verlassen, ist
`cancel: true` die richtige Operation** — eine Löschung dort nicht als „saubere" Variante
anbieten.

**2. Zwei optionale Booleans, beide mit Default `true`.**

| Parameter | Wirkung bei `false` |
|---|---|
| `notify_owner` | der Einsatzvertrag-Owner bleibt aus dem ~15-Minuten-Dienstplan-Digest raus |
| `notify_on_site_contact` | der Ansprechpartner vor Ort — ein **Kundenkontakt** — wird nicht angeschrieben |

- Der §-11-Digest an den **Mitarbeiter** ist aus beiden Schaltern bewusst nicht erreichbar: eine
  gesetzliche Pflicht, keine Operator-Präferenz. Der bisherige Satz „es gibt keinen Schalter, der
  die Benachrichtigung unterdrückt" ist darum jetzt nach Empfängern aufgeteilt, statt pauschal zu
  gelten — sonst hätte das Skill einen telefonisch geklärten Wechsel weiterhin als zwingend
  kundenwirksam dargestellt.
- Beide Schalter gelten **pro Aufruf** und nur auf `remove-shift`; `add-shift` / `update-shift`
  haben sie nicht. Die Tenant-Einstellung `notify_on_site_contact_on_shift_changes` gated den
  Versand unabhängig weiter — `true` kann also nichts erzwingen, was der Tenant abgestellt hat.
- Der Web-Bestätigungsdialog von `cancel_shift` bietet exakt dieselben zwei Schalter. Die Notiz,
  dass `cancel_shift` über `manage-record-action` (`0-111`) **nicht** erreichbar ist, bleibt
  richtig und wird dadurch wichtiger: die Schalter gibt es auf beiden Oberflächen, aufrufbar ist
  nur eine.
- Nebenbei korrigiert: ein Owner, der seinen **eigenen** Dienstplan ändert, hat bisher auch die
  kundenseitige Notiz verschluckt. Jetzt fällt nur seine eigene Mail weg, der Ansprechpartner
  wird informiert.

### Added — 2026-08-17 `approve-stundenfreigabe`, `head-of-disposition`: der Abweichungsgrund ist jetzt Kategorie **und** Freitext (alluvo#3917)

Wer einen vom Dienstplan abweichenden Tag per „Feierabend" abschließt, beantwortet ab sofort
**zwei** Hälften, beide Pflicht: eine Klassifikation (`deviation_reason_code`, Enum
`TimesheetDeviationReason`) und den eigenen Satz (`deviation_reason`). Vorher war es ein einzelnes
Freitextfeld, das jedes nicht-leere Zeichen durchließ — auf Prod stand deshalb „Abweichung: ."
auf einem unterschriebenen Tätigkeitsnachweis.

`approve-stundenfreigabe` beschreibt den Ablauf jetzt vollständig:

- **Wann das Gate feuert** — der Tag hat Plan *und* Erfassung und beide unterscheiden sich um
  **mehr als 5 Minuten** (`DayDeviation::TOLERANCE_MIN`, dieselbe Definition wie `deviation_flag`).
  Ein `extra`-Tag (ohne Plan) und ein `missing`-Tag (ohne Erfassung) werden **nie** gefragt.
- **Die Optionen sind richtungsgefiltert** — ein länger gelaufener Tag bietet
  `stayed_longer` / `handover_delayed` / `understaffed`, ein kürzerer `left_early` /
  `sent_home_early` / `started_late`; `break_differs` und `other` gelten in beide Richtungen. Ein
  Code aus der falschen Richtung wird abgelehnt, ein langer Tag ist also nie „früher gegangen".
- **Qualitätsregel auf dem Freitext** — mindestens 10 Zeichen und zwei Wörter aus je zwei oder
  mehr Buchstaben (`ExplanationQuality`). `..........`, `----------` und `1234567890` fallen
  durch. Ausdrücklich aufgenommen: **niemals einen Platzhalter vorschlagen oder erzeugen**, der
  die Regel nur erfüllt — der Satz ist die Schilderung des Mitarbeiters und geht an den Kunden.
- Beide Gates (§ 4 ArbZG und Abweichung) kommen in **einem** Roundtrip zurück; ein erneuter
  Abschluss räumt beide Felder wieder ab, sobald der Tag nicht mehr abweicht.
- **Ausgabe-Format** — wo der Grund gerendert wird (Tätigkeitsnachweis-PDF, Kundenportal,
  Mitarbeiter-Woche), steht `Kategorie – Satz` statt nur dem Satz. Ein vor der Änderung
  abgeschlossener Tag hat keine Kategorie und druckt weiterhin nur den Satz — kein Defekt.
- Der Snapshot der Abschluss-Zeile führt die beiden Felder jetzt mit auf (neben
  `planned_minutes`), und ein Tag mit Abweichungsgrund wird von
  `taetigkeitsnachweis_show_empty_days: false` **nicht** weggefiltert.

Neu für die Auswertung: `TimesheetDay` (`0-427`) hat mit `deviation_reason_code` eine
**filterbare** Enum-Spalte — genau der Grund, warum die Kategorie existiert. „Wie oft mussten
Leute länger bleiben?" ist damit ein `query-model` mit `aggregate: {function: "count"}` statt
einer Freitext-Lesearbeit; `head-of-disposition` führt das als Leadership-Frage samt der zwei
Vorbehalte (ältere Tage tragen keinen Code, die Werte sind richtungsgebunden).

Nichts an der Freigabe-Blocker-Semantik ist gelockert, und es gibt weiterhin **keinen
MCP-Schreibpfad** auf den Tagesabschluss (`0-422` bleibt von der Allowlist ausgenommen).

### Fixed — 2026-08-17 Stundennachweis: `TimesheetStatus::Draft` heißt jetzt `Upcoming` (alluvo#3845)

Der Enum-Fall `Draft` existiert nicht mehr. Er heißt `Upcoming` (Wert `upcoming`, Label
„Anstehend") — die Woche ist vollständig, nur die Freigabe hat noch nicht begonnen, was „Entwurf"
falsch nahelegte. `draft` ist kein gültiger `TimesheetStatus`-Wert mehr: ein `query-model`- oder
Saved-View-Filter, der ihn sendet, trifft ins Leere und eine so gebaute Backlog-Zahl liest still
Null.

`approve-stundenfreigabe` und `head-of-disposition` sprechen daher durchgehend von `Upcoming` —
Saved-View-Liste, der Hub-Refresh der Perioden-Header, die KPI „Offene Wochen"
(`Upcoming` + `PendingClient`), die nächtliche Promotion nach `PendingClient` und die
Backlog-Zählung. Beide Skills warnen zusätzlich explizit vor dem alten Wert.

**Kein pauschales Umbenennen:** `draft` kleingeschrieben bleibt an anderen Stellen korrekt — die
Dienstplan-Periode (`SchedulePeriod`, `0-110`) und der Reimbursement-Status heißen weiterhin so.
Die Treffer in `build-dienstplan`, `manage-contract-lifecycle`, `clean-inbox`, `call-summary` und
`match-bench-to-clients` sind unberührt geblieben.
### Added — 2026-08-17 `approve-stundenfreigabe`, `using-alluvo-operator`: Ansprechpartner-Listung ist eine MCP-Action — und vergibt weiterhin keinen Portalzugang (alluvo#3893)

Einen Kontakt auf die kundenseitige **Ansprechpartner-Liste** einer Firma zu setzen, ging bisher
nur über die UI (ein Bespoke-Endpunkt, über MCP nicht erreichbar). Jetzt sind es zwei Record-Actions
auf dem Contact (`0-105`), über `manage-record-action` `operation: "execute"`:
`list-as-portal-contact-person` und `unlist-as-portal-contact-person`.

- **`company_id` im `data`-Objekt.** Wird automatisch gesetzt, wenn genau eine Firma des Kontakts
  in Frage kommt, und ist Pflicht, sobald es mehrere sind. Eine Firma, für die die Richtung nicht
  zutrifft, wird abgelehnt — nicht stillschweigend ignoriert.
- **Die beiden schließen sich per Sichtbarkeit gegenseitig aus.** Es erscheint immer nur die
  zutreffende: wer überall gelistet ist, hat kein `list-…`, wer nirgends gelistet ist, kein
  `unlist-…`. Deshalb erst `operation: "list"` auf dem Kontakt — die fehlende Action ist die
  Antwort auf „ist der schon gelistet?", kein Fehler.
- **Listung ist kein Zugang.** Listen vergibt weder Login noch Rolle und verschickt nichts;
  Entfernen entzieht weder Zugang noch Rolle noch Login. Das alte UI-Label „Im Portal freischalten"
  hat genau das fälschlich suggeriert — die Skills sagen jetzt explizit, dass sie es nicht bedeutet.
  Zugang bleibt `send-portal-invitation` / `assign-portal-roles`.
- Die Skills trennen die Kundenportal-Stufen jetzt sauber: **Firmenkontakt → als Ansprechpartner
  gelistet → login-fähig** (aktive Membership **mit** rollentragendem Grant). Stufe 2 und 3 sind in
  beide Richtungen unabhängig. Eine aktive Membership **ohne** Rollen-Grant hält keinen Login — auf
  realen Daten ist das die Mehrheit der Kontakte, „hat eine Membership" ist also kein Zugangsbeleg.
- Der Lese-Pfad ist unverändert, aber jetzt benannt: eine lebende `CompanyContactPerson`-Zeile
  (`0-361`) für das Paar (Firma, Kontakt) **ist** die Listung und ist das, was die beiden Actions
  schreiben. Rollen, Reichweite und Anmeldung stehen weiterhin ausschließlich auf `PortalMembership`
  (`0-430`).
### Fixed — 2026-08-17 §11-Einsatzmitteilung: beendeter Einsatz ist wieder nachmeldbar, die Automatik schweigt (alluvo#3912)

Die Skills beschrieben bisher genau die falsche Asymmetrie: manuell sei ein beendeter Einsatz
gesperrt, automatisch werde trotzdem gesendet. Beides ist umgedreht — eine einzige Vorbedingung
(`AssignmentNotificationEligibility`) beantwortet jetzt für jeden Weg, ob die §11-Abs.-2-Satz-4-AÜG-
Mitteilung rausgehen darf.

- **Manuell** verlangt `send_assignment_notification` nur noch `stage: won` plus einen Vertrag, der
  nicht gescheitert ist (`cancelled`/`rejected`). `performed` ist erlaubt: auf einem Mehr-Einsatz-AÜV
  beschreibt der Vertragsstatus das Bündel, nicht die einzelne Scheibe. Ein **beendeter Einsatz ist
  ausdrücklich nachmeldbar** (Nachtrag) — eine versäumte §11-Mitteilung muss erreichbar bleiben,
  sonst ist die Compliance-Lücke dauerhaft unheilbar. Kein „das Fenster ist zu" mehr: den Nachtrag
  anbieten, sagen dass die Mitteilung verspätet ist, und erst nach Bestätigung senden.
- **Automatisch** wird nicht mehr gesendet, sobald der Einsatz vorbei ist — pro Einsatz, nicht pro
  Vertragsstatus, und für alle drei Wege (Auto-Versand bei Commissioning, spät hinzugefügter
  Einsatz, Client-Portal-Checkout). Der Skip wird geloggt, aber **nirgends in der UI angezeigt**:
  wenn ein Mitarbeiter „nie eine Mail bekommen hat", ist das bei einem beendeten Einsatz die
  Erklärung, und der Nachtrag die Abhilfe. „Beendet" ist ein Datumsvergleich in der Tenant-Zeitzone
  — ein heute endender Einsatz läuft noch, ein offener (ohne `end_date`) gilt nie als beendet.
- Weiterhin echte Blocker, jetzt klar benannt: unsignierter Vertrag, **stornierter Einsatz**,
  fehlender Mitarbeiter, fehlende Mitarbeiter-E-Mail.

Betroffen: `manage-contract-lifecycle` (Schritt 5 und 6 — inklusive `add_replacement`, das jetzt
dieselbe Statusreichweite hat wie die §11-Folgeaktion), `build-dienstplan` (Schritt 8) und
`record-absence` (Vertretung).

> Die Action-Beschreibung des MCP-Tools hinkt hier noch hinterher (sie nennt weiter
> `commissioned`/`performing` und weist `performed` ab) — als alluvo#3913 gemeldet. Die Skills
> dokumentieren das tatsächliche Verhalten und weisen auf die Abweichung hin.

### Fixed — 2026-08-17 Contact-Merge trägt Vertragsreferenzen mit — die Sperre aus #3903 gilt nur noch fürs direkte Löschen (alluvo#3909)

Nachtrag zum Eintrag darunter, der teilweise überholt ist. `Contact::mergeableRelationships()`
enthält jetzt `contract_recipients`, den Legacy-Spiegel `framework_contract_recipients` und
`assignments`. Damit wandern Empfänger-Zeilen und der Einsatz-Ansprechpartner **vor** dem Löschen
auf den behaltenen Kontakt — der Löschguard findet nichts mehr zu blockieren, und ein Merge geht
wieder durch, auch wenn die Dublette Hauptempfänger eines lebenden Vertrags ist. `preview-merge`
läuft damit ebenfalls wieder durch (es spielt denselben Ablauf in einer zurückgerollten
Transaktion durch).

`merge-duplicate-companies` beschreibt den Fall daher nicht mehr als blockiert: der Merge ist der
**empfohlene** Weg für die Vertrags-Dublette, statt erst per `recipient_contact_ids` bzw.
`manage_einsatz` `contact_id` von Hand umzuhängen. Was weiterhin blockiert, bleibt unverändert:
`mergeBlockingRelations` (beide Seiten tragen Employee und/oder Candidate) und
`MergeDataLossException` ohne `confirm_data_loss`.

**Neu erwähnenswert für den Disponenten:** waren **beide** Seiten Empfänger desselben Vertrags,
verwirft der Unique-Index die Zeile der Dublette. Hielt die das `is_primary`, setzt
`Contact::reconcileAfterMerge()` den Hauptempfänger neu — den verbliebenen Empfänger mit der
kleinsten `sort_order`, was auch eine **dritte Person** sein kann. Der Hauptempfänger ist der
Name, den ein unsignierter AÜV als Kunden-Unterzeichner druckt, also nach einem Merge die
betroffenen Verträge prüfen und `primary_recipient_contact_id` bei Bedarf setzen.
`manage-contract-lifecycle` und `using-alluvo-operator` sagen das jetzt.

**Unverändert:** das **direkte** Löschen (`delete-model` auf `0-105`) eines Kontakts, den ein
lebender Vertrag braucht, wird weiter abgelehnt — der Eintrag unten gilt dort vollständig. Auch
der Befund `dangling_contract_recipient` bleibt wie beschrieben (keine MCP-Oberfläche, kein
`Issue`-Record); `triage-data-quality` nennt jetzt zusätzlich den Merge als Auflösung, wenn die
verwaiste Empfänger-Zeile einen lebenden Zwilling derselben Person hat.

### Fixed — 2026-08-17 Kontakt-Löschung wird blockiert, solange ein lebender Vertrag den Ansprechpartner nennt (alluvo#3903)

Das Löschen eines `Contact` (`0-105`) kann ab jetzt **fehlschlagen**. Kein Tool, kein Parameter
und kein Schema hat sich geändert — aber ein Kontakt, der noch Empfänger eines Rahmen- oder
Einsatzvertrags ist (weder gelöscht noch `lost`/`cancelled`) oder Ansprechpartner eines lebenden
Einsatzes, wird nicht mehr gelöscht. Die Meldung nennt jeden Blocker konkret (`RV #72`,
`AÜV #685`, `Einsatz #2040`); der Ausweg ist immer, dort zuerst einen Ersatz zuzuweisen.
`is_test`-Kontakte und Verträge, die abgebrochen oder gelöscht sind, blockieren nicht.

**Das trifft auch die Kontakt-Dublette.** Ein Contact-Merge endet damit, die Dublette zu löschen,
und er re-pointet weder `contract_recipients` noch `assignments.contact_id` — beide stehen in
keiner Merge-Relationsliste. Also läuft der Merge in dieselbe Absage, inklusive `preview-merge`,
das denselben Ablauf in einer zurückgerollten Transaktion durchspielt. Alles läuft in **einer**
Transaktion: nichts bleibt halb zusammengeführt. `merge-duplicate-companies` beschreibt jetzt,
die genannten Verträge zuerst per `recipient_contact_ids` (ersetzt die **komplette** Liste) bzw.
`manage_einsatz` `contact_id` auf den behaltenen Kontakt zu ziehen und den Merge dann zu
wiederholen — und **niemals** „Dublette einfach löschen" als Ersatz anzubieten: dieselbe Sperre
greift, und die Historie wäre weg statt zusammengeführt.

Ebenfalls dokumentiert: der Altfall, den die Sperre verhindert. Ein gelöschter Empfänger behielt
seine `contract_recipients`-Zeile, war aber für **jeden** Leser unsichtbar — der Vertrag war
weder versendbar noch unterschreibbar („kein Empfänger mit E-Mail-Adresse"), obwohl ein Empfänger
zugewiesen aussah, und der unsignierte AÜV fiel auf den Hauptempfänger der Rahmenvereinbarung
durch, nannte also eine **andere Person** als Unterzeichner. Solche Verträge meldet die neue
Data-Quality-Regel `dangling_contract_recipient` auf `0-30` und `0-31`. Sie ist **kein** Issue
(`0-190`) — `query-model` findet sie unter keinem Filter; sie steht auf der Vertragsseite und im
Data-Quality-Dashboard. `triage-data-quality` sagt das jetzt, statt „nichts gefunden" zu melden.

### Added — 2026-08-16 `build-dienstplan`: Dienstplan veröffentlichen geht jetzt direkt über `manage-shift-plan` (alluvo#3850)

`manage-shift-plan` hat eine neue Action `publish` (`draft` → `published`). Wer einen Monat im
Chat baut, veröffentlicht ihn jetzt mit demselben Tool, statt über `manage-record-action` auf
`0-110` auszuweichen. Zweistufig wie jeder andere Write dort: Vorschau, dann `confirmed: true`.

Ziel ist entweder `schedule_period_id` — die `create`-Antwort druckt sie als **Schedule Period
ID**, Bauen und Freigeben bleiben damit ein Gespräch ohne Zwischen-Lookup — oder `assignment_id`,
das den einen Entwurf des Einsatzes auflöst. Bei mehreren Entwürfen wird **abgelehnt statt
geraten**; die Fehlermeldung nennt die Kandidaten-ids. Auf einer Periode, die nicht `draft` ist,
kommt eine lesbare Absage mit dem aktuellen Status, kein 500.

Der Weg über `manage-record-action` (`0-110`, `action: "publish"`) bleibt gültig — dieselbe
Action dahinter, dieselben Garantien: die Absage bei überlappendem Live-Dienstplan (ein Einsatz
hat höchstens einen live-Plan je Zeitraum) gilt unverändert und wird nie automatisch aufgelöst.
`0-110` bleibt für `manage-model` weiterhin read-only.

Ebenfalls in der Skill festgehalten, was das Veröffentlichen tatsächlich umlegt: Sichtbarkeit im
Kundenportal und beim Mitarbeiter, plus Aufnahme in die *committed* Pläne — erst ab da zählen die
Schichten als Konflikt für Doppelbuchung, §5-Ruhezeit und Wochenhöchstgrenze auf den **anderen**
Einsätzen. Verfügbarkeit und Soll-Minuten liefert ein Entwurf ohnehin schon. Benachrichtigt wird
weiterhin niemand, ein bereits gearbeiteter Monat ist also unkritisch.
### Fixed — 2026-08-17 `approve-stundenfreigabe`: ein abgeschlossener Tag ist vor dem geplanten Schichtende freigebbar (alluvo#3899)

Die Skill erklärte `running` als "warten, bis die Schicht vorbei ist". Das stimmt nicht mehr:
ein aktiver Tagesabschluss macht den Tag **unabhängig vom geplanten Ende** fällig. Wer um 11:35
Feierabend macht, obwohl der Plan bis 19:00 läuft, gibt die Stunden sofort frei, statt hinter
"Schicht läuft noch — kann erst nach Feierabend freigegeben werden" zu hängen.

Richtiggestellt: `running` heißt "heute, geplantes Ende noch offen **und** nicht abgeschlossen" —
ein abgeschlossener Tag kommt `selectable` ohne blockierenden Grund zurück. Ein **nicht**
abgeschlossener Tag verhält sich unverändert und wartet weiter auf sein geplantes Ende; ein
Zurückziehen des Abschlusses blockiert den Tag wieder. Nur die eigene Erklärung des Mitarbeiters
sticht den Plan, nie deren Fehlen — der Kunde kann also nach wie vor keine laufende Schicht
zeichnen.

Nichts dahinter ist gelockert: die §-4-ArbZG-Pausenprüfung und die Plan-Abweichungsprüfung laufen
danach, ein Abschluss, der seinen Tag nicht mehr trägt, wird weiterhin abgelehnt.

Ebenfalls nachgezogen: dieselben drei Verdikte (`not_closed`, `unsettled`, `running`) maskieren die
Ist-Zeiten im Kundenportal, ein abgeschlossener Tag ist dort also sofort sichtbar; die
Fristablauf-Freigabe liest denselben Tages-Gate; und der Navigator routet "die Schicht läuft noch /
der heutige Tag lässt sich nicht freigeben" jetzt als Tagesabschluss-Frage.

### Fixed — 2026-08-15 `approve-stundenfreigabe`: Die Timesheet-Suche (`search-model` auf `0-426`) findet jetzt Mitarbeiter, Personalnummer und Einsatzbetrieb (alluvo#3844)

`Timesheet` (`0-426`) hatte bis hierher **keine einzige** durchsuchbare Spalte. Ohne durchsuchbare
Spalte filtert die Suche nicht — sie war kein „findet nichts", sondern ein **No-op**, der jede
Zeile zurückgab. Ein `search-model` mit einem Namen bekam also die komplette (paginierte) Liste,
ohne Hinweis darauf, dass der Suchbegriff ignoriert wurde.

Ab jetzt matcht die Suche tokenisiert und case-insensitive über Mitarbeiter-Vorname
(`employee.contact.first_name`), -Nachname (`employee.contact.last_name`), Personalnummer
(`employee.employee_number`), Einsatzbetrieb (`assignment.assignmentContract.company.name`) und
dessen Aliasse (`…company.alternative_names`) — dieselbe Semantik wie die globale Suche, d.h.
`"Sabine Vogel"` trifft über zwei Spalten und `"UKD"` findet die Uniklinik über ihren Alias.

In der Skill festgehalten: der Einstieg „welche Zeiträume hat X" ist **ein** Aufruf — `search-model`
auf `0-426` mit Name oder Personalnummer. Der Umweg „erst Employee (`0-2`) auflösen, dann
`query-model` mit `employee_id`" ist damit hinfällig (ein `employee_id`-Filter bleibt richtig,
wenn die id schon vorliegt). Dazu die eine Einschränkung der Quick-Search: `q` allein liefert
id + Label, und das Label eines Zeitraums ist `Tätigkeitsnachweis <Name>` **ohne** den Zeitraum —
mehrere Perioden derselben Person sehen identisch aus. Vor dem Benennen eines Zeitraums in den
List-Mode wechseln (`limit` / `fields` / `filter_groups`) und `period_label`, `date_from` /
`date_until` und `status` lesen.

Nur Lesepfad — an der MCP-Reichweite ändert sich nichts: `0-426` bleibt read-only, `manage-model`
verweigert weiterhin jeden Schreibzugriff.

### Fixed — 2026-08-15 `approve-stundenfreigabe`, `using-alluvo-operator`, `head-of-disposition`, `build-dienstplan`, `record-absence`: Die Kundenfreigabe ist tagesgenau geworden — Teilabnahme, Rücknahme, laufende Schicht (alluvo#3834)

Eine Kundenfreigabe ist ab jetzt ein **Vorgang** (`TimesheetRelease`, `0-435`), kein Häkchen auf
dem Zeitraum: wer, wann, über welchen Kanal, mit welcher Unterschrift, plus ein Snapshot der
gezeichneten Werte je Tag. Ein Zeitraum kann mehrere tragen. Vier Verhaltensänderungen, die die
Skills bisher anders beschrieben haben:

1. **Eine Teilfreigabe sperrt nicht mehr den ganzen Zeitraum.** Gesperrt sind nur die
   freigegebenen **Tage**, und die Sperre gilt **pro Einsatz** — an einem offen gelassenen Tag
   erfasst und korrigiert der Mitarbeitende weiter. Vorher sperrte die erste Teilfreigabe die
   ganze Woche, ein fehlender Tag war danach unkorrigierbar.
2. **Ein Tag mit noch laufender Schicht ist nicht freigebbar** — weder von Hand vor Ort noch
   durch den Fristablauf.
3. **Eine Tagesfreigabe kann zurückgenommen werden**: neue Operator-Action `revoke_release` auf
   `TimesheetDay` (`0-427`) über `manage-record-action`, Pflichtfeld `reason`, Permission
   `timesheet_days.revoke_release`, nur solange der Zeitraum `Upcoming`/`PendingClient` ist. Die
   ursprüngliche Unterschrift bleibt in der Historie; der `status` des Zeitraums bewegt sich nicht.
4. **Fristablauf überschreibt keine menschliche Unterschrift mehr**, sondern gibt als eigener
   Vorgang genau die noch offenen Tage frei.

Geänderte MCP-Reichweite: `TimesheetDay` (`0-427`) und `TimesheetRelease` (`0-435`) sind neu auf
der MCP-Allowlist, `TimesheetDayRelease` (`0-436`) ist es nicht. Bei der Gelegenheit korrigiert:
die Skills behaupteten noch, `Timesheet` (`0-426`) sei nicht MCP-lesbar — es ist es (lesend), und
alle drei taugen als Automations-Trigger. Schreibend bleibt alles außer `revoke_release` gesperrt.

Im Kundenportal gibt der Kunde jetzt tageweise frei (optionale Tagesauswahl beim Bestätigen; die
alte Wochenprüfung „letzter Tag muss abgeschlossen sein" ist entfallen). Neu dokumentiert, weil es
die naheliegende Verwechslung ist: **`canRelease` („die Woche kann abschließen") gatet nichts,
`hasReleasableDay` („mindestens ein Tag ist jetzt unterschreibbar") ist die Bedingung für das
Freigabe-Steuerelement** — wer die beiden verwechselt, versteckt die Freigabe einer ganzen Woche
wegen eines offenen Tages. Die Sammelfreigabe gibt eine Woche ganz oder gar nicht frei, und Zeiten
noch nicht abgeschlossener Tage werden dem Kunden gar nicht geliefert.

Aus Tabelle/Infolist/Filter des Stundennachweises entfernt: `signer_name`, `client_channel`,
`client_confirmed_by_contact_id` — „wer hat unterschrieben" beantwortet jetzt der Freigaben-Tab
bzw. `0-435`. Neu als versteckte Spalten: `Diensttage gesamt` / `Freigegebene Diensttage`.
`client_confirmed_at` am Zeitraum heißt nur noch „jeder Tag ist freigegeben" und ist bei einer
Teilfreigabe leer. Der Tätigkeitsnachweis listet jede Freigabe einzeln auf. Und: ein
Zeitraum-Rebuild (z. B. nach einer Krankmeldung) friert bereits freigegebene Tage ein und
re-derived nur die offenen.

### Fixed — 2026-08-14 `approve-stundenfreigabe`, `record-absence`, `using-alluvo-operator`: Abwesenheitstage stehen standardmäßig **nicht** auf dem Tätigkeitsnachweis, und eine Krankheitswoche wartet nicht mehr auf den Mitarbeiter (alluvo#3831)

Zwei Änderungen an der Stundenfreigabe, beide aus demselben Produktionsfall (ein Tag ohne
erfasste Zeit wurde behandelt, als trüge er welche).

**1. Neues Setting `taetigkeitsnachweis_show_absence_days` — Standard `false`.** Les- und
schreibbar über `manage-settings` (Gruppe `time_tracking_hours_approval`) und pro
Kundenunternehmen über `manage-record-settings` (`0-3`, Key
`timesheet.taetigkeitsnachweis_show_absence_days`). Es entscheidet, ob Tage, an denen der
Mitarbeiter abwesend war (krank **und** Urlaub — jede Kategorie), überhaupt auf dem
§ 17c-Nachweis erscheinen. **Aus als Standard, anders als das Geschwister-Setting
`taetigkeitsnachweis_show_empty_days`** — der Entleiher bestätigt die bei ihm geleisteten
Stunden, und „Krank" auf einem Dokument, das zum Kunden geht, verrät ihm etwas über die
Gesundheit der Mitarbeiterin. Die Skills berieten hier bisher falsch: sie beschrieben die
„Krank"-Zeile als das, was der Kunde sieht, und kannten den Schlüssel gar nicht. Jetzt
dokumentiert: eigener Abschnitt in `approve-stundenfreigabe`, der Vorbehalt im „Krank"-Block
und im `record-absence`-Abschnitt, eine Routing-Zeile im Navigator — samt der Abgrenzung zum
Leere-Tage-Filter (der läuft vorher und lässt die Abwesenheitszeile stehen; erst dieser Filter
entfernt sie) und der Zusicherung, dass ein Teiltag mit erfassten Stunden nie verschwindet, also
keine Summe wandert.

**2. Eine reine Krankheitswoche geht nach der Kundenunterschrift direkt auf `approved`.** Der
Vergleich „vereinbart vs. erfasst" überspringt jetzt Tage ohne Zeiten auf **beiden** Seiten,
bevor die Pause geprüft wird. Bisher erbte ein nicht gearbeiteter Tag die 30-Minuten-Pause der
geplanten Schicht, während `ist_break` 0 blieb — die Woche landete auf `pending_employee` und
löste eine Abweichungs-Mail aus, obwohl `has_deviation` false war und vereinbart = erfasst.
`approve-stundenfreigabe` sagt jetzt an beiden Stellen (Gegenbestätigung, „Ein Kranktag ist
keine Abweichung"), dass eine solche Woche **nicht mehr in `PendingEmployee` auftaucht** — ihr
Fehlen dort ist der Fix, kein hängender Übergang — und dass eine Woche in `PendingEmployee`
damit deutlich eher eine echte Korrektur ist. Der Fix sitzt im Vergleich, nicht in den Daten,
wirkt also auch auf bereits gespeicherte Wochen; ein Backfill war nicht nötig.

### Fixed — 2026-08-14 `manage-contract-lifecycle`: Kundenportal-Signatur verteilt die Unterlagen nicht mehr automatisch (alluvo#3822)

Schritt 4a (*Auftragsbestätigung — what the customer receives*) beschrieb nur noch, **welche**
Dokumente rausgehen, nicht mehr korrekt an **wen**. Nach einer Unterschrift im Kundenportal
gilt jetzt für Rahmenvertrag **und** Einsatzvertrag, digital wie Papier-Upload:

- **An:** ausschliesslich die unterzeichnende Person.
- **CC:** nur, was der Unterzeichner im letzten Signatur-Schritt aktiv angehakt hat.
  Vorgeschlagen wird die bisherige Empfängerliste (Vertragsempfänger, beim AÜV plus der
  Besteller, ohne den Unterzeichner selbst) — **nichts ist vorausgewählt**, eine unberührte
  Unterschrift kopiert also niemanden. Der Unterzeichner kann zusätzlich Firmenkontakte
  anhaken oder eine freie Adresse eintragen, maximal 10 Kopien.
- **BCC an den Vertrags-Owner bleibt auf jedem Pfad unverändert.**

Unverändert und jetzt explizit abgegrenzt: `commission_as_agreed` und die Selbstbuchung über
den Portal-Checkout lösen den Verteiler weiterhin automatisch auf, `resend_order_confirmation`
bleibt die bewusste Operator-Entscheidung. Neu ergänzt: die Skill sagt jetzt, dass ein Operator
nach einer Portal-Unterschrift **nicht** behaupten darf, die Ansprechpartner hätten die
Unterlagen erhalten, und dass das Hinzufügen eines Vertragsempfängers keine garantierte Kopie
mehr ist, sondern nur ein Vorschlag, den der Unterzeichner ablehnen kann (Callout unter
*Recipient gate on `send_for_signoff`* entsprechend nachgezogen).

### Fixed — 2026-08-14 `approve-stundenfreigabe`, `record-absence`, `build-dienstplan`, `using-alluvo-operator`: eingereichte Krankmeldung zählt sofort — nicht erst nach Genehmigung (alluvo#3810)

Vier Skills behaupteten, nur eine **genehmigte** Abwesenheit nehme den Tag aus der
Abweichungsfrage heraus. Überholt: der neue SSOT `CoveringAbsenceDates` (ersetzt
`ApprovedAbsenceDates`) zählt `submitted`, `pending`, `needs_revision` **und** `approved` —
nur ein nie abgeschickter `draft`, `rejected` und `cancelled` zählen nicht. Konsequenzen, jetzt
überall gleichlautend dokumentiert:

- **Ein gemeldeter Kranktag ist keine Abweichung mehr** (`has_deviation` bleibt false, keine
  `disputed`-Woche wegen einer noch ungenehmigten Krankmeldung) — vorausgesetzt, an dem Tag
  wurde nichts erfasst; echte Über-/Unterschreitungen bleiben stehen.
- **Der Tätigkeitsnachweis druckt „Krank" schon bei Einreichung**, und der Tagesabschluss wird
  für gedeckte Tage gar nicht erst verlangt. Die Genehmigung entscheidet weiterhin über die
  **Bezahlung** — die Skills trennen Anwesenheits- und Lohnfrage jetzt explizit.
- **Das Soll bleibt am Tag stehen:** `replacement_needed`-Schichten zählen wieder in die
  `soll_minutes` des Zeitraums, damit der Nachweis „geplant 06:00–14:12 · Krank" zeigen kann —
  das Soll einer Abwesenheitswoche ist nicht mehr 0 (kein Doppelzählen: das Arbeitszeitkonto
  rechnet sein Soll separat und liest die Timesheet-Werte nie).
- **Neuer Job `RebuildTimesheetsForAbsence`:** jede Abwesenheits-Transition baut überlappende
  Wochen in `draft`/`pending_client` automatisch neu — eine Ablehnung bringt die Abweichung
  zurück. Unterschriebene und strittige Wochen werden bewusst nie angefasst; bestehende
  `disputed`-Wochen repariert weiterhin nur die Stundenklärung.

Unverändert (geprüft, nicht nur behauptet): `replacement_needed` wird nach wie vor nur von
**genehmigten** Abwesenheiten gesetzt (`ShiftAbsenceStatusSynchronizer`), inklusive
`affected_shifts`-Weiterverarbeitung in `record-absence`.

### Fixed — 2026-08-13 `approve-stundenfreigabe`: „gar keine MCP-Oberfläche" stimmte für den Stundennachweis nicht mehr (alluvo#3798)

Die Skill behauptete an zwei Stellen, der Stundennachweis (`0-426`) habe **„no MCP surface at
all"**. Das ist überholt: `manage-custom-field` nimmt `0-426` inzwischen an
(`CustomFieldRegistry::supportedModelTypes()`), und `manage-task` hängt eine Aufgabe über
`taskable_type: "timesheets"` an den Zeitraum. Beide Sätze sind jetzt korrekt abgegrenzt.

**Die Abgrenzung ist der eigentliche Inhalt.** Custom Fields lassen sich auf dem Zeitraum
*definieren* — nicht befüllen. `0-426` steht weiterhin **nicht** auf der generischen Allowlist
(`ModelTypeEnum::availableForMcp()`), also lehnen `get-model` und `manage-model` den Typ nach wie
vor ab und ein `cp_*`-Wert wird ausschließlich in der Web-App gesetzt. Die Skill schärft deshalb
ein, dem Operator nicht zu versprechen, das gerade angelegte Feld auch füllen zu können. Dazu die
Entdeckungslücke: `list-model-types` führt `0-426` nicht (die Liste ist die generische Allowlist),
der Typ ist also für genau dieses eine Tool gültig, ohne dort aufzutauchen. Tages-Custom-Fields
gibt es nicht — `0-427` und `0-428` sind nicht unterstützt.

**Notizen bleiben ausdrücklich draußen.** alluvo hat den Notiz-Pfad zwar generisch gemacht (das
polymorphe `note_entity` über das Trait `HasNotes`, Timesheet ist der erste Nutzer), aber das
betrifft die App, nicht MCP: `manage-activity` führt seine eigene Subject-Allowlist — `0-105`,
`0-3`, `0-30`, `0-31` — und weist alles andere ab. Über MCP lässt sich also weiterhin keine Notiz
an einen Stundennachweis hängen; eine Bemerkung gehört an den Tag oder in den `review_note` einer
Klärung. Die Identity-Root-Regel gilt unverändert: eine Notiz zu einer **Person** landet am
Contact, nie am Employee-/Candidate-Datensatz.

### Added — 2026-08-13 `onboard-new-employee`, `using-alluvo-operator`, `manage-contract-lifecycle`: bAV-Versorgungsträger für Ziffer 9.11 des Arbeitsvertrags (alluvo#3788)
Die Gruppe `contract` von `manage-settings` nimmt ein neues Feld `pension_providers` — die
Liste der Versorgungsträger der betrieblichen Altersvorsorge, Pflichtangabe nach § 2 Abs. 1
Satz 2 Nr. 13 NachwG auf dem **Arbeitsvertrag** (Ziffer 9.11).

**Es gibt keine Einstellungsseite dafür — MCP ist der einzige Weg hinein.** Ein Operator, der
nach „bAV eintragen" oder „Versorgungsträger hinterlegen" fragt, wird jetzt über
`using-alluvo-operator` nach `onboard-new-employee` (neuer Schritt **2g**) geroutet, statt in
die Web-App geschickt zu werden, wo die Liste nicht existiert.

**Leer ist der Normalzustand, nicht eine Lücke.** Jeder Tenant startet mit einer leeren Liste,
und solange sie leer ist, druckt der Arbeitsvertrag Ziffer 9.11 **gar nicht** — keine
Überschrift, kein Platzhalter. Genau das ist die richtige Darstellung für einen Tenant, der
keine bAV zusagt. Die Skill schärft deshalb ein: nur befüllen, wenn eine bAV tatsächlich
zugesagt ist — ein erfundener Versorgungsträger wäre eine falsche Angabe in einem
unterschriebenen Arbeitsvertrag.

**Form und Fallstricke, die dokumentiert sind:** `name` ist Pflicht (≤255), `address_line`,
`postal_code` (≤32), `city` und `country` sind optional; ein Eintrag ohne `name` lässt den
**ganzen Aufruf** scheitern. Das Update **ersetzt die komplette Liste** (kein Anhängen — erst
`get`, dann die volle Liste zurückschicken), und `manage-settings` hat **kein** `confirmed` —
`update` schreibt sofort, also wie beim Go-Live-Datum vorher explizit bestätigen lassen.

`manage-contract-lifecycle` bekommt nur eine Abgrenzung: `pension_providers` liegt zwar in
derselben Settings-Gruppe `contract`, gehört aber zum Arbeitsvertrag mit dem Mitarbeiter, nicht
zum Rahmen-/Einsatzvertrag mit dem Kunden — dort also nicht anfassen.

### Changed — 2026-08-13 `bench-check`, `onboard-new-employee`, `triage-data-quality`, `enrich-contacts-from-activities`, `profilvertrieb`: Bundesland/Kanton per Name setzen, Land per ISO-Code suchen (alluvo#3779)
Zwei MCP-Oberflächen rund um Adressen und Stammdaten haben sich geändert:

**`subdivision_code` nimmt jetzt den Namen.** Bisher galt „ISO 3166-2 oder Ablehnung", und
die Skills warnten wörtlich „niemals das blanke `NW`, niemals der ausgeschriebene Name".
Diese Warnung ist weg — sie führte genau zu dem Raten, das sie verhindern sollte. Akzeptiert
werden die ISO-Form (`DE-NW`, `AT-9`, `CH-ZH`, weiterhin bevorzugt), der ausgeschriebene Name
(`Nordrhein-Westfalen`, `Wien`, `Genf` — Schweizer Kantone auch französisch/italienisch/
englisch, `Genève` / `Ticino`) und das blanke Kürzel (`NW`, `ZH`), letzteres **nur mit
gesetztem `country`**: `NW` ist Nordrhein-Westfalen in Deutschland und Nidwalden in der
Schweiz. Gespeichert wird immer die ISO-Form. Das ist vor allem für **AT/CH** relevant, wo
`subdivision_code` mangels PLZ-Ableitung Pflicht ist und die Codes (`AT-9` = Wien) niemand
herleiten kann — dort jetzt: den Kanton/das Bundesland ausschreiben. Die volle Regel steht in
`bench-check`, die übrigen Skills verweisen darauf. Unverändert abgelehnt: ein Wert, der
keine Untereinheit von DE/AT/CH benennt, und ein ISO-Code, der `country` widerspricht.

**Eine Ausnahme, die neu dokumentiert ist:** das Personalfragebogen-Feld
`address_subdivision_code` (§2a) hat diese Lockerung **nicht** — es prüft weiter gegen eine
feste Liste **deutscher** ISO-Codes. Ein Name, ein blankes `NW` oder ein AT/CH-Code wird dort
abgelehnt; der verlässliche Weg bleibt die korrekte **PLZ**, aus der das Feld abgeleitet wird.

**Land wird per ISO-Code gefunden, nicht per Name.** `Country` (`0-90`) ist über `code` /
`code_3` suchbar. `onboard-new-employee` riet bisher zu `q: "Deutschland"` — das liefert
**0 Treffer**: der Katalog speichert den englischen ISO-Kurznamen, die deutsche Fassung wird
erst beim Rendern über ICU abgeleitet und ist keine Spalte. Richtig ist `q: "DE"` (oder
`"DEU"` / `"Germany"`); der Code überlebt außerdem Umbenennungen wie Turkey→Türkiye. Der
Fix-Hint in `get-profile-completeness` nennt jetzt ebenfalls `q:"DE"`.

### Changed — 2026-08-12 `onboard-new-employee`, `profilvertrieb`, `match-bench-to-clients`, `using-alluvo-operator`: Länder-Katalog lesbar, Pivot pro Ziel beim `bulk-attach`, „vollständig" ≠ „gefüllt", kein blindes Kalender-Versprechen (alluvo#3762)
Fünf MCP-Oberflächen, auf die die Skills sich verlassen, haben sich geändert:

**Country (`0-90`) ist lesbar.** Damit lässt sich die Staatsangehörigkeit erstmals ohne
Raten setzen: `search-model` `0-90` löst die Länder-ID auf, `nationality_id` /
`country_of_birth_id` gehen per `manage-model` `update` auf den **Contact** (`0-105`). Das
ist mehr als Stammdaten-Kosmetik — genau dieses Feld entscheidet über `is_eu_citizen`, und
eine **fehlende** Staatsangehörigkeit gilt als *unbekannt*, hält also Aufenthaltstitel und
Arbeitserlaubnis bei einer deutschen Pflegekraft dauerhaft als Pflichtdokument offen. Der
Katalog ist bewusst read-only (`create`/`update` auf `0-90` wird abgelehnt).
`onboard-new-employee` sagt jetzt auch, dass eine als Nicht-EU erfasste Staatsangehörigkeit
die beiden Dokumente **nicht** entfernt, sondern bestätigt — nie ein EU-Land wählen, um eine
Anforderung loszuwerden.

**`manage-association` `bulk-attach` nimmt `targets: [{id, pivot}]`.** Ein Pivot **pro
Ziel**, gemerged über das Call-Level-`pivot`. In `onboard-new-employee` §2f stand bisher die
jetzt falsche Regel „die eine `pivot`-Map gilt für *jedes* Ziel, also nie `is_primary: true`
im Bulk — Sekundärrollen im Bulk, die Primärrolle einzeln". Die Berufsbilder gehen jetzt in
**einem** Aufruf raus, mit `years_experience` / `certified_since` je Rolle und `is_primary`
auf genau einem Eintrag. `target_ids` + gemeinsames `pivot` bleibt gültig und richtig, wenn
die Werte sich wirklich decken. Die Vorschau weist die Pivot-Werte pro Ziel aus
(„per target: …"), wo sie abweichen — vor dem Bestätigen vorlesen.

**`get-profile-completeness`: `sections[].complete` heißt nur „kein Pflicht-Item offen".**
Zwei Sektionen haben überhaupt keine Pflicht-Items — **Fachbereiche & Technik** und
**Foto** — und melden deshalb bei 0 von N gefüllt weiterhin `complete: true`. Wer über
`sections[]` iteriert, hakt damit ausgerechnet die beiden Blöcke ab, die ein Profil
verkaufbar machen. Das neue Feld **`has_required`** trennt „erfüllt" von „nichts zu
erfüllen"; die Markdown-Ausgabe zeigt dafür `➖ … — 0/3 (alle optional)` statt eines nackten
✅. `onboard-new-employee` und `profilvertrieb` sagen das jetzt — und zugleich, dass das
**kein** Pflichtfeld-Fehler ist: eine leere optionale Sektion ist eine offene Empfehlung vor
dem Versand, nie ein „unvollständiger" Mitarbeiter.

**`get-profile-url` bestätigt den Verfügbarkeitskalender nicht mehr blind.** Bei einer Person
ohne Employee-Datensatz (jede reine Kandidatin) antwortet das Tool „Requested, but NOT shown
…" statt „Enabled" — der Kalender wird aus Employee-Verfügbarkeitszeiträumen gespeist und
die Profilseite rendert schlicht keinen. `profilvertrieb` und `match-bench-to-clients` sagen
jetzt: das Kalender-Versprechen an den Kunden kommt aus der **Antwortzeile**, nicht aus dem
gesetzten Flag.

**Action-Vorschau mit `sends_mail` zeigt Markdown statt komplettem Mail-HTML.** Empfänger und
Betreff sind unverändert vollständig und wörtlich; der Body ist eine Darstellung, bei 1.200
Zeichen gekappt mit sichtbarer Truncation-Markierung. Als querschnittliche Regel in
`using-alluvo-operator` aufgenommen (plus konkret in `onboard-new-employee` §2a): Empfänger
aus der Vorschau bestätigen, Betreff wörtlich zitieren, bei gesetzter Markierung nicht
behaupten, die Mail enthalte nichts weiter — und Layout/Fußzeile nie aus der Vorschau
beschreiben. Was versendet wird, hat sich nicht geändert; Mail geht weiterhin nur bei
`confirmed: true` raus.

### Fixed — 2026-08-12 `manage-contract-lifecycle`, `build-dienstplan`: die §11-Einsatzmitteilung hat keine wählbaren CC-Empfänger — ein Kundenkontakt kommt nie in CC (alluvo#3748)
Beide Skills beschrieben eine Empfängerauswahl, die es nicht mehr gibt (und die faktisch nie
so funktioniert hat): „der Ansprechpartner vor Ort wird **nur** dann in CC gesetzt, wenn er in
der Empfängerliste des Vertrags angehakt ist". Das war der Weg, über den in der Produktion 27
von 55 Sendungen einen Kundenkontakt in CC trugen — bei einer Offenlegung, die nach § 11
Abs. 2 Satz 4 AÜG dem **Leiharbeitnehmer** gilt, nicht dem Entleiher.

`send_assignment_notification` hat jetzt eine **feste, rein interne CC-Liste**: der
Vertragsinhaber, beim manuellen Versand zusätzlich der sendende Operator. Der Auto-Versand bei
`won` hat keinen Operator und geht deshalb nur an den Vertragsinhaber in CC — die Skills sagten
bisher pauschal „Inhaber und sendender Operator". Die Empfängerliste des Vertrags
(`recipient_contact_ids` / `add_contract_recipient`) ist die kundenseitige **Unterschrifts**-Liste
und wird für diese Mail bewusst nicht mehr herangezogen; ein trotzdem mitgeschicktes
`recipient_contact_ids` wird stillschweigend ignoriert, nicht ausgeführt. Beide Skills sagen das
jetzt so — und dass es dafür schlicht keine Auswahloberfläche gibt, der Operator also nie
gefragt oder ermutigt werden darf, einen Kundenkontakt aufzunehmen. Die Abgrenzung § 11
(Mitarbeiter) / § 12 (Kunde, über AÜV und Konkretisierung) bleibt unverändert stehen.

### Changed — 2026-08-12 `profilvertrieb`, `call-summary`, `enroll-outreach`: das Profil kann jetzt auch als PDF rausgehen — Link und PDF sind aber nicht dasselbe (alluvo#3746)
`manage-1on1-email` hängt auf `draft`/`update` alluvos generiertes **Profil-PDF** an
(`profile_pdf_employee_ids` / `profile_pdf_candidate_ids`, dazu
`profile_pdf_show_assignments`, Default **false**). Damit war eine Aussage in
`profilvertrieb` schlicht falsch geworden: „das Profil selbst reist immer als öffentlicher
**Link**" — das stand dort als Abgrenzung zum Personalakten-Dokument und ist ersetzt.

**Der Link bleibt die Empfehlung für die Erstansprache, und zwar aus einem konkreten Grund.**
Das Skill führt die Entscheidungsregel jetzt als Tabelle: Der Link bleibt aktuell, verfällt
nach 7 Tagen, meldet das Öffnen zurück und kürzt den Nachnamen ab („Anna M." —
`AbbreviatedName`, eine bewusste Datenschutzgrenze). Das PDF ist ein dauerhafter Schnappschuss,
trägt den **vollen** Namen und lässt sich weder zurückholen noch korrigieren noch messen. Das
PDF ist damit die **weitere** Offenlegung — richtig, wenn der Kunde etwas Ablagefähiges
verlangt hat, nicht als Verstärker einer kalten Ansprache. Beides zusammen zu schicken ist
üblich und in Ordnung.

Ergänzt, weil es sonst zu falschen Ansagen an den Operator führt: Es gibt **nichts vorher zu
erzeugen oder hochzuladen** — gerendert wird aus dem *aktuellen* Profil im Moment der
Bestätigung, bewusst nicht in der unbestätigten Vorschau. Employee- und Candidate-Ids dürfen
zusammen kommen und werden **pro Mensch dedupliziert** (ein Mensch, ein PDF). Zwei Ablehnungen
sind als Tool-Fehler weiterzureichen statt zu umgehen: ein Mensch ganz ohne Profildaten wird
abgewiesen, statt ein leeres PDF zu verschicken, und die Berechtigung ist dieselbe, die
`get-profile-url` auf den öffentlichen Link anwendet (`employees.view` / `candidates.view`).
Wie bei Dokumenten fügt `update` nur hinzu und entfernt nie; eine Anhang-Rücknahme kann das
Tool nicht.

`call-summary` bekommt denselben Hinweis für „Schicken Sie mir das Profil" aus dem Gespräch
(Verweis auf die volle Regel). In `enroll-outreach` ist festgehalten, dass eine **Sequenz das
Profil ausschließlich als Link** trägt — `manage-outreach-enrollment` hat keinen
PDF-Parameter, ein Datei-Wunsch ist eine handgeschriebene Einzelmail.

### Changed — 2026-08-12 `build-dienstplan`: der vorläufige Plan des Operators ist für den Mitarbeiter unsichtbar, ein verstrichener Monat nicht mehr änderbar (alluvo#3728)
Zwei Einschränkungen an dem, was die Mitarbeiter-App aus `SchedulePeriod` zeigt — beide in
§ 6b beschrieben, plus je ein Verweis dort, wo Operatoren sie treffen.

**„Meine Dienstpläne" blendet einen `provisional`-Plan aus, den der Mitarbeiter nicht selbst
verfasst hat.** Gefiltert wird nach **Autorschaft** (`creator_id`), nicht nach Status — jeder
andere Status bleibt sichtbar, gleich wer ihn angelegt hat. Da der Entwurf aus dem
Vertragsassistenten (`plan_provisional_shifts`, Schritt 1) vom **Operator** stammt, ist damit
praktisch jeder vorläufige Plan ausgeblendet; vorher stand er in der Liste, als wäre es der
Dienstplan des Mitarbeiters. Das Skill sagt jetzt ausdrücklich, dass „der Mitarbeiter kann ja
schon mal reinschauen" falsch ist — sichtbar wird der Plan mit der Veröffentlichung
(Schritt 7).

**Ein vollständig verstrichener Monat ist für den Mitarbeiter zu.** „Ändern"-Button,
Plan-Auswahl des Wizards und der Dienstplan-Upload bieten eine `published`-Periode nur noch,
solange `end_date` **heute oder später** liegt (Tenant-Zeit) — `end_date >= heute`, nicht
„enthält heute", der Plan für den nächsten Monat bleibt also änderbar. Serverseitig ebenso: ein
Ganzplan-Sync gegen eine verstrichene Periode wird mit `PERIOD_NOT_EDITABLE` abgewiesen, ist
also keine bloße Kosmetik. `draft` und `needs_revision` bleiben bewusst ohne Datumsgrenze — das
ist der Resubmit-Weg (§ 6b-a, dort ebenfalls ergänzt). Ohne Aufweichung einer Invariante
festgehalten: ein beendeter Monat ist damit **nicht** Operator-Reparatur — eine bereits
gespeicherte vergangene Schicht ist auch für Operatoren gesperrt und das Backfill-Fenster ist
der laufende Monat, Korrekturen gehören in die Stundenklärung (`→ approve-stundenfreigabe`).

Keine MCP-Fläche berührt: `app/Mcp/`, `routes/ai.php` und `ModelTypeEnum` sind unverändert.

### Added — 2026-08-12 `manage-contract-lifecycle`, `approve-stundenfreigabe`, `using-alluvo-operator`: Rollenanfragen im Kundenportal (`PortalRoleRequest` `0-434`) (alluvo#3719)
Benennt ein Kunde im Signier-Schritt jemanden, der gar kein Unterschriftsrecht hat, endet das
nicht mehr in einer 403 der Sign-Route, sondern schreibt eine **Rollenanfrage** —
`PortalRoleRequest`, Model-Typ **`0-434`** (nicht `0-433`, das ist `ShiftChangeLog`). Die
Anfrage erteilt für sich **nichts**: die benannte Person bekommt einen Contact bei der Firma
und sonst nichts — keine Membership, keine Rolle, kein Login, keine Mail — bis ein
Administrator entscheidet.

`manage-contract-lifecycle` dokumentiert den Fall jetzt im Empfänger-/Portalzugang-Block: das
Lesen über `query-model` auf `0-434` (`status` `pending`/`approved`/`rejected`, `company_id`,
`contact_id`, `requested_by_contact_id`), die beiden über `manage-record-action`
(`operation: "execute"`, zweistufig) erreichbaren Actions —
**`approve-portal-role-request`** (`role`, `context_only`, `decision_note`) erteilt die Rolle
**und** gibt den Vertrag weiter, **`reject-portal-role-request`** (`decision_note`) schließt
die Anfrage ohne Erteilung und ohne jede Mail — sowie die drei Punkte, an denen sich Operatoren
sonst verlaufen: `role` ist per Default die angefragte, normalerweise `commercial` (die Rolle,
die `contracts.sign` trägt) und **nicht** `administrator`; die Freigabe macht die genehmigte
Person zum **Hauptempfänger** (der Anfragende bleibt als CC drauf), ändert also den Namen, den
der ungezeichnete AÜV als Unterzeichner druckt; und ein Kunden-Administrator
(`ContactsManage`) entscheidet **im selben Zug**, sodass „der Kunde hat jemanden benannt, wo
ist meine Anfrage?" legitim mit „schon genehmigt" beantwortet ist. Nur eine `pending`-Anfrage
ist entscheidbar; beide Actions verlangen `contacts.edit` + `client_portal.manage_access`.
Anfragen entstehen ausschließlich im Portal — es gibt keinen Create-Pfad, weder für Operatoren
noch über MCP.

Ausdrücklich als **kaputt** dokumentiert statt geglättet: `context_only: true` („nur dieser
eine Vertrag, keine dauerhafte Rolle") setzt die Anfrage auf `approved` und läuft danach in
einen Berechtigungsfehler — keine Rolle, keine Vertragsweitergabe, keine Signier-Mail, und die
Anfrage lässt sich nicht erneut entscheiden. Die Skills raten davon ab, bis alluvo#3721 gefixt
ist.

`approve-stundenfreigabe` bekommt den Abschnitt neben `PortalMembership` (`0-430`), weil eine
genehmigte Anfrage eine ganz normale Rollenzuweisung auf der Membership erzeugt — die dort
gelesenen `portal_roles_label` können also aus einer Freigabe stammen und nicht aus einem
`assign-portal-roles`-Aufruf. `using-alluvo-operator` routet „Kunde kann nicht unterschreiben /
hat jemand anderen benannt / Rollenanfrage offen" auf `manage-contract-lifecycle`.

### Changed — 2026-08-12 `build-automation-agent`, `build-dienstplan`: eine zu einem freigegebenen Dienstplan hinzugefügte Schicht meldet jetzt (`ShiftChangeType::Added`) (alluvo#3718)
`ShiftChangeType` hat einen vierten Fall: `added`. Eine Schicht, die zu einem bereits
freigegebenen Dienstplan hinzugefügt wird, schreibt jetzt eine `ShiftChangeLog`-Zeile —
vorher schrieb `ShiftObserver::created()` keine, sodass der AÜG-§-11-Abs.-2-Satz-4-Digest des
Mitarbeiters die Stornierungen einer Planänderung meldete und über die von derselben Änderung
hinzugefügten Arbeitstage schwieg.

`build-automation-agent` (Trigger-Abschnitt `0-433`) hatte beides gegenteilig festgeschrieben
und ist korrigiert: `change_type` hat vier Werte statt drei, und die Einschränkung „eine vom
Mitarbeiter hinzugefügte Schicht feuert nichts" entfällt — „sag mir Bescheid, wenn ein
Mitarbeiter einen Einsatz einträgt" **ist** jetzt auf `0-433` baubar. Neu dokumentiert:
`old_values` fehlt bei einer Hinzufügung (Spiegelbild der Löschung, bei der `new_values`
fehlt), das Beispiel mit der `alt → neu`-Pfeilschreibweise passt nur zu `time_changed`, und
die **Erst-Materialisierung einer Portal-Buchung** ist bewusst unterdrückt (der Plan entsteht
dort sofort veröffentlicht, die Einsatzmitteilung deckt sie ab) — eine **spätere** Buchung auf
denselben Einsatz meldet sehr wohl.

`build-dienstplan` Schritt 6a nennt die Hinzufügung jetzt neben Zeitänderung, Storno und
Löschung als auslösendes Ereignis, samt der Konsequenz für Operatoren: „stattdessen den Tag
hinzufügen" ist **kein** stiller Weg mehr, und ein Tausch (`remove-shift` + `add-shift`) liest
sich im Digest als zwei Zeilen. Schritt 6b verliert die Aussage, dass eine vom Mitarbeiter
hinzugefügte Schicht keine Zeile schreibt.

### Changed — 2026-08-12 `build-dienstplan`, `approve-stundenfreigabe`: Soll/Plan-Vergleich am Ende des Mitarbeiter-Dienstplan-Wizards, blockierende Bestätigung entfällt (alluvo#3716)
Der Review-Schritt des employee-seitigen Dienstplan-Wizards zeigt jetzt `Soll <Monat>`,
`Verplant im <Monat> gesamt`, die Differenz („X h über/unter Soll") und „davon bereits
gearbeitet". Abschnitt 6b in `build-dienstplan` beschrieb den Wizard bisher ohne diese
Oberfläche und ist ergänzt worden — vor allem um die drei Punkte, an denen sich Operatoren
sonst verlaufen: **die Plan-Zahl ist monatsweit über alle Einsätze** (nicht der Plan auf dem
Bildschirm des Mitarbeiters), **das Soll kommt vom Gehalt** (`Salary` `0-12`:
`monthly_target_hours` → `weekly_working_hours × 52 ÷ 12` → GVP 35 h, flach, abzüglich
genehmigter Abwesenheiten, anteilig im Ein-/Austrittsmonat) und **nicht** aus
`agreed_hours_per_week` am Einsatzvertrag, und **ohne auflösbares Soll erscheint das Panel gar
nicht** (Gehaltsdatenlücke, `→ triage-data-quality`). Dazu: Schichten außerhalb des
Ankermonats zählen nicht mit, der Ankermonat ist der Startmonat der Periode.

**Weggefallen:** die blockierende Checkbox „Ich habe die Abweichung von der Sollzeit zur
Kenntnis genommen…". Ein unterbesetzter Monat wird vom Mitarbeiter **nicht** mehr aktiv
bestätigt — ein eingereichter Plan ist kein Beleg dafür, dass er die Unterschreitung gesehen
hat. Die ArbZG-§ 3-Hartgrenze und die `max_hours`-Obergrenze des Einsatzes blockieren
unverändert weiter. `approve-stundenfreigabe` bekommt einen Abgrenzungshinweis: das Soll aus
der App ist ein **anderes** als das eingefrorene Plan-Soll auf Stundenzettel und
Tätigkeitsnachweis — die beiden gehören nicht miteinander abgeglichen.

### Added — 2026-08-12 `build-automation-agent`: Datensätze von Hand in einen Workflow einsteuern (`enroll`, `list-candidates`) (alluvo#3712)
`manage-workflow` bekommt zwei Verben. **`enroll`** (`workflow_id` + `record_id`, optional
`force`, `reason`) schiebt EINEN Datensatz von Hand in einen Workflow — das Gegenstück zum
vorhandenen `unenroll`, und der einzige Weg, einen Datensatz zu melden, der vor der Anlage des
Workflows entstand oder während er deaktiviert war. **`list-candidates`** (`workflow_id`,
optional `limit`, Standard 20, gedeckelt bei 50) ist die lesende Auswahlliste dazu: die
jüngsten Datensätze des Trigger-Typs mit ID, Anlagezeitpunkt und der Angabe, ob sie die
Bedingungen erfüllen.

Der Enrollment-Abschnitt in Schritt 7 nennt jetzt die vier Punkte, die ein Operator vor dem
`enroll` wissen muss: die **Bedingungen gelten weiter** (ein ausgeschlossener Datensatz wird
abgelehnt, `force: true` ist ein ausdrücklicher Bypass — nie nehmen, nur damit der Aufruf
durchgeht); **`allow_reenrollment` entscheidet über die Wiederholung** (während `active`/`waiting`
nie eine zweite Einschreibung, nach Abschluss nur mit dem Flag); der **Workflow muss aktiviert
sein**; und die **Slack-Fußzeile sagt „manuell nachgereicht"**, der Post ist also nicht mit einer
frischen Änderung der einsteuernden Person zu verwechseln. Dazu: `enroll` ist einstufig (kein
`confirmed`-Preview) und feuert die Aktionen wirklich — vorher ausdrücklich freigeben lassen.
Beide Verben lehnen einen datensatzlosen geplanten Workflow ab.

Die Abschnitte zu den **Trigger-only-Typen** (`0-422` TimeTrackingDayClosure, `0-433`
ShiftChangeLog) verweisen jetzt auf `list-candidates` als **einzige** Möglichkeit, überhaupt an
eine Datensatz-ID dieser Typen zu kommen — sie haben keine MCP-Lesefläche, `query-model` /
`get-model` weisen sie ab.

### Added — 2026-08-12 `build-automation-agent`, `build-dienstplan`, `using-alluvo-operator`: Änderung am freigegebenen Dienstplan (`0-433`) als Workflow-Trigger (alluvo#3705)
`ShiftChangeLog` ist als Modelltyp `0-433` registriert und — wie `TimeTrackingDayClosure`
(`0-422`) — von einem Workflow beobachtbar, aber **nicht** über MCP verwaltbar. Damit ist
„ein Mitarbeiter hat einen bereits freigegebenen Dienstplan geändert" erstmals als Auslöser
verfügbar; vorher gab es dafür keinen beobachtbaren Datensatz (`Shift` `0-111` ist nicht
MCP-lesbar).

`build-automation-agent` bekommt den Abschnitt dazu: `trigger_event: "created"`, Bedingung
`record_source equals external_panel` trennt die Mitarbeiter-Änderung von der des Disponenten
(`manual` / `mcp`), `change_type` ist `time_changed` / `cancelled` / `deleted`, Platzhalter-Wurzel
ist `shift_change_log`. Dazu die beiden Lücken, die man Operatoren vor der Zusage nennen muss:
ein vom Mitarbeiter **hinzugefügter** Einsatz schreibt keine Zeile und feuert nicht, und eine
komplette Umbesetzung ist bewusst unterdrückt. Außerdem: **eine Auslösung pro geänderter
Schicht** — die 15-Minuten-Bündelung gilt nur für die Mitarbeiter-Mail, nicht für Workflows.

### Fixed — 2026-08-12 `build-automation-agent`: Mitarbeiter-Platzhalter zeigten auf ein Feld, das leer rendert (alluvo#3705)
Die Identitätsfelder eines Mitarbeiters (`first_name`, `last_name`, `email`) liegen am
verknüpften **Kontakt** — `{{…employee.first_name}}` rendert deshalb leer. Der `0-422`-Abschnitt
nennt jetzt `{{…employee.contact.first_name}}` bzw. `{{…employee.display_name}}`.

### Changed — 2026-08-12 `approve-stundenfreigabe`, `head-of-disposition`, `using-alluvo-operator`, `onboard-new-employee`: aus `TimesheetWeek` wird `Timesheet` — Slug, Recht und Datensatzname (alluvo#3628)
Ein Abrechnungszeitraum ist längst nicht mehr zwingend eine Woche (das Schema hängt am
Vertrag: wöchentlich, halbmonatlich, monatlich). Das Modell heißt deshalb jetzt `Timesheet`.
Die **Modelltyp-ID `0-426` bleibt unverändert** — und bleibt weiterhin *nicht* auf der
MCP-Allowlist, ebenso wenig wie `0-427` / `0-428`. Es ändert sich also nichts daran, was ein
Skill aufrufen kann, sondern nur, wie die Skills die Oberfläche benennen.

- **Datensatzliste**: `/objects/timesheet-weeks` → **`/objects/timesheets`** (HR & Payroll →
  Stundennachweise). Zweimal in `approve-stundenfreigabe` genannt.
- **Recht**: der fehlende Menüpunkt hängt jetzt an **`timesheets.view`** (Familien
  `timesheets.*`, `timesheet_days.*`, `timesheet_day_corrections.*` — die beiden letzteren
  unverändert). Korrigiert in `approve-stundenfreigabe`, `head-of-disposition` und
  `using-alluvo-operator`.
- **Modellname**: jede Nennung von `TimesheetWeek` heißt jetzt `Timesheet` — in
  `approve-stundenfreigabe` (Allowlist-Absatz, Vorschau-Zeile, `Timesheet.deadline_at`,
  Go-Live-Warnung), `head-of-disposition` und `onboard-new-employee`.
- **Prosa**: wo der Datensatz noch "week" hieß, steht jetzt Zeitraum/period — passend zum
  Abschnitt "an approval period is not an ISO week any more", dem der alte Wortlaut
  widersprach.

Unverändert und bewusst *nicht* angefasst: die Einstellung
`deadline_days_after_week_end`, die Portal-Kennzahl **"Offene Wochen"** (nur der
Payload-Schlüssel dahinter heißt jetzt `openTimesheetsCount`, das Label nicht) sowie die
Feldnamen `period_label`, `date_from`, `date_until`, `has_deviation`, `client_channel` und
`deadline_at`.

### Changed — 2026-08-12 `onboard-new-employee`: "es kommt kein Code" — der Ersteinladung repariert das OTP-Flag, das erneute Senden nicht (alluvo#3688)
`invite-user` setzte das Flag für die E-Mail-Authentifizierung bisher nur dort, wo es das
Benutzerkonto selbst **anlegt**. Existierte die Zeile schon (Import, früherer Tenant, manuell
erstellt), blieb das Flag leer — und die Anmeldung verschickt dann **stillschweigend** keinen
Code: keine Mail, kein Fehler, der Mitarbeiter sieht trotzdem "Code gesendet".

- Die **Ersteinladung** repariert das Flag jetzt auf der zentralen *und* der Tenant-Zeile. Wer
  noch kein verknüpftes Konto hat, wird durch `invite-user` also nebenbei anmeldefähig.
- Beim **erneuten Senden** (Mitarbeiter hat schon ein verknüpftes Konto) passiert das
  ausdrücklich **nicht**: dieser Pfad erneuert nur die Einladung und schickt die Mail noch
  einmal. Das Skill sagt das jetzt klar, statt ein erneutes Senden als Lösung zu versprechen —
  und verbietet, das Flag selbst am Benutzerdatensatz zu setzen.
- Genannt ist außerdem, wo die Betroffenen sichtbar sind: *Auswertungen → Mitarbeiter-App*,
  Liste **"Freigeschaltet, aber Login unmöglich"**.

### Changed — 2026-08-12 `bench-check`, `onboard-new-employee`, `profilvertrieb`, `enrich-contacts-from-activities`, `triage-data-quality`: Bundesland ist auf allen Location-Schreibpfaden Pflicht (alluvo#3680)
`manage-location` (`create`, `bulk-create`, `update`) und `manage-model` für Location
(`0-95`) weisen eine Adresse zurück, deren Bundesland (`subdivision_code`) sich nicht
auflösen lässt. Eine deutsche Adresse **ohne PLZ** wird nicht mehr angelegt.

- **`bench-check`** trägt die kanonische Regel: DE → korrekte fünfstellige `zip`, daraus wird
  das Bundesland abgeleitet (nicht raten); AT/CH → `country` **und** `subdivision_code`
  explizit (`"AT-9"`, `"CH-ZH"`), da es dort keine PLZ-Zuordnung gibt. `country` defaultet
  still auf `"DE"`. ISO-3166-2-Code, nie `"NW"`, nie ins veraltete `state`.
- **`onboard-new-employee`** fragt für die Privatadresse jetzt die **PLZ** ab statt Ort + Land.
- **`profilvertrieb`** und **`enrich-contacts-from-activities`** nennen dieselbe Bedingung —
  bei angereicherten Web-Daten fehlt die PLZ gern; dann nachfragen statt erfinden.
- **`triage-data-quality`** korrigiert eine überholte Angabe: `manage-location` kennt
  `subdivision_code` inzwischen sehr wohl, beide Wege landen den Fix. Ein `update` wird auf
  der **zusammengeführten** Adresse geprüft, Altdatensätze ohne Bundesland bleiben also
  bearbeitbar.

### Changed — 2026-08-12 `onboard-new-employee`, `profilvertrieb`, `triage-data-quality`: Staffing-Rollen gehören dem Menschen, nicht dem Employee (alluvo#3676)
Die Qualifikationen sind vom `Employee` auf den `Contact` umgezogen
(`employee_staffing_role` → `contact_staffing_role`). Employee, Candidate und Contact
derselben Person lesen und schreiben jetzt **eine** Zeile.

- **`onboard-new-employee` bekommt Schritt 2f (Qualifikationen/Berufsbilder).** Rollen lassen
  sich über `manage-association` mit `source_type: "0-105"` (Contact) — oder unverändert
  `"0-2"` (Employee) — anhängen, inklusive `pivot` (`is_primary`, `years_experience`,
  `certified_since`). Damit trägt ein **Kandidat vor der Einstellung** erstmals
  Qualifikationen; `source_type: "0-81"` bleibt kein gültiges Paar. Genau eine primäre Rolle
  pro Mensch, serverseitig erzwungen.
- **`profilvertrieb`:** der Qualifikationen-Block des öffentlichen Profils liest aus dem
  Contact und ist für Kandidaten nicht mehr strukturell leer. Ein leerer Block ist damit eine
  echte Datenlücke — vor dem Versand des Links melden und füllen.
- **`triage-data-quality`:** `get-model` auf einer Rolle (`0-100`) listet **Contacts** statt
  Employees (`_relationship_counts.contacts`). „Mitarbeiter ohne primäre Rolle" wird weiter am
  Employee gemeldet und mit `set-primary-staffing-role` behoben, wirkt aber auf die geteilte
  Zeile — also auf alle Datensätze der Person.
### Changed — 2026-08-12 `build-dienstplan`, `using-alluvo-operator`: Auf dem Mitarbeiter-Pfad blockiert das ArbZG strenger als auf dem Operator-Pfad (alluvo#3643)
Der Dienstplan der Mitarbeiter-App ist bei den *abweichungsfähigen* ArbZG-Befunden bewusst
**strenger** als jeder Pfad, den ein Disponent nutzt — bisher stand in Schritt 6b das Gegenteil
("dieselben nicht-blockierenden § 5-Hinweise"). Korrigiert:

- **§ 5 Ruhezeit, § 7 (> 48 h/Woche) und Sonntagsarbeit blockieren dort**, sofern keine Ausnahme
  sie positiv erlaubt: Sonntagsarbeit nur mit Ausnahmekategorie am **Einsatzbetrieb**
  (Fallback: Position des Mitarbeiters), § 7 nur mit Tarifbindung im aktiven Gehalt, § 5 nur bei
  einer Lücke **ab 10 h** *und* Kategorie "Krankenhäuser und Pflege". Unter 10 h blockiert immer
  (§ 5 Abs. 2 erlaubt die Verkürzung *auf* zehn Stunden, nie darunter); ein Befund ohne lesbare
  Lücke blockiert ebenfalls (fail closed). Herabgestuft wird nie — § 3 bleibt beidseitig hart.
- **Erlaubte Sonntagsarbeit erzeugt gar keinen Befund mehr** — auch keinen "erlaubt"-Hinweis.
  Jeder Mandant ist Pflege-Personaldienstleister, der erlaubte Sonntag ist also der Normalfall;
  ein Hinweis je Sonntag begrub die § 3/§ 5-Befunde, auf die es ankommt. Ein sauberer Plan zeigt
  **null** Befunde. Die Ersatzruhetag-Pflicht (§ 11 Abs. 3) steht einmal pro Plan als Fußnote
  unter der Übersicht. Das **Fehlen** des Hinweises bestätigt die Ausnahme — sein Auftauchen
  heißt, der Einsatzbetrieb ist nicht gepflegt.
- **Zwei sich überschneidende Schichten innerhalb EINER Abgabe sind neu ein harter Befund** —
  auf allen Pfaden, auch dem Operator-Pfad. Bisher verglich die Prüfung eingehende Zeilen nur
  gegen *bereits gespeicherte* Schichten, zwei gemeinsam gesendete Konfliktzeilen kamen also
  überall durch (auch bei `manage-shift-plan action: "create"`). Direkt aneinander grenzende
  Schichten (Ende 13:00 / Beginn 13:00) bleiben zulässig.
- **Der Ansprechpartner im Einsatz wird jetzt ebenfalls benachrichtigt** — und das ist der
  **Kunde**. Reine Notiz (Änderungen, Restplan, vergangene Schichten als eine Summenzeile),
  kein CTA. Abschaltbar je Mandant über `notify_on_site_contact_on_shift_changes` (Gruppe
  `availability`, **Default an**). Außerdem behoben: ein AÜV ohne Owner unterdrückte bisher die
  gesamte Benachrichtigung — es erfuhr niemand etwas.
- **Nur Befunde an Tagen, die der Mitarbeiter tatsächlich schreibt, blockieren ihn.** Ein harter
  Befund an einem unberührten Tag wird angezeigt, verweigert die Abgabe aber nicht — sonst
  sperrt ein alter Verstoß den Mitarbeiter dauerhaft aus.
- **Die `max_hours`-Grenze des Einsatzes blockiert dort ebenfalls** — genau umgekehrt zum
  Operator-Pfad, wo sie gar nicht geprüft wird. Die Ablehnung nennt den AÜV-Owner bzw.
  "Disposition" als Ansprechpartner; das Anheben ist eine Vertragsfrage.
- **Häufigste Ursache ist eine fehlende Ausnahme am Einsatzbetrieb, kein schlechter Plan.**
  Die Schicht stattdessen per MCP selbst einzutragen umgeht das Gate bewusst — kein Workaround.
- **Der Wizard zeigt die Befunde vor dem Absenden** (je mit "gesetzliche Grenze?" und "würde
  *diese* Abgabe verweigert?") samt Telefonnummer des Ansprechpartners im Einsatz und des
  AÜV-Owners.
- **Schritt 6b-a**: derselbe geprüfte Satz gilt **vor** dem Parken eines Vorschlags — ein
  geparkter Vorschlag hat ihn also schon bestanden. Zusätzlich aufgenommen: solange
  `allow_multiple_shifts_per_day` (Gruppe `availability`, Default aus) aus ist, wird ein Tag
  abgelehnt, der von ≤ 1 auf ≥ 2 Schichten wachsen würde; bereits zweifach belegte Tage haben
  Bestandsschutz.
- **`using-alluvo-operator`**: neuer Routing-Eintrag für "Die App lässt den Mitarbeiter seine
  Schicht nicht speichern".

### Changed — 2026-08-11 `profilvertrieb`, `call-summary`: Der Tracking-Wächter greift jetzt auch bei `send` und `schedule` (alluvo#3681)
Nachtrag zum Eintrag unten: die dort dokumentierte Lücke ("Die Sperre sitzt auf
`draft`/`update`, nicht auf `send`") ist geschlossen — jeder Entwurf, der vor dem Wächter
geschrieben wurde, blieb sonst versendbar.

- **`send` und `schedule` prüfen den *gespeicherten* Body** und lehnen ihn ab, wenn er unser
  eigenes Öffnungs-/Klick-Tracking zitiert.
- **Die Ablehnung kommt ohne `confirmed`** — auch die unbestätigte Vorschau wird abgelehnt.
  Beim Senden liefert der Aufrufer keinen neuen Text, den eine Vorschau zur Korrektur anbieten
  könnte; Skills dürfen hier also nicht "erst Vorschau, dann bestätigen" erwarten.
- **Der einzige Ausweg ist `action: update` auf dieselbe `email_id`**, danach senden. Ein
  neuer Entwurf ist es ausdrücklich nicht — das Werkzeug verlangt `update` statt eines
  Duplikats.

### Changed — 2026-08-11 `profilvertrieb`, `call-summary`, `enrich-contacts-from-activities`, `build-automation-agent`, `triage-data-quality`: Interne Daten bleiben intern — Tracking-Ablehnung, `privacy_warnings`, Art.-9-Sperre, Feldhistorie-Verweis (alluvo#3675)
Zwei Vorfälle haben je eine Code-Sperre bekommen, dazu ein neues Warnfeld und ein Verweis
statt einer Sackgasse. Vier Punkte für die Skills:

- **`manage-1on1-email` lehnt Entwürfe ab, die unser eigenes Öffnungs-/Klick-Tracking
  zitieren.** Betrifft `draft` und `update` bei `confirmed: true`; die unbestätigte Vorschau
  nennt die beanstandete Phrase vorab ("Confirming this body as-is will be refused."). Die
  Ablehnung ist eine **inhaltliche Korrekturaufforderung, kein technischer Fehler** — Passage
  umschreiben, nie denselben Text erneut bestätigen. Die Daten kommen indirekt an: eine
  interne Aufgabe zitiert sie in Prosa, `get-timeline` gibt diese Bodies wörtlich zurück. Die
  Sperre sitzt auf `draft`/`update`, nicht auf `send`.
- **`build-profile-links-block` kann `privacy_warnings` zurückgeben.** Neues Feld auf oberster
  Ebene, wenn die kundensichtbare `bio` eines verlinkten Profils nach einer besonderen
  Kategorie nach Art. 9 DSGVO aussieht (`record_id`, `contact_id`, `name`, `field`, `terms`,
  `message`). **Keine Sperre** — der Link wird gebaut. Befund dem Operator vorlesen und eine
  ausdrückliche Entscheidung einholen, bevor der Link in eine Kundenmail geht.
- **Art.-9-Daten gehören nie in ein Freitextfeld** (`bio`, `notes`, `availability_notes`,
  `other_profile_notes`, `headline`, `summary`) — sie werden weit weg vom Gespräch gelesen,
  und `bio` rendert im Kundenportal. Die automatisierten Schreibpfade (AI-Takeover,
  Inbox-Agent, `manage_model`-Step) **verweigern** eine solche Nutzlast und nennen Feld und
  Begriffe; der MCP-Pfad tut das nicht — dort bindet die Regel den Operator. Der Fakt gehört
  in sein strukturiertes Feld (z. B. `Employee.is_severe_disability`) oder in eine Aufgabe.
- **`get-field-history` verweist bei leerem Ergebnis auf den Contact.** Fragt man ein
  Employee-/Candidate-Feld ab, das am Identity-Root Contact hängt (z. B. `bio`), nennt die
  leere Antwort jetzt `model_type` und `record_id` des Datensatzes, der die Historie führt —
  aber nur, wenn dort tatsächlich welche liegt. Dem Verweis folgen statt "keine Historie"
  zu melden.

### Changed — 2026-08-11 `approve-stundenfreigabe`, `manage-contract-lifecycle`, `using-alluvo-operator`: Portal-Einladung schaltet den Zugang jetzt frei und stempelt die Membership (alluvo#3665)
`send-portal-invitation` vergibt nicht mehr nur die Rollen und verschickt die Mail, sondern
**aktiviert vorher eine deaktivierte Membership**. Ohne das konnte eine Einladung folgenlos
bleiben: eine `disabled` Membership kann keine Session aufbauen, der OTP-Endpunkt verschickt
dann bewusst gar keinen Code, zeigt dem Empfänger aber trotzdem den "Code gesendet"-Screen.
Zwei Punkte für die Skills:

- **Einladen *ist* Zugang gewähren.** Das repariert den Klassiker "eingeladen, aber es kommt
  kein Code" in einem Aufruf — ist aber kein Freifahrtschein: eine `disabled` Membership ist
  eine bewusste Entscheidung (Sperre, Offboarding, strittiger Account), und die Einladung hebt
  sie auf. Erst `status` auf `0-430` lesen, dann fragen. Die Umschaltung landet als
  `client_portal_access_toggled` in der Timeline, und nur wenn der Schalter wirklich aus war.
- **Der Einladungs-Stempel sitzt jetzt auf der Membership.** Vorher wurde nur das alte Pivot
  beschrieben, `portal_invitation_status` blieb deshalb nach einem erfolgreichen Versand auf
  `never_invited` stehen. Bei Altdatensätzen ist `never_invited` also **kein** Beleg dafür,
  dass nie eingeladen wurde — Timeline (`client_portal_invitation_sent`) prüfen.

Dazu: Kontakte, die vor dem 2026-08-11 über das Portal-Formular "Ansprechpartner hinzufügen"
angelegt wurden, kamen mit **ausgeschaltetem** Portal-Zugang auf die Welt (der Toggle hatte
keinen Default). Der Toggle steht jetzt standardmäßig auf **an**; Altfälle heilt ein erneutes
`send-portal-invitation`. In `manage-contract-lifecycle` steht beim Empfänger-Callout
zusätzlich, dass `assign-portal-roles` den Zugang **ohne** Mail wiederherstellt (und dabei die
vollständigen `assignments` mitgeschickt werden müssen), die Einladung dagegen mit Mail.
### Changed — 2026-08-11 `triage-data-quality` + `onboard-new-employee` + `profilvertrieb`: Berufsstationen ausblenden statt löschen, CV-Sortierung, Profil-Zeitfenster (alluvo#3669)
Die Lebenslauf-Modelle haben über `manage-model` neue schreibbare Felder bekommen. Damit
ist die Sackgasse aus alluvo#3650 weg — Profil-Aufräumen war bisher nur in der App möglich:

- **`profile_visibility` auf `0-184` (ContactWorkExperience)** — neues Enum `auto`
  (Standard) / `always` / `never`. `never` blendet die Station auf dem veröffentlichten
  Profil, im Kundenportal **und** im Profil-PDF aus, `always` hält sie gegen das
  Mandanten-Zeitfenster. Neuer Schritt **3g** in `triage-data-quality`: `delete-model`
  lehnt `0-184` weiterhin ab (kein Soft-Delete), Ausblenden ist der Weg. Nichts wird
  gelöscht, nichts wird repariert — eine ausgeblendete Station zählt weiterhin für
  `work_history_coverage`, Ausblenden macht also keine Lücke grün. Andere Werte als die
  drei werden abgelehnt.
- **`position` auf `0-184`, `0-183` (ContactEducation) und `0-185` (ContactLanguage)** —
  das Sortierfeld hatte vorher keine Regel im Form Request und wurde still verworfen: der
  Aufruf meldete Erfolg und änderte nichts. In `onboard-new-employee` steht jetzt, dass es
  schreibbar ist und dass eine früher „nicht hängengebliebene" Sortierung genau diese Lücke
  war.
- **Zeitfenster `talent_hub.profile_work_experience_visible_years`** — rollierendes Fenster
  **nur** für das veröffentlichte Profil (Standard `null` = alles sichtbar; eine laufende
  Station fällt nie heraus). `profilvertrieb` warnt jetzt in Schritt 5: ein dünn wirkender
  Profil-Link ist eine Sichtbarkeitseinstellung, kein verlorener Datensatz — erst `0-184`
  lesen, nie eine zweite Station anlegen, damit der Lebenslauf voller aussieht.
- Das Zeitfenster ist über MCP **nicht** einstellbar (`manage-settings` kennt das Feld in
  der Gruppe `talent_hub` weder lesend noch schreibend) — als alluvo#3671 gemeldet, in den
  Skills bis dahin als Ist-Zustand dokumentiert.

### Added — 2026-08-11 `build-dienstplan`, `approve-stundenfreigabe`, `using-alluvo-operator`: Dienstplan-Änderung des Mitarbeiters übernehmen oder ablehnen (alluvo#3653)
Neuer Schritt **6b-a** in `build-dienstplan`. Schaltet der Mandant
`employee_shift_changes_require_approval` ein (**Standard aus**, les-/schreibbar über
`manage-settings` `group: "shift_planning"` — *nicht* über die alte Gruppe `availability`),
geht die Ganzplan-Änderung aus dem Mitarbeiter-Dienstplan nicht mehr sofort live, sondern
liegt als **Vorschlag** an der Dienstplan-Periode. Zwei neue Record-Actions auf `0-110`
(`manage-record-action`, zweistufig wie jeder Write):

- `apply-employee-shift-proposal` — übernimmt den Vorschlag über denselben Schicht-Diff wie
  die direkte Mitarbeiter-Änderung: eine verschobene Schicht **behält ihre id** (und damit
  §-11-Änderungsspur, Umbesetzungs-Status und eine anhängende TimeEntry), eine entfallene
  wird **storniert, nie gelöscht**, neue Tage werden angelegt. Optionales
  `data.proposal_version`; eine Abweichung wird abgelehnt und nichts geschrieben.
- `reject-employee-shift-proposal` — verwirft den Vorschlag und **fasst keine Schicht an**;
  der Live-Plan war nie geändert. `data.reason` mitgeben.

Weiter dokumentiert, weil operativ entscheidend:

- **Gilt nur für die Ganzplan-Änderung.** Einzelne Schichten legt der Mitarbeiter weiterhin
  in jedem Mandanten sofort an, verschiebt oder storniert sie sofort (Schritt 6b) — der
  Schalter macht *nicht* jede Mitarbeiter-Änderung prüfpflichtig.
- Die Periode **behält ihren Status** (ein veröffentlichter Monat bleibt `published`, er
  wechselt bewusst nicht nach `pending_approval`), der Live-Plan bleibt die ganze Zeit
  wirksam. Ein Vorschlag **ersetzt**, er stapelt nicht. Nur `published`, `draft` und
  `needs_revision` nehmen die Ganzplan-Änderung überhaupt an.
- § 3 und die `max_hours`-Grenze werden **vor** dem Parken geprüft; die Sperre für bereits
  begonnene oder vergangene Schichten greift beim Übernehmen weiterhin und lässt die
  Übernahme dann komplett scheitern (eine Transaktion, nichts halb angewendet).
- **Der Vorschlag ist über MCP nicht lesbar** — `pending_shift_proposal` /
  `pending_proposal_version` stehen in keinem Schema, keine der Actions hat eine Diff-Vorschau,
  und auch die Weboberfläche zeigt nur die beiden Buttons ohne Inhalt (alluvo#3660). Die Skill
  sagt das ausdrücklich: nie einen Vorschlag übernehmen, dessen Inhalt der Operator nicht
  bestätigt hat.
- `approve-stundenfreigabe` grenzt sich in `## Related skills` explizit ab: dort werden
  *geleistete Stunden* freigegeben, hier eine Änderung am *laufenden Dienstplan*.

### Changed — 2026-08-11 `onboard-new-employee`, `profilvertrieb`: Einsatzumfang ist ein Pflichtfeld im öffentlichen Profil (alluvo#3647)
`monthly_hours` (Einsatzumfang, Stunden/Monat) ist im Katalog der Profil-Vollständigkeit
von optional auf **required** gewechselt — Matching und Buchung rechnen mit dem
Monatsvolumen. Auswirkung auf `get-profile-completeness`:

- Ein Kandidat ohne `desired_monthly_hours` steht jetzt in
  `public_profile.missing_required`, meldet `is_complete: false` und ein niedrigeres
  `required_progress`. Ein Profil, das vorher vollständig war, kann ohne jede
  Datenänderung auf unvollständig kippen — das ist die Umstellung, kein verlorener Wert.
- `onboard-new-employee` benennt das Feld samt Fix (`manage-model update` Contact `0-105`,
  `desired_monthly_hours`) und stellt klar, dass **eine Stundenzahl** gespeichert wird,
  kein Label: `160`, nie `"Vollzeit"`. Die Labels (Vollzeit / Teilzeit 30h / Teilzeit 20h /
  Minijob / Andere) bietet nur der Personalfragebogen-Chat an und rechnet sie selbst um.
- `profilvertrieb` prüft `missing_required`, bevor es ein `is_complete: false` der
  lückenhaften Berufserfahrung zuschreibt.

Nicht nachgezogen (keine Operator-Oberfläche): die kandidatenseitigen Chat-Änderungen
derselben Auslieferung — der Abschluss des Personalfragebogens fragt offene optionale
Angaben einmal gebündelt nach und behauptet keine vollständige Vollständigkeit mehr,
solange optionale Lücken offen sind; der KI-Hinweis reist jetzt mit der Begrüßung.

### Changed — 2026-08-11 `approve-stundenfreigabe`: Quittungsmail nach Unterschrift auf dem Gerät + Tätigkeitsnachweis schon ab Kundenfreigabe (alluvo#3314)
Der Stundenfreigabe-Unterschriftenfluss auf dem Gerät des Mitarbeiters ist nachgezogen
(kein MCP-Tool hat sich geändert — der Produkt-Flow dahinter schon):

- **Neue Quittungsmail:** Wer eine Stundenfreigabe auf dem Gerät des Mitarbeiters
  unterschreibt, erhält **eine** Mail pro Unterschrift mit allen freigegebenen Zeiträumen
  (`timesheet.signature_receipt`, transaktional, auf der Kontakt-Timeline protokolliert) —
  aber nur, wenn der Kontakt eine E-Mail-Adresse hat. Ohne Adresse wird nur der Versand
  übersprungen (Normalfall, kein Fehler); die PDFs entstehen trotzdem. Der Skill sagt
  deshalb nie mehr bedingungslos "der Unterzeichner bekommt eine Kopie".
- **Tätigkeitsnachweis-Fenster:** Das PDF entsteht jetzt nach jeder vollständigen
  Kundenfreigabe — auch für Zeiträume, die wegen abweichender Stunden in `PendingEmployee`
  landen (vorher gab es dort gar kein PDF, bis der Mitarbeiter reagierte). "Entwurf"-Badge
  und die Approved/Invoiced-Sperre der Aktion „Tätigkeitsnachweis öffnen" sind unverändert.
- **Teilfreigabe:** erzeugt weiterhin weder PDF noch Mail, bis der Rest freigegeben ist.
- **Bekannter Defekt dokumentiert:** Die Quittungsmail kommt derzeit **ohne** die
  PDF-Anhänge an (falsche Media-Collection auf alluvo-Seite, gemeldet als alluvo#3636);
  bis zum Fix bekommt der Unterzeichner das Dokument vom Operator, nicht aus dem Postfach.

### Changed — 2026-08-11 `manage-contract-lifecycle`: Einsatzmitteilung nur noch über das Vertrags-Tool, importierte Verträge über MCP nachpflegbar (alluvo#3343)
Zwei Oberflächen-Änderungen nachgezogen (MCP-Server 1.4.19 → 1.4.20):

- **Einsatzmitteilung: `manage-record-action` listet `send_assignment_notification` auf
  `0-31` nicht mehr.** Die Web-Buttons (Senden + Ansehen) sind auf die Assignment-Seite
  gewandert — die §11-AÜG-Mitteilung gilt pro Einsatz, nicht pro Vertrag — und sind dort
  reine Wizard-Einstiege ohne MCP-Pendant. Der einzige MCP-Weg ist jetzt
  `manage-assignment-contract` `action: "send_assignment_notification"` (unverändert, inkl.
  optionalem `assignment_id`); der Skill verwies noch auf den generischen
  Record-Action-Pfad.
- **Importierte WON-Verträge sind über MCP nachpflegbar.** `action: "update"` akzeptiert
  neu `framework_contract_id` + `inherit_billing_from_framework` (nur ein signierter
  Rahmenvertrag derselben Firma), und `manage_einsatz` `update`/`remove` ist auf einem
  importierten WON-Vertrag erlaubt (Import-Ausnahme statt reinem DRAFT-Gate). Der Skill
  beschrieb `update`/`remove` als draft-only und kannte den nachträglichen
  Rahmenvertrag-Link nicht.

### Changed — 2026-08-11 `manage-contract-lifecycle`, `record-absence`, `clean-inbox`, `using-alluvo-operator`: echter `confirmed:false`-Preview in `manage-record-action`, End*-Confirmed-Hard-Cut, Einsatzmitteilung-Web-Umzug, Vapi-Lese-/Re-Sync-Vertrag (alluvo#3605)

- **`manage-record-action` `confirmed:false` ist jetzt ein echter Preview.** Der Tool-Preview
  ruft die schreibfreie Preview-Maschinerie der Action selbst auf und rendert sie unter
  `## Action Preview` (Kaskaden-Summen, `affected_shifts`, …); deklarierte Effekte erscheinen
  separat unter `## Declared Effects (preview)`. `manage-contract-lifecycle` (Schritt 6,
  Call-Shape-Block) und `record-absence` ("kein Preview liefert `affected_shifts`" — stimmt
  nicht mehr) entsprechend vereinfacht.
- **End*-Actions: absent-means-execute ist weg (Hard Cut).** `EndAssignmentContractAction` /
  `EndAssignmentAction` führen nur noch bei explizitem `data.confirmed: true` aus; fehlender
  Key oder `false` previewt. Über MCP füllt das Tool `data.confirmed` weiterhin aus dem
  Top-Level-Schalter, wenn der Key fehlt — der Skill beschreibt beide Ebenen jetzt korrekt.
- **Einsatzmitteilung-Web-Controls sind vom Vertrag auf den Einsatz umgezogen**; das
  generische `manage-record-action` listet `send_assignment_notification` auf `0-31` nicht
  mehr. Der MCP-Weg bleibt unverändert `manage-assignment-contract`
  `action: "send_assignment_notification"`.
- **`update-vapi-instructions` (C5, Hard Cut):** unbestätigter Aufruf ist jetzt ein reiner
  Read (liefert gespeicherte `custom_instructions` + `composed_prompt` — der bisher fehlende
  Lesepfad); expliziter Re-Sync ist ein nacktes `data: {"confirmed": true}`. Die alte
  "kein-Data-Aufruf = sicherer Re-Sync"-Konvention ist gelöscht; `clean-inbox`
  (Geschäftszeiten-Re-Sync, Lese-/Schreib-Ablauf, Push-Retry) und der Navigator nachgezogen.
- Nicht übernommen, weil kein Skill die Fläche referenziert: die neue
  `effect-previews`-Web-Route und die präzisierte `TransitionAction`-Beschreibung (der
  §11-Auto-Send bei `won` steht bereits im Skill).

### Changed — 2026-08-11 `manage-contract-lifecycle` + `using-alluvo-operator`: json-Spalten korrekt auf „leer" filtern, übersprungene Filterbedingungen warnen jetzt überall (alluvo#3583)
Zwei Engine-Fixes im Filter-/Query-Layer, die die Skills jetzt dokumentieren (kein
Tool-Name hat sich geändert):

- **`is_empty`/`is_not_empty` auf json-Spalten ist jetzt JSON-bewusst.** SQL-NULL,
  JSON-`null`, `[]` und `{}` zählen alle als „leer" — vorher lief der Filter auf einer
  json-Spalte entweder ins Leere (ungefilterte Gesamtmenge) oder in einen SQL-Fehler.
  Auf den Rollen-Zeilen (`0-344`) sind `surcharge_overrides` und `surcharges` damit
  direkt filterbar: „welche aktuellen Rollen-Zeilen haben keine Zuschläge konfiguriert"
  ist `surcharges is_empty` + `is_current` true — nicht `is_null`, das den häufigen
  Fall „gesetzt, aber leeres `[]`" übersieht (`manage-contract-lifecycle`).
- **`query-model` meldet übersprungene Filterbedingungen jetzt als Warnung** — wie
  `count-model`/`search-model` es schon taten. Eine Bedingung, deren Operator die
  Spalte nicht trägt, wird verworfen und als `Filter condition on '<field>' … was NOT
  applied` gemeldet; das Ergebnis ist dann breiter als angefragt
  (`using-alluvo-operator`).

### Changed — 2026-08-11 `approve-stundenfreigabe` + `using-alluvo-operator` + `onboard-new-employee`: `manage-settings` Gruppen kommen jetzt aus der App-Registry (alluvo#3569)
`manage-settings` leitet einen Teil seiner Gruppen jetzt aus der neuen App- &
Integrations-Registry ab; die Einstellungsseiten sind unter **Einstellungen → Apps**
umgezogen (alte URLs leiten weiter):

- **Kanonischer Gruppenschlüssel für die Stundenfreigabe ist `time_tracking_hours_approval`**
  (die Stundenfreigabe ist jetzt das hours-approval-Feature der Zeiterfassung-App). Der alte
  Schlüssel `timesheet` funktioniert übergangsweise weiter, wird aber entfernt — beide
  `manage-settings`-Beispiele in `approve-stundenfreigabe` und die Navigator-Einträge sind
  umgestellt. Die Firmen-Overrides über `manage-record-settings` behalten ihr
  `timesheet.`-Präfix (andere Oberfläche, unverändert).
- **Der Live-Timer ist jetzt per MCP schaltbar:** `manage-settings`, Gruppe `time_tracking`,
  Feld `live_timer_enabled`. Die bisherige Aussage "kein MCP-Setting" in
  `approve-stundenfreigabe` war damit veraltet und ist korrigiert (weiterhin tenant-weit,
  kein Firmen-Override; Zustimmung des Operators vor dem Schreiben einholen).
- **Navigator:** neuer Eintrag für "wo ist die Einstellungsseite hin" → Einstellungen → Apps
  / Integrations-Hub, mit den registry-abgeleiteten Gruppenschlüsseln (`time_tracking`,
  `time_tracking_hours_approval`, `fleet`, `fleet_driving_licence_checks`, `client_portal`).
  UI-Pfade in `approve-stundenfreigabe` und `onboard-new-employee` (Fuhrpark) nachgezogen.
  Kein Skill nutzte den Schlüssel `driving_licence_checks`; `fleet` und `client_portal`
  behalten ihre Schlüssel unverändert.

### Changed — 2026-08-11 `onboard-new-employee` + `using-alluvo-operator`: digitaler Personalfragebogen — harte Absende-Sperre, "Liegt mir nicht vor", Bundesland/Land, Notfallkontakt-Liste (alluvo#3632)
Der Fragebogen-Ablauf in Schritt 2a ist in fünf Punkten nachgezogen (kein MCP-Tool hat
sich geändert — der Produkt-Flow dahinter schon):

- **Absenden ist jetzt eine harte serverseitige Sperre.** Ein unvollständiger Fragebogen
  kann nicht mehr unterschrieben werden: alle gesetzlichen Pflichtfelder (Name,
  Geburtsdaten, Staatsangehörigkeit, Geschlecht, komplette Anschrift, IBAN, Steuer-ID,
  SV-Nummer) müssen gefüllt sein. Zwischenspeichern und "Weiter" bleiben bewusst
  permissiv.
- **"Liegt mir nicht vor"** gibt es strukturiert für genau zwei Felder — `tax_id` und
  `social_security_number` — mit Grund (`not_to_hand` / `first_job` / `other`). Das ist
  die Auskunft für einen blockierten Berufsanfänger; jedes andere Feld lehnt einen
  Escape ab. Über MCP zeigt sich ein Escape als fehlender Statutory-Key in
  `filled_keys`.
- **Bundesland und Land sind neue Pflicht-Adressfelder** (Adresssuche im
  Anschrift-Schritt); "Stammdaten übernehmen" schreibt jetzt auch `subdivision_code`
  und `country` auf die Home-Location.
- **Notfallkontakte sind eine Liste.** Im Übernahme-Dialog eine Zeile für die ganze
  Liste (`accepted_keys`-Key: `emergency_contacts`, keine Spalten-Keys mehr), und die
  Übernahme **synchronisiert destruktiv** — gespeicherte Kontakte, die die Einreichung
  nicht trägt, werden gelöscht. Deshalb nie vorausgewählt, sobald Kontakte existieren.
- **Schwerbehinderung / Grad der Behinderung** stehen nicht mehr auf dem
  Pre-Hire-Fragebogen eines Candidates — nur noch, wenn die Person bereits Employee ist
  (§ 164 Abs. 1 SGB IX vs. AGG). Ihr Fehlen ist keine Lücke.

Mitverifiziert und gleich korrigiert: `filled_keys` ist inzwischen im MCP-Schema der
Submission (`0-429`) sichtbar (alluvo#3382 geschlossen) — der Skill schickte den Operator
für die Key-Liste noch in die Web-App; `accepted_keys` lässt sich jetzt direkt daraus
bauen.

### Changed — 2026-08-10 `onboard-new-employee` + `using-alluvo-operator`: Fuhrpark — Fahrzeugzuweisung als Modelltyp `0-432`, Schadensmeldung über Actions (alluvo#3582)
Beide Skills behaupteten bisher, die Fahrzeugzuweisung sei **nicht** über MCP schreibbar
("passiert in der Web-App"). Das ist falsch: **EmployeeVehicle** ist ein eigener Modelltyp
(`0-432`) auf `manage-model`. Die Zuweisung ist eine **Historie**, keine Verknüpfung —
jede Zeile hat eigene `id` und ein `valid_from`/`valid_until`-Fenster, und dieselbe Person
kann denselben Wagen in zwei getrennten Zeiträumen fahren.

- **Übergeben** = `0-432` anlegen mit `employee_id` + `vehicle_id` + `valid_from` (alle drei
  Pflicht); optional `valid_until`, `max_annual_mileage_km`, `notes`.
- **Beenden** = `valid_until` **aktualisieren** — niemals `detach` über
  `manage-association`, das die Zeile *löscht* statt ihr Fenster zu schließen und damit die
  Antwort auf "wer ist den Wagen wann gefahren" mitnimmt.
- `is_current` ist **nicht** schreibbar (wird bei jedem Save aus den Daten neu berechnet).
- Das Paar Employee→Vehicle bleibt in der Registry, aber **read-only**: es listet die
  Zeiträume mit ihren Assignment-IDs und weist Schreibzugriffe auf `0-432` um.
- Nebeneffekt dokumentiert: eine gültige Zuweisung nimmt den Mitarbeiter in den
  Führerschein-Kontroll-Zyklus auf — **einseitig**, das Beenden räumt das Flag nicht ab.

Neu ist ausserdem der ganze Weg der **Schadensmeldung** (neuer Schritt 2e):
`report_damage` als Record-Action auf dem Fahrzeug (`0-4`) erzeugt dieselbe Meldung wie der
Fahrer in der App — Status `submitted`, Benachrichtigung an den Fuhrpark-Verantwortlichen,
Beteiligte (`parties`, max. 5) in einem Rutsch. Ein handgemachter `0-67`-Datensatz ist der
falsche Weg (stiller `draft`, niemand wird benachrichtigt). Pflicht: `incident_type`
(`accident`|`damage`|`theft`), `occurred_at`, `description` und ein Fahrer (`employee_id`,
Default = aktueller Fahrer des Wagens). Zwei kontraintuitive Punkte stehen ausdrücklich im
Skill: die Betriebsanweisung "bei jedem Schaden die Polizei hinzuziehen" gilt dem **Fahrer**
und wird hier **nicht** erzwungen (telefonisch gemeldete Schäden sollen erfasst werden, nicht
verloren gehen), und **Fotos gehen über MCP nicht** — nur Web-Formular und App.

Der Schadensfall wird über zwei weitere Actions auf `0-67` fertiggefahren (seit dem Issue
dazugekommen, mitverifiziert): `draft`|`submitted`|`under_review` --`send_to_insurer`-->
`sent_to_insurer` --`close`--> `closed`. `send_to_insurer` erzeugt als **einziger** Schritt
das ausgefüllte Versicherungsformular (nur wenn die verknüpfte Versicherung einen Form-Filler
hat — `insurance_id` also **vorher** setzen), friert den Datensatz ein und **mailt nichts**;
`close` ist terminal und der einzige verbleibende Zug. `0-67` ist über MCP lesbar, aber
**nicht** `manage-model`-schreibbar, und `status` schreibt man nie selbst.

### Added — 2026-08-10 `clean-inbox`: Ticket an einen Kontakt weiterleiten (`forward-ticket`, alluvo#3451)
Neue Record-Action `forward-ticket` auf dem Ticket (`0-300`), erreichbar über
`manage-record-action` (`operation: "execute"`, `action: "forward-ticket"`, Vorschau ohne
`confirmed`, dann `confirmed: true`). Sie leitet die **ursprüngliche eingegangene E-Mail** an
einen **Kontakt** (`contact_id`, bevorzugt — Adresse kommt aus dem CRM) oder ersatzweise an
eine getippte `to_email` weiter; `note` und `include_attachments` (Default `true`) wie gehabt.
Beides gesetzt → `contact_id` gewinnt, keins von beidem → Fehler beim Ausführen.

Der Skill trennt sie ausdrücklich vom bereits dokumentierten `manage-ticket` `forward`:

- **`forward-ticket`** — beliebiger bekannter Kontakt, **keine** Preset-Prüfung gegen
  `forward_targets`. Der Guardrail greift hier schlicht nicht, deshalb ist die ausdrückliche
  Bestätigung der Adresse durch den Operator die einzige Kontrolle vor `confirmed: true`.
- **`manage-ticket` `forward`** — nur konfigurierte Drittadressen (Fibu), dafür mit
  `close_after` in einem Schritt.

Ebenfalls festgehalten, weil es Erwartungen setzt: die Weiterleitung landet als weitere
Nachricht am **selben Ticket** (nie ein neues); weitergeleitet wird die **erste** eingehende
Nachricht, nicht die letzte; ein noch nicht verknüpfter Kontakt wird dem Ticket als
*Mentioned* angehängt (eine bestehende Rolle bleibt), sodass der Vorgang in seiner Timeline
auftaucht; die Action **schließt nichts** — Schließen bleibt `set_status` mit Grund und
Beleg; und sie funktioniert nur auf **Gmail-Tickets** (WhatsApp/Chat/Telefon werden beim
Ausführen abgelehnt, obwohl die Action dort noch gelistet ist).

Dazu die ehrliche Einordnung der Vorschau: eine Record-Action-Vorschau spiegelt nur die
übergebenen `data` plus Formularvalidierung — sie löst die Kontakt-Adresse nicht auf, prüft
die Gmail-Bedingung nicht und rendert die ausgehende Nachricht nicht. Empfänger (Name *und*
Adresse), Begleittext und Anhänge werden dem Operator deshalb in eigenen Worten vorgelegt.
`description:` nimmt „Ticket weiterleiten" / „an den Kontakt weiterleiten" als Trigger auf.

### Changed — 2026-08-10 `document_planned_disclosure`: Einstellungs-Pfad und Options-Labels ergänzt (alluvo#3427)
Das Setting selbst ist bereits dokumentiert (kam mit alluvo#3384 herein): drei Werte
`none` | `delta_only` | `full`, Default `delta_only`, pro Kundenunternehmen überschreibbar,
plus die Warnung zu `none`. Was fehlte, war das, was jede andere Setting-Sektion in
**approve-stundenfreigabe** nennt — **wo** man es im Web-App klickt und **wie** die Optionen
dort heißen.

Ergänzt: **Einstellungen → Stundenfreigabe → „Soll-Ist-Darstellung im Tätigkeitsnachweis"**
(Dropdown direkt unter dem Leere-Tage-Schalter) und eine Zuordnung Options-Label → Enum-Wert:

| Operator sagt | Wert |
|---|---|
| „Nur Ist-Stunden (kein Soll, keine Abweichung)" | `none` |
| „Ist-Stunden + Abweichung (ohne geplante Zeiten)" | `delta_only` |
| „Vollständiger Soll-Ist-Vergleich (Soll-Block + Abweichung)" | `full` |

Ein Operator zitiert das Label, nicht den Enum-Wert — ohne die Tabelle ließ sich „stell auf
vollständigen Soll-Ist-Vergleich" nicht sicher auf `full` abbilden. Zusätzlich festgehalten:
die Auswahl `none` blendet im Web-App selbst eine Inline-Warnung ein (dieselbe Portal-Parität
wie im Skill) — wer sie zitiert, liest die App richtig, sieht keinen Fehler.
`description:` nimmt die drei Label-Formulierungen als Trigger auf.

Reine Präzisierung, keine Verhaltensänderung: das Setting bleibt Darstellung, Summen und
Abrechnung bewegen sich nicht.

### Changed — 2026-08-10 `manage-record-action`: schreibfreie Action-Vorschau ist wieder erreichbar (alluvo#3574)
Korrigiert den Sync von heute früh (alluvo#3568): die Verodung wurde durch eine **Präzedenz**
ersetzt. Ein **explizit gesetztes** `data.confirmed` gewinnt jetzt in *beide* Richtungen; das
Top-Level-`confirmed` füllt den Schlüssel nur noch, wenn er fehlt. Damit ist die
aktions-eigene, schreibfreie Vorschau für alle sieben Actions wieder da, die auf
`data['confirmed']` prüfen (`end_contract`, `end_assignment`, `reassign_shifts`,
`add_assignment`, `replace_employee`, `merge_employee`, `merge_candidate`):

| Aufruf | Verhalten |
|---|---|
| Top-Level `confirmed: false` | generische Tool-Vorschau, Action wird **nicht** aufgerufen — keine Kaskade/kein Plan/kein Preflight |
| Top-Level `true` + `data.confirmed: false` | **Vorschau der Action** — rechnet die Konsequenzen, schreibt nichts |
| Top-Level `true` + `data.confirmed: true` | führt aus |
| Top-Level `true`, `confirmed` in `data` **fehlt** | führt aus |

**manage-contract-lifecycle** (Call-Shape zu `end_contract`/`end_assignment`),
**build-dienstplan** (Schritt 6c, Umbesetzung) und **merge-duplicate-companies**
(`merge_employee`/`merge_candidate`) zeigen dem Operator wieder die echten Konsequenzen
— Kaskade, Umbesetzungsplan, Merge-Preflight — **bevor** geschrieben wird. Für
destruktive, AÜG-relevante Schritte ist das der richtige Ablauf.

Neu in allen drei Skills festgehalten: die Tool-Hülle titelt **jeden** Aufruf mit
`# Action Executed`, auch den, der nichts geschrieben hat. Die Überschrift ist **kein**
Beleg für einen Schreibzugriff — maßgeblich sind die Response Data (`preview_only` bei
`end_contract`/`end_assignment`; bei `reassign_shifts` ein `plan` mit `result: null`, bei
den Merges der Preflight ohne Merge-Ergebnis). Kein „erledigt" an den Operator melden,
nur weil die Überschrift das behauptet.

### Changed — 2026-08-10 `manage-record-action`: Top-Level-`confirmed` ist jetzt der einzige Schalter (alluvo#3568)
Das Tool verodert sein Top-Level-`confirmed` ab sofort in `data.confirmed` — ein
`confirmed: true` auf Tool-Ebene führt jede Record-Action **wirklich** aus, egal was in
`data` steht. Damit ist das alte Muster „Top-Level `confirmed: true` + `data.confirmed:
false` als Vorschau" (end_contract, end_assignment, reassign_shifts) **kein Preview mehr,
sondern ein Schreibzugriff**; die aktions-eigene, schreibfreie Vorschau (Kaskade/Plan) ist
über MCP derzeit nicht erreichbar — Konsequenzen/Plan kommen in den Response Data des
bestätigten Laufs zurück, Blocker und unquittierte Warnungen verweigern den Lauf weiterhin
serverseitig. **manage-contract-lifecycle** (Call-Shape-Block zu `end_contract`/
`end_assignment`) und **build-dienstplan** (Schritt 6c, Umbesetzung — dort auch
`record_id` statt des falschen `model_id` im Call-Shape) sind auf das neue Verhalten
umgeschrieben; **merge-duplicate-companies** braucht für `merge_employee`/`merge_candidate`
kein `data.confirmed: true` mehr, das Top-Level-Flag genügt.
Ein Kontakt-Paar, bei dem **beide** Seiten einen verknüpften Kandidaten tragen, war bisher
eine Sackgasse (pauschale Ablehnung „merge those first", ohne dass es einen Kandidaten-Merge
gab). `manage-duplicates` `preview-merge`/`merge` liefert jetzt — analog zum Employee-Fall —
einen geführten **Candidate Merge Preflight** (wandernde Spalten, Relationen, offene
Entscheidungen wie abweichender `status` oder zwei CVs), und die neue Record-Action
**`merge_candidate`** (auf dem behaltenen Kandidaten, `0-81`, via `manage-record-action`)
erledigt den mechanischen Teil: Spalten auffüllen, Bewerbungen/Tasks/Kommentare/CV umhängen,
Quelle in den Papierkorb. Blockieren beide Rollen, kommen beide Preflights zurück und beide
Merge-Actions laufen zuerst; `bulk-merge` überspringt so ein Paar mit Nennung der
blockierenden Rolle(n). **merge-duplicate-companies** (Abschnitt „Blocked at 3a") und
**triage-data-quality** (Schritt 5) dokumentieren den Kandidaten-Fall jetzt genauso wie den
Employee-Fall — einen Kandidaten zu löschen, um einen Kontakt-Merge freizuschalten, ist
ausdrücklich keine Option mehr.

### Changed — 2026-08-09 Workflow-Dry-Run läuft den Steps-Baum, `actions: []` räumt Altlisten auf (alluvo#3564)
`manage-workflow` `action: "test"` rendert nicht mehr die flache Legacy-`actions`-Liste,
sondern läuft den **v2-Steps-Baum** genauso ab wie eine echte Enrollment: unter
`## Steps dry-run (branch decisions + rendered output, nothing sent):` zeigt der Dry-Run pro
Knoten die genommene `if`/`switch`-Verzweigung, die gerenderte Ausgabe jeder `action` auf dem
genommenen Pfad und annotiert `delay`/`wait_until`, ohne zu warten. Außerdem akzeptiert
`update` jetzt `actions: []` als bewusstes Leeren einer veralteten Legacy-Liste — nur erlaubt,
wenn der Workflow einen `steps`-Baum hat oder im selben Update bekommt.
**build-automation-agent** dokumentiert beides.

### Changed — 2026-08-09 Workflows können jetzt warten, verzweigen und Felder schreiben (alluvo#3438)
`manage-workflow` ist auf Workflow Builder v2 gewechselt: eine Auslösung ist ab sofort eine
dauerhafte **Enrollment**, die schlafen und später weiterlaufen kann — nicht mehr ein einmaliger
Durchlauf. **build-automation-agent** dokumentiert die neue Oberfläche vollständig:

- **`steps`-Baum** als rekursive Alternative zur flachen `actions`-Liste — `action`, `if`,
  `switch`, `delay` (feste Dauer oder relativ zu einem Datumsfeld, optional `business_hours`)
  und `wait_until` (mit `timeout_days` und `on_timeout`). Grenzen: max. 100 Knoten, Tiefe 10,
  max. 365 Tage pro `delay`. Ein Knoten-`id` darf beim Bearbeiten **nicht** geändert werden,
  sonst verlieren wartende Enrollments ihren Wiedereinstiegspunkt. Flache `actions` bleiben
  unverändert gültig — nichts muss migriert werden.
- **Vier weitere `trigger_event`-Werte** mit eigenem `trigger_config`: `field_changed`,
  `starts_matching`, `date_reached` — und `action_performed`, das heute **noch keine gültigen
  Aktionsschlüssel hat** (keine Aktion ist `#[WorkflowTriggerable]` markiert) und deshalb
  ausdrücklich nicht angeboten werden darf.
- **`goal_conditions`** (Enrollment endet sofort als `goal_reached`, sobald das Ziel erreicht
  ist) und **`unenroll_on_mismatch`** (Ende, sobald der Datensatz die `conditions` nicht mehr
  erfüllt) — die beiden Ausstiege, die eine mehrstufige Erinnerungsstrecke überhaupt vertretbar
  machen.
- **Neue Aktion `update_field`** (`set` / `copy` / `clear`) — nur eigene, fillable Spalten,
  Money-Felder in **EUR**, aktionsverwaltete Lifecycle-Felder (z. B. AssignmentContract
  `stage`/`status`) sind hart gesperrt. Erste Workflow-Aktion, die unbeaufsichtigt in einen
  Geschäftsdatensatz schreibt, und im Preview entsprechend explizit zu benennen.
- **Neue Verben `list-enrollments` und `unenroll`** — die Antwort auf „warum hängt dieser
  Datensatz?" (Status, wartender Knoten, Wiederaufnahmezeitpunkt) bzw. das Herausnehmen eines
  einzelnen Datensatzes aus einer laufenden Strecke.
- **Re-Enrollment präzisiert:** ein Datensatz bekommt **nie** eine zweite Enrollment, solange
  eine frühere `active` oder `waiting` ist — `allow_reenrollment` entscheidet erst danach. Bei
  einem Workflow mit `delay` bedeutet das: Auslöser während der Wartezeit verfallen.

### Changed — 2026-08-09 `body_html` nie HTML-escapen — escapte Bodies werden repariert und gemeldet (alluvo#3426)
A `body_html` that arrives with its tags escaped (`&lt;p&gt;` instead of `<p>`) used to be
stored verbatim, so the recipient saw the markup — and `body_text` showed it too, because the
downstream cleaner found no real tags to strip and then decoded the entities. `manage-1on1-email`
now **decodes such a body once on the way in** on both `draft` and `update`, and adds a warning
line containing `HTML-escaped` to the unconfirmed preview *and* to the response after the write.
The check is deliberately narrow — it only fires when the body has no real tags at all, so a
legitimate `<p>5 &lt; 6</p>` is left alone. **profilvertrieb** (§6b Compose & send) and
**call-summary** (§5 Draft the follow-up email) now state the rule up front: pass real HTML
(`<p>…</p>`, `<br>`), or plain text with `\n\n` separators, never both styles in one body and
never escaped tags. The repair is a safety net, not a licence — the warning line means the
composing step was wrong and the body should be re-sent as real HTML; the `build-*-block` output
is already real HTML and gets embedded verbatim. No tool, action, parameter or schema changed.

### Changed — 2026-08-09 Tätigkeitsnachweis: AÜV-Nummer im Seitenkopf, Soll-Block nur bei `full` (alluvo#3384)
The § 17c sheet's layout description in **approve-stundenfreigabe** was wrong in three places, and
the drift issue itself was already stale — a later change made the planned block optional. Verified
against `origin/main` rather than the issue text. **The meta block now carries four facts only**
(Mitarbeiter/in mit Tätigkeit, Entleiher, Einsatzort, Abteilung): **Kalenderwoche** moved to the
per-KW group headers in the table, and **AÜV-Nummer plus the documented range live exclusively in
the running page header** — they were removed from the meta list, not duplicated into the header,
so an operator must not be sent looking for an "Einsatzzeitraum" row. The page header is what makes
a loose printed page filable against a contract. **The table's column count is a per-company
setting**, `timesheet.document_planned_disclosure` (`none` | `delta_only` | `full`, tenant default
`delta_only`, overridable on the Company via `manage-record-settings`): only `full` prints the
**Soll block mirrored beside Ist** — Von · Bis · Pause · Std. on both sides, twelve columns — while
the default prints the worked block plus the single Abw. figure and `none` drops Abw. too. So the
old flat claim "Spalten sind … · Soll · Ist · Abw. …" misdescribed the default document. Layout
only: no total, no derived break and nothing billed moves with it. Setting a client to `none` now
carries an explicit warning, since the portal's approval screen always shows the full comparison —
the document would omit the deviation the client actually signed. **build-dienstplan** no longer
states the Soll column as unconditional, and **using-alluvo-operator** routes the two new questions
("wo ist die KW hin / wo finde ich die AÜV-Nummer", "Soll-Spalte fehlt").

### Changed — 2026-08-07 Einsatz-Ansprechpartner ist eine Platzierung ohne Rolle, kein Viewer-Login (alluvo#3450)
Naming an **Ansprechpartner vor Ort** on an Einsatz (`contact_id`) no longer produces a portal
login. It now creates a **placement** — a grant with *no* role, at the Einsatz's Einsatzbetrieb
and Abteilung — because who to call about an Einsatz is a location fact, not an access decision.
The `viewer` grants this group had inherited from the client-portal rollout backfill were revoked
(except for contract recipients and anyone with an actual account), so a long-standing
Ansprechpartner may have no access today. **manage-contract-lifecycle** gains the contrast
missing from both sides of the same contract: an **Empfänger** gets membership + `viewer` (they
were mailed the contract and must open it), an **Ansprechpartner vor Ort** gets a placement and
nothing else — so a skill must never read "Ansprechpartner eingetragen" as "kann sich anmelden",
and someone who is both keeps the `viewer` *and* gains a placement, appearing legitimately twice
in the Organigramm. **approve-stundenfreigabe** — which carries the access model — now says where
placements come from, that the placement's Einsatzbetrieb follows the §11 correction chain
(`client_site_correction_id`/department correction before the contract, same waterfall as the
Einsatzmitteilung), that placing **sends nothing** (invitations come only from
`send-portal-invitation`), and that **swapping the contact leaves the old placement standing** —
so an Organigramm node is not evidence of who the *current* Ansprechpartner is. Two corrections
to the existing placement note: a placement shows someone in the **Organigramm**, not on the
customer-facing Ansprechpartner list (a separate, independent designation), and at one and the
same position a real role wins the badge rather than showing a competing "no role" entry.
Confirming hours still requires an explicit **`approver`** assignment.

### Changed — 2026-08-07 Beleg einreichen: sichtbar im Katalog, nicht ausführbar über MCP (alluvo#3420)
A new `submit_beleg` record action lets an operator file a receipt on an employee's behalf
(`0-2`, "…" menu, one image/PDF up to 10 MB, same extraction pipeline as the employee app).
`manage-record-action` **lists and previews** it like any other action but cannot execute it —
its only field is a real file upload and the tool carries JSON, so `confirmed: true` fails with
a "no file" error. **approve-stundenfreigabe** now says so outright, so the action appearing in
a `list` result is not read as proof it can be run, and three follow-on facts are recorded:
an upload creates an *extraction job*, not a `0-20` record — the draft `Reimbursement` only
exists once the extraction is reviewed and confirmed in the app, so `query-model` showing
nothing straight after an upload is correct, not a failure; a draft **an operator filed is
invisible to the employee** until it leaves draft, because their own list shows only drafts they
created themselves; and acting on an employee's behalf across the whole extraction pipeline
(Beleg, Stundenzettel, Dienstplan) requires edit permission on that employee — a missing one is
refused, never quietly filed onto the operator. The Freigeber gate gains its default: the step
is tenant-flagged and **off**, so `authorized_by_id: null` is the normal case and not a missing
approver; where it is on it binds only Auslagen (`EXPENSES`) without one on file, never
Reisekosten.

### Changed — 2026-08-07 `query-model` includes waren abgeschnitten, „Signed in" hieß nicht angemeldet (alluvo#3415)
Two silent-wrong-answer surfaces under `query-model`, plus two newly readable ones.
**Includes were truncated:** the per-relation `limit` was applied as one flat SQL `LIMIT` across
all parent rows instead of per parent, so an include returned at most ~10 related rows *in total*
— at 25 root records per page, practically every relational query. Any completeness claim a skill
derived from an include ("dieser Vertrag hat einen Empfänger") rested on cut-off data. Now correct
per record. **Deleted linked records are no longer passed over in silence:** soft-deleted rows stay
out of the payload, but the caller gets a warning naming the count and the reason. The navigator
**using-alluvo-operator** gains a short cross-cutting `query-model` section stating all three
facts — a warning is a *finding*, includes are limited per parent, and pivot columns must be asked
for. **manage-contract-lifecycle** applies it to recipients: a contract showing one healthy
recipient may have four with the **Hauptempfänger** among the deleted, and a contract whose
primary recipient is a deleted contact is neither sendable nor signable — so the warning is a
data-quality finding to repair before `send_for_signoff`, not noise. It also documents the new
`include: { recipients: { pivot: true } }` / `{ pivot: ["is_primary"] }`, which makes **who the
primary recipient is** readable for the first time instead of inferred from list order.
**approve-stundenfreigabe** corrects a claim that was simply wrong: `has_portal_login` means a
portal **account exists**, not that anyone signed in — the on-device Stundenfreigabe signing flow
provisions an account with no login involved. Only `portal_invitation_status = logged_in` proves a
sign-in, and it is **not retroactive**: for contacts whose last sign-in predates the change the
field is empty, so an empty one is no evidence that nobody ever logged in. The
`assign-portal-roles` availability gate is restated accordingly in both skills (account exists,
not signed in). Finally, **PortalMembership (`0-430`) is now filterable** on `company_id`,
`contact_id`, `status` and `grants.role` (two-hop dotted path) — "wer hat bei Firma X Zugang",
"welche Zugänge sind deaktiviert", "wer ist irgendwo Administrator" are direct queries instead of
free-text search or parsing the `portal_scope_label` prose.

### Changed — 2026-08-07 Empfänger eines Vertrags bekommt den Portalzugang automatisch (alluvo#3406)
Being a contract recipient and being able to open the contract were two unconnected facts:
attaching a recipient wrote only the pivot row, and it appeared to work solely because the
client-portal rollout backfill had handed every company contact a `viewer` grant. Revoking that
unused cohort removed the coincidence and left contracts out for signature whose primary
recipient could not authenticate. Attaching a recipient — via `recipient_contact_ids`, the
`add_contract_recipient` action, `new_recipient_contact_ids` on a resend, or `create` on a
Rahmenvertrag — now provisions the membership plus a **`viewer`** grant at that company.
**manage-contract-lifecycle** reframes its pre-`send_for_signoff` block accordingly: adding a
recipient is an **access decision**, not just addressing an email, and should be named as such to
the operator. Two invariants it now states — an existing role-bearing grant is never widened or
narrowed, and a **disabled** membership is deliberately left disabled (the contract still sends,
the person stays locked out until someone re-enables them via `assign-portal-roles` with
`portal_access_active: true`). Also corrected: never assign a *stronger* role "so they can sign".
`viewer` supplies only the authentication — signing is authorised by being attached to that
contract, regardless of role or site scope — so a site-scoped role does not lock a recipient out
of signing, it only decides what else they see. **approve-stundenfreigabe**, which documents the
access model in full, notes this as the one exception to "portal access is opt-in", and that it
is *not* sufficient for Stundenfreigabe: confirming hours still needs an explicit **`approver`**
assignment. Its note on pre-existing access is corrected too — the backfilled `viewer` grants for
contacts who never had a login were revoked, so a long-standing Ansprechpartner may have none.

### Changed — 2026-08-07 Portal-Zugang ist zwei Fragen, nicht eine (alluvo#3342)
The person↔company portal relationship moved onto a single membership aggregate, and with it the
answer to "can this client contact sign in" became a **two-part** predicate: the membership must
be `active` **and** carry at least one grant that names a role. **approve-stundenfreigabe** now
states both halves and warns that a *placement* grant — someone attached to an Einsatzbetrieb or
Abteilung with no role — lists a person in the Organigramm while granting them **no** login, so
"has a row at the company" never answers "can they confirm the hours". The consequence operators
most needed spelled out: **revoking access and removing roles are now distinct operations**.
`portal_access_active: false` on `assign-portal-roles` disables the membership and the person
keeps every role they hold — reversible, and the right tool for a temporary lockout — whereas
clearing the role list is destructive: it deletes the grants along with their site/department
scoping, and restoring them means rebuilding each assignment by hand. A skill that cleared roles
to lock someone out was doing the wrong thing. New read surface: **PortalMembership (`0-430`)**
is now queryable, one row per (company, contact) with `status`, `portal_roles_label`,
`portal_scope_label`, `portal_invitation_status` and `has_portal_login` — the skill documents it
as the way to check access instead of guessing, plus the trap that `function_title` is the
person's job ("Pflegedienstleitung") and not a portal permission. `CompanyContactPerson`
(`0-361`) stays the type for counting Ansprechpartner in CRM work but is no longer the
portal-access answer. **manage-contract-lifecycle** applies the same check before
`send_for_signoff` (a reachable recipient still may not be able to sign), and
**using-alluvo-operator** routes portal-access questions to `0-430` rather than the contact list.
The role catalog and permission semantics are unchanged, and existing access was backfilled to
`active` — nobody lost a login.

### Changed — 2026-08-07 Eine Portal-Rolle gilt jetzt irgendwo, nicht überall (alluvo#3226)
Client-portal role assignment gained a **scope axis**, and both MCP-exposed portal actions
changed their parameter shape with it: `send-portal-invitation` and `assign-portal-roles` no
longer take `roles` (a list of role values) but **`assignments`** — a list of objects
`{ role, client_site_id, department_ids }`. `client_site_id: null` is the unchanged company-wide
role; an Einsatzbetrieb id scopes the role to that site, and a non-empty `department_ids`
narrows it further to Abteilungen that must sit under that same site. The catalog gained a sixth
role, **`site_admin`** — a per-Einsatzbetrieb administrator holding everything a company
`administrator` does *except* billing management, and it **must** carry a `client_site_id` while
`administrator` must **not**. **approve-stundenfreigabe** documents the new shape, both scope
rules, and what scoping buys an operator: a site-scoped `approver` reaches that Einsatzbetrieb's
Wochennachweise and no other, so "Haus 1 soll Haus 2 nicht sehen" is a role assignment now
rather than a workaround. Two traps are called out because they cost a person their login:
`assignments` is a **full replace**, so sending a bare list of role names (the old shape) or
calling `assign-portal-roles` with only `portal_access_active` collapses the list to empty and
deletes every grant; and an unknown role value is silently dropped rather than rejected, so a
typo is a quiet no-op. **manage-contract-lifecycle** carries the same shape at the
`send_for_signoff` access check, plus the signer-specific consequence: a site-scoped role only
reaches that site's Einsatzverträge, so it does not unlock a contract sitting elsewhere. Nothing
was migrated — every pre-existing assignment is company-wide and behaves exactly as before.

### Added — 2026-08-07 Der digitale Personalfragebogen ist ein Workflow, kein Diktat mehr (alluvo#3373)
Master data used to be dictated field by field; there is now a guest link the person fills in
themselves. **onboard-new-employee** gains step 2a for the whole loop and the old manual step
becomes the paper-form fallback. Asking runs `request-employee-master-data` through
`manage-record-action` on Employee (`0-2`), Candidate (`0-81`) or Contact (`0-105`) — it needs a
linked Candidate *with an email*, and the mail goes to that candidate's address, not to one held
on the Employee. The one thing an operator must hear before confirming: while an unfinished link
is open the call re-sends that same link, but once the person has completed one, the identical
call starts a **brand-new, empty** questionnaire under a new link instead of reviving the old one
— previous answers untouched either way, so a single wrong value gets corrected on the record,
not by re-sending. Taking the answers over runs `apply-employee-master-data` on the submission
(`EmployeeMasterDataSubmission`, `0-429`) with `data: {"accepted_keys": [...]}`; only the passed
keys are written, a blank answer never overwrites a stored value, tax data opens a **new**
TaxProfile version rather than overwriting the current one, a second call is a no-op, and the
signed PDF is filed as the `onboarding_questionnaire` document — which closes the always-mandatory
Personalfragebogen requirement by itself, so nobody should chase a scan for it any more. Three
corrections the skills now make explicitly: the submission is **read-only** over MCP (allowlisted
but not `manage-model`-manageable); the **answers never reach the session** — `data` is encrypted
and hidden, so only `status`, `filled_keys_count` and the signature/apply timestamps come back,
and the key list has to be read in the web app (the apply tool's description points at
`filled_keys`, which is not exposed — alluvo#3382); and **Anschrift is not a field on the
Contact**, it resolves to the Location under the home purpose. **using-alluvo-operator** routes
"Stammdaten anfordern" / "Personalfragebogen schicken" here instead of to a manual walkthrough.

### Changed — 2026-08-06 Der Tätigkeitsnachweis zeigt jetzt den Plan, die Lücken und die Krankmeldung (alluvo#3371)
The § 17c AÜG sheet the Entleiher signs was rebuilt, and since the skills describe that flow they
described the old sheet. No tool, parameter or enum changed — only what the document says.
**approve-stundenfreigabe** gains a section on what the Nachweis actually puts in front of the
client: rows grouped per Kalenderwoche with a Soll/Ist/Abw. subtotal per group (a period is four to
five weeks under any month-aligned scheme, so one flat total was unreadable), a new **Soll** column
read off the timesheet day's frozen `soll_*` rather than today's Dienstplan, a new **Abw.** column
taken from the stored `deviation_minutes` and **suppressed on an `extra` day** — so an empty Abw.
beside real hours is correct, not a missing number — and planned-but-unworked days marked as
highlighted gaps carrying "Nicht gearbeitet". Two corrections it has to make explicitly:
**"Einsatzzeitraum (Gesamt)" is removed**, and the range that remains is the period's first and
last *worked* day, so the Vertragslaufzeit can no longer be read off the sheet (that was the point);
and the empty-rows setting now also keeps **gap rows**, not just days with a Bemerkung — the
existing bullet claimed less than the filter does. **record-absence** documents the side effect
nobody would guess from the absence form: an **approved** absence in any of the three incapacity
categories (`SICK_LEAVE`, `SICK_LEAVE_WITHOUT_PAY`, `CHILD_CARE`) prints exactly one word, "Krank",
on a customer-facing document — deliberately collapsed, because the sheet documents attendance and
not the wage type, and "Kind krank" does not belong in front of a client; a *submitted* Krankmeldung
prints nothing, and a manual note is appended rather than replaced. **build-dienstplan** notes that
the plan is now visible to the customer through the Soll column, and that the printed Soll is frozen
per day — retiming a Schicht does not repair a number on an issued Nachweis, the Stundenklärung
does. **using-alluvo-operator** routes "warum steht da Krank / wo ist der Einsatzzeitraum hin".

### Added — 2026-08-06 Eine genehmigte Krankmeldung ist der Anfang der Ersatzsuche, nicht ihr Ende (alluvo#3365)
A Schicht now carries a lifecycle status of its own — `planned` · `replacement_needed` ·
`reassigned` · `cancelled` — and it, not `cancelled_at`, decides whether the Schicht still counts.
Approving an Abwesenheit moves every uncovered Schicht in the window to `replacement_needed` and
returns them as `affected_shifts`. **record-absence** stops at "genehmigt" no longer: a new section
tells the assistant to relay that list grouped by client and offer the Umbesetzung per distinct
`assignment_id`, cancelling only where no replacement exists. Three things it has to say because
they are counter-intuitive — there is **no `confirmed: false` preview** that returns the list
(`manage-record-action`'s preview path is wholly generic and calls nothing action-specific, so
promising to "preview which Schichten are affected" describes a call that returns nothing);
**`execute_bulk` discards response data entirely**, so bulk-approving imported zvoove Urlaube
silently drops every `affected_shifts` and the list is capped at 20 rows besides; and Schichten
that carry tracked time are **left alone**, so a late AU never retroactively unmakes hours somebody
demonstrably worked. **build-dienstplan** documents the status table, that `reassigned` and
`cancelled` are finally distinguishable (they used to be the same stamped `cancelled_at`), that
both are terminal and survive a withdrawn Krankmeldung, that `remove-shift` with `cancel: true` now
sets the status too, that only live Schichten move in an Umbesetzung — and that `manage-shift-plan`
`list` still prints `Cancelled` off `cancelled_at`, so a `replacement_needed` Schicht reads as an
ordinary planned one. **triage-data-quality** gains the `staffing` category and its single member,
`UncoveredShiftsDuringAbsence` on the Einsatz (one per Einsatz, not per Schicht; self-closing;
route it to Disposition rather than triaging it) — which is also the only queryable surface, since
Shift (`0-111`) stayed **off** the MCP allowlist when it gained the status; the corrected claim is
in both skills. **approve-stundenfreigabe**: a day covered by an *approved* absence owes no
Tagesabschluss at all and can no longer wall off a week's release (a *submitted* Krankmeldung
discharges nothing), and a `replacement_needed` Schicht is not Soll — so a week whose Sollstunden
dropped after an approval is correct. **bench-check** reads open `staffing` issues as
already-contracted demand, **match-bench-to-clients** warns that an uncovered Schicht is not a
StaffingDemand and must not be answered with a second Einsatzvertrag, and
**using-alluvo-operator** routes "wer übernimmt jetzt die Schichten?".

Three corrections on top of that pass. The Issue is self-closing but **not instantly** — no shift
write re-evaluates it (`checkForIssues` is called from the absence synchronizer, never from a
Schicht write), so it clears on the nightly data-quality sweep; all three skills now say an Issue
still open right after a completed Umbesetzung is expected, and to verify against the Schichten
rather than the Issue. A `replacement_needed` Schicht **already in the past is a dead end**: a
backdated Krankmeldung routinely marks days that have passed, and those can be neither umbesetzt
(`shift_already_started`) nor cancelled (`remove-shift` refuses a started or past Schicht), so they
stay `replacement_needed` permanently and hold the Issue open — **record-absence** now says to
dismiss it rather than hunt for a fix, and to offer the Umbesetzung only for days still ahead. And
**build-dienstplan**'s publish section no longer claims "a Schicht has no status of its own (only
`cancelled_at`)", which the same file now contradicts a few hundred lines earlier — publication
lives on the Periode, and the Schicht's status is a lifecycle state with no "published" value.
### Added — 2026-08-06 Die Fuhrpark-Fristvorgabe war nie auf der Einstellungsseite (alluvo#3367)
`manage-settings` gained a **`fleet`** group, so the two tenant-wide Fuhrpark settings are
finally reachable over MCP: `mileage_request_due_days` (int, 1–90, default 3 — the deadline a
`request_mileage` gets when the call carries no `due_in_days`) and `usage_notes` (array, max 20
entries à ≤255 chars — the "Wichtige Hinweise für die Fahrzeugnutzung" every employee reads
verbatim on *Mein Fahrzeug*). **onboard-new-employee** step 2d documented the opposite and sent
the operator to a settings page for the deadline; that page never carried it — `FleetSettings`
only ever exposed `usage_notes` to the web UI, so MCP is not the second way to change the
deadline, it is the **only** way. The skill now carries the group with both fields, the warning
that a `usage_notes` update **replaces the whole list** (read first, send the full array back,
or you delete the other hints), the note that `usage_notes` *is* web-editable and may have moved
under you, and that changing the default leaves existing requests alone. The per-request
`due_in_days` override is unchanged and still right — plus the edge it never spelled out:
`due_in_days: 0` creates a request with no deadline, which never goes overdue and therefore
never pushes. **using-alluvo-operator** stops claiming the Fristvorgabe lives in the web app and
routes "Standardfrist ändern / Hinweise zur Fahrzeugnutzung" at the `fleet` group; only
assigning a vehicle **to an employee** is still web-only.

### Added — 2026-08-06 Kürzerer Tätigkeitsnachweis, und die Stoppuhr sagt jetzt wirklich nein (alluvo#3251)
Two things **approve-stundenfreigabe** could not answer. First, "der Tätigkeitsnachweis ist
voller leerer Zeilen": the PDF lists every calendar day of the period, and since a period is
normally a month segment, a weekend-only Einsatz prints five dash-filled rows for every two
real ones. `taetigkeitsnachweis_show_empty_days` (bool, default `true`) is now a writable
`timesheet` field on `manage-settings` and the skill documents the three things the copy has
to get right: a day carrying a **Bemerkung is never dropped** (the note is the only thing that
row says, so "der Tag mit der Notiz fehlt" is a missing time entry, not this flag); it is
**presentation only**, so the answer to "ändert das die Rechnung?" is a plain no; and it is
**overridable per client company** via `manage-record-settings` (`0-3`,
`timesheet.taetigkeitsnachweis_show_empty_days`), so "nur für diesen Kunden kürzer" is a real
request rather than a tenant-wide compromise. Second, clock-in can now be refused for a reason
the skills did not know: the tenant's `live_timer_enabled` — **off by default** — was a UI
concern only, hiding the button while the API accepted the call anyway; it is now a
server-side rule that returns a 422 (`TIMER_STATE`, *"Die Stoppuhr ist für dein Unternehmen
nicht aktiviert…"*). A new section says never to answer a time-capture question with "tap
Einstempeln" before checking that toggle — the working answers are manual entry or taking the
Dienstplan — notes that **only clock-in is gated** (Ausstempeln, Pause and Fortsetzen stay
open so a timer running when the setting flipped can still be closed, which makes "ich kann
nicht ausstempeln" a different fault), that it is **not** an MCP setting (there is no
`time_tracking` group — it lives in Einstellungen → Zeiterfassung), and that switching it off
does not retro-clean a stray entry it already let through. **using-alluvo-operator** routes
both symptoms.

### Added — 2026-08-06 Ein falsch gelandetes Ticket wird verschoben, nicht geschlossen (alluvo#3250)
Until now a ticket in the wrong queue had two outs: close it, or forward it out of alluvo
entirely. `manage-ticket` gained a third — `move_to_inbox` (`ticket_id` + destination
`inbox_id`) — and **clean-inbox** now treats "wrong inbox" as its own triage cluster instead
of a reason to close. The section spells out what the tool actually guarantees: the
destination may be **any** inbox in the tenant (an operator who staffs one queue must still be
able to delegate), while access to the ticket itself is unchanged and still runs through its
*current* inbox; the move is idempotent; it writes a system note into the thread; and — the
part that matters when the ticket is already breaching — **SLA deadlines and followers are
left running untouched**, so a move neither buys time nor puts anyone in the new inbox on the
hook. The close checkpoint gained `move_to_inbox` to its no-preview list and now says plainly
that closing is for a settled matter, not for a ticket that merely isn't yours.
`manage-ticket action=get` also reports more than it used to: alongside contacts and companies
it now prints **linked vehicles, tasks and the WhatsApp campaign**. The skill reads that block
before concluding anything is missing — a vehicle the agent already linked off a
Fahrzeugrückgabe mail, or a task somebody already filed against the ticket, was previously
invisible, and re-asking the sender for it is the failure that produced this change.
**build-automation-agent** documents the four new ticket-control steps a deployment can opt
into (`close_ticket`, `set_ticket_status`, `assign_ticket`, `set_ticket_priority`) with their
directive fields, and states the two things that decide whether to grant them: each is a
**single gated step for every trigger source** — an unattended inbox deployment cannot close,
re-status, reassign or re-prioritise a ticket without a human approving the card — and all
four are **absent from the default whitelist**, so nothing changes for an existing deployment.
The gating sentence, which claimed only `send_email`/`send_invite` paused, is corrected to the
real set. The evidence rule is restated where it now bites: an agent proposal is not evidence;
whoever approves the close reason owns it. **using-alluvo-operator** routes "Ticket in eine
andere Inbox verschieben" to `clean-inbox`.

### Added — 2026-08-06 Der Stundennachweis bekommt eine Operator-Oberfläche (alluvo#3223)
An approval period had no internal surface at all — the Stundenklärung queue lists only disputed
periods, so a pending or approved one was visible to the client and the employee but nowhere to an
operator, and the signed Tätigkeitsnachweis PDF was reachable only by hand-assembling a URL. There
is now a read-only **Stundennachweise** list in the web app. **approve-stundenfreigabe** documents
it: where it sits (HR & Payroll, between Zeiteinträge and Stundenklärung), what it shows and filters,
its per-status views, and the two link actions — "Tätigkeitsnachweis öffnen" (only on `approved` /
`invoiced`) and "Zur Vermittlung" (only on `disputed` / `escalated` / `mediating`). The stale
navigation path "Zeiterfassung → Freigaben", which named no menu that exists, is replaced by the
real one.
The load-bearing part is what the skill now refuses to promise: `TimesheetWeek` (`0-426`),
`TimesheetDay` (`0-427`) and `TimesheetDayCorrection` (`0-428`) are **not on the MCP allowlist**, so
they are absent from `list-model-types` and every generic tool — `search-model`, `query-model`,
`get-model`, `count-model`, `get-model-schema`, `manage-model` and `manage-record-action` — refuses
them, as does an automation workflow's `trigger_model_type`. The two actions are therefore things to
tell an operator to click, never things to offer to run, and any period figure still comes from
`TimeEntry` (`0-6`). The read-only stance is given with its reason (status, minutes and
confirmations are lifecycle state owned by `TimesheetConfirmationService` and the mediation flow; a
generic update would bypass the two-sided release), so it does not read as a gap to route around.
A missing menu entry is named as the new `timesheet_weeks.view` permission rather than a rollout
problem. **head-of-disposition** points the Stundenfreigabe backlog at the list's per-status views
as *where to look* while still building its number from `TimeEntry`; **build-dienstplan** answers
"did the published month's hours come back signed"; **using-alluvo-operator** routes
"Stundennachweise / Tätigkeitsnachweis / Zeitraum im Backend" there.

### Added — 2026-08-06 Kilometerstand beim Fahrer anfragen (alluvo#3348)
An operator who does not know a vehicle's Kilometerstand can now ask for it instead of guessing.
**onboard-new-employee** (step 2d) documents the `request_mileage` record action on the Vehicle
(`0-4`), run through `manage-record-action` with the usual `confirmed: false` preview and an
optional `data: {"due_in_days": <n>}`. It states plainly that creating a **VehicleMileageRequest**
(`0-425`) by hand with `manage-model` is the wrong path even though the type accepts it — only the
action resolves the recipient, so a hand-made request can land on nobody. The three block reasons
(driver without app login → invite first; neither driver nor responsible person; an already open
request) and the *non*-block where a missing driver routes the request to the responsible person
are given as reasons to pass on, not to work around. Closing is covered too: any reading (`0-424`)
fulfils every open request for that vehicle, whoever entered it, so there is no separate close call
and `fulfilled_by_reading_id` is never set by hand — withdrawing is `status: cancelled`. Also noted
that the driver gets no push until the deadline passes, so nobody promises an instant ping, and
that the tenant's default deadline is **not** reachable over `manage-settings` (it has no `fleet`
group) — pass `due_in_days` per request and change the default in the web app.
**using-alluvo-operator** routes "Kilometerstand beim Fahrer anfragen" to the same step.

### Changed — 2026-08-06 Krankmeldung telefonisch nachmelden (alluvo#3344)
An AbsenceType now carries `requires_immediate_call`, and an absence of a flagged type makes the
employee's app ask them to phone it in — to the agency and to the on-site contact of the covered
shift. **record-absence** learns the flag exists (readable on `AbsenceType` `0-14`) and, more
usefully, that the prompt is **not** limited to the employee's own submission: their absence list
rebuilds it for any flagged absence that has not yet ended, whoever created it, so a Krankmeldung an
operator enters still asks that employee to call. Three things the skill states plainly because the
surface does not match the obvious expectation: the flag was backfilled by key, so a "Kind krank"
row keyed `SICK_LEAVE_WITHOUT_PAY` is flagged too and probably should not be; the flag is **not**
settable from here, since `0-14` is read-only reference data and `manage-model` rejects the write;
and the office number behind it is resolved through a waterfall, not a single field. The three
settings that drive it — `general.company_phone`, `general.company_employee_phone` and
`employee_app.employee_phone_priority` — are readable and writable over `manage-settings`
(the `employee_app` group was added for this, alluvo#3349). It also documents the data-quality gap
the feature exposes: the on-site block is dropped entirely unless the resolved contact carries a
`phone` or `mobile`, so an Einsatz whose contact was never given a number silently shows a sick
employee nobody to call on site.

### Changed — 2026-08-06 Feiertage folgen dem Einsatzort (alluvo#3339)
Public holidays are computed per Bundesland and resolved from the **Einsatzort** of the day in
question — the Location of the Einsatzbetrieb, never the employee's home address and never one
national list. Four skills learn what that means for an operator. **triage-data-quality** documents
the new high-severity `Unresolvable Federal State` issue on a Location (`0-95`) and the trap in
fixing it: it is a `manage-model` `update`, **not** `manage-location`, which carries no
`subdivision_code` parameter at all, so the value silently never lands; correcting `zip` is the
better fix because the Bundesland is derived from it, and `subdivision_code` is ISO 3166-2
(`"DE-NW"`) unlike the bare code stored elsewhere. It also names why the issue is urgent — a
billing run containing such a site is refused at invoice generation — and that foreign addresses
never raise it. **build-dienstplan** stops claiming the shift-write path checks a Feiertag: its
§§9/10 gate fires on Sundays only, Feiertagsruhe is enforced on the timesheet side, and there it is
Einsatzort-scoped, so one date can be a Feiertag for one Einsatz and an ordinary day for another.
**record-absence** notes that vacation days are counted against the Einsatzort's holidays resolved
per day, so identical dates can cost two employees a different number of days. **manage-contract-
lifecycle** separates `applies_on_holidays` (whether a surcharge applies) from which days *are*
Feiertage (the Einsatzbetrieb's Bundesland, per shift), and warns that totals moved in both
directions — lower where a foreign state's holiday was being paid, higher where one was missing
(Reformationstag in HB/HH/NI/SH) — which is a correction, not grounds to adjust a rate. All four
name the unresolved-Bundesland fallback: only the nine nationwide holidays apply, which understates
the picture.

### Changed — 2026-08-06 Dated contract/Einsatz termination (alluvo#3329)
`mark_performed` is gone. **manage-contract-lifecycle** step 6 is rewritten around the two actions
that replace it: `end_contract` ("Vertrag beenden") on AssignmentContract `0-31` and
`end_assignment` ("Einsatz beenden") on Assignment `0-401`, both via `manage-record-action`. The
end date is now free — past, today or future — with a required `reason` that is quoted verbatim to
the employee, and post-cutoff Schichten are cancelled automatically, so the old
`confirm_future_shifts` acknowledgement (and the stranded shifts it warned about) is gone with it.
The skill spells out the call shape that is easy to get wrong: the two-stage flag lives **inside
`data`** (`data.confirmed`), the tool's top-level `confirmed` is a separate switch that must always
be `true`, **omitting `data.confirmed` executes**, and the `# Action Executed` banner is generic
tooling output on an unconfirmed call — `preview_only` in the Response Data is the only proof of a
write. Also documented: the cutoff day's own Schicht is kept, the three per-Einsatz outcomes
(untouched / shortened+`Terminated` / `Cancelled`), a past-or-today date marking the contract
`Performed` at once while a future date leaves it running for the nightly sweep, the §1 AÜG
blockers (no end before the contract start or behind an already-started Schicht), and what the
narrowed cascade does differently from a Storno (always cancel-mode, Dienstplan-Perioden untouched,
only post-cutoff availability released, employee mailed even without a prior §11 Einsatzmitteilung
when they lose Schichten). **build-dienstplan** learns that a still-`won` contract can legitimately
show cancelled Schichten past a date plus an inert Periode, and that the §11 re-send window is read
from the status — not `valid_until` — since a future-dated end leaves the contract in force.
**using-alluvo-operator** routes "Vertrag beenden" / "Einsatz beenden" to the lifecycle skill.

### Changed — 2026-08-06 Der kommende Zeitraum ist im Mitarbeiter-PWA sichtbar (alluvo#3338)
The employee's „Ausstehende Aufgaben" card and the Freigabe-Wizard now preview the **next**
approval period — „Danach: <Zeitraum>" with „Freigabe ab TT.MM. möglich" on the start page, a
dashed „Kommt als Nächstes" card with a disabled checkbox in step 1. **approve-stundenfreigabe**
gains a section next to the three urgency states: the preview is a projection from the Einsatz's
Abrechnungszeitraum with **no `TimesheetWeek` behind it**, so it carries no Frist, is not in the
red badge, is never promoted to `PendingClient`, is never reminded about, and cannot be found by
any `query-model` — an employee quoting it is not reporting a lost period. It shows only when the
projected period has planned Schichten (the same `effective()` rule as the Soll), is clamped to
the Einsatzende, and starts after the Einsatz's last existing period rather than on the next
scheme boundary, so it stays correct across an Abrechnungszeitraum switch. It is deliberately not
clickable, always sits under „Anstehend", and never makes the card appear on its own.
**head-of-disposition** notes it can never inflate a Draft backlog figure;
**using-alluvo-operator** routes „Danach" / „Kommt als Nächstes" / „der Zeitraum lässt sich nicht
anklicken" to the skill. No MCP tool, schema or action changed.

### Added — 2026-08-06 Personalakte-Dokument an die 1:1-Mail anhängen (alluvo#3335)
`manage-1on1-email` accepts `employee_document_ids` on `draft` and `update` — EmployeeDocument
ids (`0-346`), not media ids, findable via `audit-employee-documents` — so a Berufsurkunde or
an Impfnachweis can accompany a profile. **profilvertrieb** documents it where the acquisition
email is composed (step 6b): the profile still travels as the public **link**
(`build-profile-links-block` is unchanged) and attaching a file is a separate act on personnel
data, so it happens only when the operator asks. Sending is opt-in per tenant and the release
list is **empty by default**, so the skill never promises an attachment — it attempts it and
relays the refusal, which names the released types. Refusals also cover a tenant-defined type
(never attachable), a non-`active` or expired document, one without a file, and one the user
may not view; nothing above the „a client may see this anyway" ceiling can ever be released, so
an Arbeitsvertrag or a Lohnabrechnung is never offered. The unconfirmed preview names the
employee, the type and every file with its size and must be read out in full — „1 attachment"
is not something anyone can confirm about Art. 9 GDPR data. The attachment is a copy taken at
draft/update time (`send` does not re-check it) and the tool can neither remove an attachment
nor delete a draft — the wrong document means composing a new draft, not sending. **call-summary**
gets the short version for a Nachweis promised on a call, **onboard-new-employee** notes that
filing a document is what makes it sendable later and that filing does not release it.

### Changed — 2026-08-06 Schlüssel und Versicherung sind doch verknüpfbar (alluvo#3328)
Correction to the entry below, which shipped in the same Unreleased block: `KeyForm` and
`InsuranceForm` now carry a `vehicles` relation field, so `manage-model` syncs the
`key_vehicle` / `insurables` pivot on **create and update** — `vehicles: [<vehicle_id>]`,
where the list replaces the current set. The „stays in the web app" note for **Schlüssel**
(`0-52`) and **Versicherung** (`0-63`) is gone from **onboard-new-employee** (step 2d) and
**using-alluvo-operator**; only assigning a vehicle **to an employee** (`employee_vehicle`)
is still web-app only, and that is what the „report the gap instead of parking data in
`notes`" rule now refers to. The insurance pivot's own terms (`valid_from` / `valid_until`,
`premium_amount`, `coverage_amount`) remain deliberately off the MCP surface — they stay on
the vehicle's Versicherungen tab. With this, all nine points of a „Fahrzeugdaten
vervollständigen" task are doable through the assistant.

### Added — 2026-08-06 Fuhrpark über MCP bedienbar (alluvo#3324)
Seven fleet model types joined the MCP surface: `VehicleMileageReading` (`0-424`, a new
model), `FuelCard` (`0-56`), `Key` (`0-52`), `Insurance` (`0-63`), `VehicleLease` (`0-65`,
with the new `contracted_mileage_km`), `VehicleAsset` (`0-64`) and `VehicleRental` (`0-66`).
`Vehicle` (`0-4`) gained a writable `first_registration_date` plus the read-only
`current_mileage_km` / `current_mileage_recorded_at`. Until now the assistant could set a
vehicle's colour but not do what the operator handbook literally asks of it — link a fuel
card, enter lease terms, record a Kilometerstand — and the fleet import parked those values
in a `[fuhrpark-daten]` text block in `vehicles.notes`, which a migration has now lifted into
real columns.

**onboard-new-employee** gains step 2d (Dienstwagen / Fuhrpark), reached from the open
`vehicle` requirement or a „Fahrzeugdaten vervollständigen" task: the required fields per
type, the to-one rule for Lease/Asset/Rental, and the two hard conventions — a Kilometerstand
is **always a new `0-424` reading** (`recorded_at` is the reading date, `source` defaults to
`operator`), never a write on the vehicle, because an observer recomputes the vehicle's
projection from the readings; and fleet data never goes back into `notes`. One limit is
stated rather than improvised around: assigning a vehicle **to an employee** is web-app only.
(The `Key` / `Insurance` limit this entry originally claimed was lifted before release — see
the entry above.) **using-alluvo-operator** routes Fuhrpark/Tankkarte/Kilometerstand there.

### Changed — 2026-08-06 Fünf reine Nachweis-Dokumenttypen entfallen (alluvo#3321)
`id_document`, `social_security_card`, `tax_id`, `bank_details` and
`health_insurance_proof` were removed from the product. Each existed only to *prove* a
master-data value the system already holds structurally (`social_security_number` /
`tax_id` on the Employee, the IBAN on the BankAccount) or that payroll owns as system of
record — the scan never belonged in the Personalakte. All five were always-mandatory,
which by itself generated ~1000 permanently-open „Dokument fehlt" rows in a single tenant.

**onboard-new-employee** (step 2): the document-backed examples now name types that still
exist (`onboarding_questionnaire`, `employment_contract`, `temp_work_act_info_sheet`), and
the old „`bank_details` ist der Scan, nicht der Datensatz" callout is replaced by the new
truth — there is no Nachweis-Dokument for Ausweis, SV-Ausweis, Steuer-ID, Bankverbindung or
Krankenkasse at all. Recorded with it: those types no longer appear in
`missing_non_blocking` (completeness scores read higher for an unchanged employee — that is
the removal, not a data fix), `manage-employee-document` `action: "create"` rejects the five
codes with `Unknown document type: '<code>'`, and the data goes in as data instead (IBAN →
`BankAccount` per step 2b; `social_security_number` / `tax_id` → Employee fields via
`manage-model`, schema confirmed first). `onboarding_questionnaire` is now the only
always-mandatory Identity type; for non-EU **or unknown** citizenship `residence_permit` +
`work_permit` are additionally mandatory, and the rest of the always-mandatory set is
employer-issued.

**triage-data-quality**: missing-document triage lost five identifiers. The skill no longer
quotes `tax_id` as an example gap, must not propose refiling one of the five, and reads the
live set with `action: "list-types"` instead of naming codes from memory. A sharp drop in
missing-document volume is this cleanup, not a triage win.

Unchanged and explicitly kept: `criminal_record_certificate`,
`extended_criminal_record_certificate`, `school_certificates`, `curriculum_vitae`,
`work_permit`, `a1_certificate`. `clean-inbox` and `record-absence` already resolve codes
via `manage-employee-document` `action: "list-types"` and needed no edit.

### Changed — 2026-08-06 Ein laufender Zeitraum ist nicht mehr „bereit zur Freigabe" (alluvo#3308)
The employee start page's „Ausstehende Aufgaben" card no longer treats every Draft/PendingClient
period as actionable. Each approval period is its own row now, classified into three states:
**überfällig** (`deadline_at` elapsed, grouped under „Überfällig"), **offen** (period ended,
deadline ahead — „bis <Datum>") and **wartend** (period still running — „ab <Datum> freigebbar"
plus „Läuft noch — noch nichts zu tun"). `approve-stundenfreigabe` gained a section for this,
because it changes a diagnosis the skill already owned: *„der Mitarbeiter sieht keine
Stundenfreigabe / kann nicht freigeben"* about the **current** period is now the designed state,
not a Tagesabschluss, go-live or Freischaltungsproblem to chase.

Recorded with it: the still-running test wins over the deadline (a running period is never
reported überfällig), a period without a stamped `deadline_at` shows no badge and falls back to
„offen", the card's header badge counts only the überfällige rows and caps the list at three
periods — so neither a missing red number nor a short list means anything is lost. The candidate
pool is explicitly unchanged (Einsatz clamp, tracked/agreed hours, go-live floor still decide
whether a period exists at all); urgency only ranks what is already there.

Also documented: the deadline the employee works against is the period's own
`TimesheetWeek.deadline_at`, computed per company as period end + `deadline_days_after_week_end`
days at `deadline_time`, company override before tenant default — so „bis wann muss der
Mitarbeiter freigeben" is a per-client answer, never a tenant-wide one and never the old
„Montag 19:00". `head-of-disposition` §1e now names the running period as the first reason a
Draft period is not backlog, ahead of the unclosed-day explanation, and `using-alluvo-operator`
routes the „Läuft noch" symptom before the Tagesabschluss and Go-Live branches.

### Fixed — 2026-08-06 Dublettenerkennung faltet Umlaute, Telefon-Matching gleicht Formate ab (alluvo#3301)
Two identity-hardening changes moved surfaces the skills describe.

`manage-duplicates` `find` — and the Data Quality Dashboard's Duplicates tab, which shares the
same engine — now folds German umlauts and diacritics in its **name-match gate**. On Contact
that gate is load-bearing for the email, alternative-email, phone and mobile rules too (only
the name-only rule skips it), so two records with the *same email* spelled "Göbel" on one and
"Goebel" on the other were previously not grouped at all. `merge-duplicate-companies` and
`triage-data-quality` now say so and warn that the duplicate count **rises** — the detector
catching up, not a data regression. `merge-duplicate-companies` also had the wrong action in
step 1: it named `find-by-field` for the rules-based sweep. Corrected to `find`, with
`find-by-field` kept as its own option and marked as *not* folding umlauts (its normalization
is per field), so a name-field sweep there still splits the two spellings.

`clean-inbox` gains the inbound-number fact: a ticket with no sender address (Vapi call,
WhatsApp) resolves its Contact by comparing three shapes of the number — raw digits, E.164
digits, and German national-format digits — so `+4915785537909` attaches to a Contact stored
as `015785537909` and vice versa. The old digit-only comparison minted a fresh Contact on
every call from a number already on file in the other format, so the skill also points at the
pairs that behaviour left behind as Dubletten to merge.

### Added — 2026-08-06 Neuer Issue-Typ „Kontakt: Mögliche Dublette" (alluvo#3303)
A new data-quality issue definition (`PossibleDuplicateContact`) ships on Contact, so
`triage-data-quality` gained a section (3e) for it and `merge-duplicate-companies` gained the
entry point plus the merge-direction guidance it needs. The finding is raised two ways: an
audit-driven check that fires the moment one of `email`, `phone`, `mobile`, `first_name`,
`last_name` flips from **empty to set** on an already-saved Contact, and the nightly
`issues:check-all` sweep. That first trigger is the part the skills had no way to explain — an
enrichment agent backfilling a signature address is enough to raise it, so the operator sees a
duplicate finding appear on a record nobody visibly touched, days after both contacts were
created. Documented as advisory: the write always succeeded, nothing was rolled back, and the
fix is the existing `manage-duplicates` `preview-merge` → `merge` path.

Recorded with it: only the record that was **written to** carries the issue (the counterparts
are named in its `description`), a corrected value never raises it because only empty→set
counts, and the issue does not reliably clear itself on merge — Contact does not re-check its
issues on save, so it is resolved by hand (`remediation_kind: "manual"`) or by the nightly
sweep. A dismissal is durable: the definition does not re-create a dismissed or resolved
finding, so "two real people who share a name" is answered once, not nightly.

`merge-duplicate-companies` step 3 now says outright that **"more complete" is not "more
useful"** when choosing `keep_id`. In the production case behind this check the correct
survivor was the *phone-only* Contact — it held the calls, tickets, an open task and a
hand-typed availability profile — over the fuller-looking chat-lead record. Since
relationships are re-pointed either way, the direction really decides which id/URL lives on
and whose conflicting values get discarded.

Also corrected while verifying: `triage-data-quality`'s triage ladder in step 2 filtered on
`severity: "critical"` and `"info"`. `IssueSeverity` carries exactly `high`, `medium` and
`low` — both of those return nothing, and the ladder skipped `medium` entirely, which is
precisely the tier the new possible-duplicate finding lands in.

### Fixed — 2026-08-06 Zuschlagssatz-Skala und `is_exclusive` über `sync_surcharges` (alluvo#3273)
`manage-contract-lifecycle` still said `manage-assignment-contract` `sync_surcharges` **cannot**
set `is_exclusive` / `applies_on_holidays` (alluvo#2640) and that `list_surcharges` does not show
them — both are now false: the two keys are validated and written per row, and the listing carries
**Exclusive** and **Holidays** columns. The skill was sending operators to the wizard's Zuschläge
editor for a repair MCP can do. Corrected, with the exact recognized row keys spelled out, since a
misspelled one (`exclusive` instead of `is_exclusive`) is no longer stripped silently — it comes
back in an `⚠️ IGNORED FIELDS (not written)` block that sits inside an otherwise *successful*
response, so the skill has to be told to read it.

New section on the **rate scale**, the part that used to mis-bill quietly: a `percent`
`rate_value` is a FRACTION (`0.25` = 25 %) on both `sync_surcharges` and
`manage-framework-contract` `add_role`/`update_role`, while `list_surcharges` now renders the
*human* percentage (`25 %`, previously the raw `0.25 %` that convinced readers the templates were
wrong). Echoing the rendered number back is exactly the mistake: `sync_surcharges` refuses a
percent row above `1.5` with `IMPLAUSIBLE_SURCHARGE_RATE` and writes nothing — at
`confirmed: false` already — where before it stored `25` as 2500 %. `acknowledge_unusual_rate:
true` overrides it, but only after the operator confirms a >150 % surcharge is real. Flagged too
that `add_role`/`update_role` carry **no** such guard, so a mis-scaled role surcharge there is
still stored as sent.

### Fixed — 2026-08-05 Leere Freigabezeiträume verschwinden aus dem Kundenportal (alluvo#3222)
`approve-stundenfreigabe` scoped the hidden-empty-period rule too narrowly: it read as if only a
**planning-only** card (one with no Wochennachweis) could be dropped. The client-portal hub drops
any period with no Schicht rows, `Soll = 0` **and** `Ist = 0` — a *materialised* Wochennachweis
included, which is exactly the production case (`01.08.–02.08.2026`, the scheme's first segment
clamped against an Einsatz starting mid-segment) that used to render "Noch keine Dienstpläne
vorhanden · 0h 0min · 0h 0min" beside a Freigeben button releasing nothing. Two facts the skill was
missing: a period already **freigegeben or abgerechnet** stays visible even when empty, so an
approval is never hidden from whoever gave it; and a client seeing fewer cards than the month has
periods is now expected — the answer is "da ist nichts drin", not a missing Freischaltung, role or
Freigabe. Nothing is left unchased by it: the nightly run only promotes periods with tracked hours,
so an empty one never reaches `PendingClient`, and the employee's release list excludes it too.
Also recorded: the plan list's **"Offene Freigaben"** filter now counts the rendered cards, so
filter and list cannot disagree — and it is a different figure from the hub's top KPI **"Offene
Wochen"**, still a plain `Draft` + `PendingClient` count that includes hidden cards.

The same section's claim that "the nightly deadline run is **broader** than the employee's own
list" is corrected while verifying this: `ProcessTimesheetDeadlinesCommand::promoteDraftWeeks()`
filters on `withTrackedHours()` (`Ist > 0` or `agreed > 0`), the identical scope
`EmployeeApprovableWeeksPayload` uses. A planned-only period therefore reaches the client neither
manually nor by deadline — it used to be promoted like any other, mailing "bitte freigeben" for a
period with nothing on it. The elapsed-Schicht condition is an *additional* gate on the automatic
route, not a looser hours rule.

### Fixed — 2026-08-05 Kundenportal-Stundenfreigabe wird nach Abrechnungszeitraum geschnitten, nicht nach KW (alluvo#3209)
`approve-stundenfreigabe` described the client's Dienstpläne/Stundenfreigabe hub as if its cards
were ISO calendar weeks. They are **approval periods**, cut by the assignment's resolved
Abrechnungszeitraum — under the default `month_segments` that is 1.–7., 8.–14., 15.–21. and
22.–Monatsende — and each card carries the same `01.08.–07.08.2026 (KW 31/32)` label as the
Tätigkeitsnachweis PDF and the twelve Stundenfreigabe notifications (the portal is now named in
that surface list). A materialised Wochennachweis keeps its stored bounds and the scheme only
fills what is left uncovered, so card and Nachweis always cover the identical days; a
planning-only period shows as "Geplant" with no Freigabe button, and an empty one is not rendered
at all. Two periods starting in the same ISO week are both shown now — they used to collapse onto
one (ISO-Jahr, ISO-Woche) key, so a clamped 10.–14. beside a full 15.–21. silently lost one card
and the client could never release it. That is no longer to be re-diagnosed as a role or
activation problem.

The KPI is "Aktueller Zeitraum", not "Diese Woche": it sums the period **containing today**
instead of the one *starting* in the current ISO week, which under a month-aligned scheme read 0h
on any day whose segment began in the previous week. And the deemed-approval footer is only
stated where it is true — company `deadlines_enabled` on, `deadline_behavior: auto_approve`, and a
stamped `deadline_at` on that period — naming the real Frist rather than the hardcoded "Montag,
19:00 Uhr" the old copy promised every client. The Fristen note in the activation section is
corrected accordingly: they resolve **per company** (company `timesheet.*` override → tenant
default), not tenant-wide.

### Fixed — 2026-08-05 §11-Einsatzmitteilung geht an den Mitarbeiter + Dienstplan-Digest für den Vertragsinhaber (alluvo#3206)
`build-dienstplan` stated the §11 Einsatzmitteilung was the **customer-facing** duty. It is not:
`SendAssignmentNotificationAction` addresses it **TO the deployed Mitarbeiter** under §11 Abs. 2
Satz 4 AÜG, with the contract owner and the sending operator locked in as CC; the customer's
Ansprechpartner vor Ort is CC'd only when ticked in the contract's recipient checklist. The
customer-facing disclosure duty is the *other* paragraph, §12 AÜG (the AÜV and the
Konkretisierung). The skill contradicted itself two blocks later ("a re-send re-opens **the
employee's** read receipt"), and the product's own notification copy carried the same error until
this change. Step 8's note is rewritten around the real §11-employee / §12-customer split — the
distinction from the step 6a digest is the *trigger* (operator decision vs. automatic), not the
audience. `manage-contract-lifecycle` gains an explicit recipient bullet in step 5, its
completeness gate no longer says the Einsatzmitteilung is what "the customer sees", and the §12
bullet now says the mail *restates* those facts to the employee.

Second, the owner-facing Dienstplan-change notification became a **digest**: post-publish shift
changes are recorded and collapsed into a single `DienstplanChangedAfterPublish` per Dienstplan
~15 minutes after the first change (`SendSchedulePeriodChangeDigestJob`, mirroring the employee
digest), summarising the shape of the change ("7 Schichten entfernt") plus the affected days —
not one mail per Schicht. It only *hints* that a corrected Einsatzmitteilung may be owed; it never
re-sends it. An operator changing the plan on a contract they own is not mailed about their own
edit. `build-dienstplan` step 6a says so where it tells operators what the owner hears, and notes
that the internal scope which silences both digests is data-repair/seeding only and reachable from
no operator path — so "let's do it silently" is still never on offer. No MCP tool, param, enum or
model type changed.

### Fixed — 2026-08-05 Kundenportal-Stundenfreigabe: Menüname + Tagesvergleich (alluvo#3199)
Two client-portal surfaces the operator skills describe to customers moved. The portal nav
entry is now **"Dienstpläne/Stundenfreigabe"** (EN "Shift Plans/Hours Approval") — the hub is
the single Stundenfreigabe surface, there is no second menu entry to look for, and the same
label names the shift-plan button on a won AÜV detail page. And the hub's "gemäß Zeiterfassung"
column now reads the shift date's **whole tracked day**, collapsed by
`App\Services\Timesheet\DayCollapse` — the same collapse the Wochennachweis is built from —
instead of matching the one time entry closest to the shift start within a ±1-day window. That
retires three symptoms operators used to explain away: a split day reporting only its first
block (3h41 of a 7h21 day, shown as a −3h40 deficit), a `break` row winning the match and being
displayed as worked time, and an untracked day borrowing its neighbour's entry. The hub also
refreshes **Draft** week rollups on load, so a "0h 0min" week header above rows that show times
is gone; **PendingClient** weeks are deliberately not refreshed — those numbers are what the
client was asked to approve, and the correction flow is how a submitted week changes.
`approve-stundenfreigabe` gains a "What the client's 'gemäß Zeiterfassung' column actually
shows" section (a minus is now a real shortfall; an empty Ist means nothing was tracked; a
geteilter Dienst shows one collapsed day on both rows and the week counts the date once) plus
the new nav label in the activation-gate and fingerprint notes; `using-alluvo-operator` routes
"Kunde sieht Minusstunden / gemäß Zeiterfassung stimmt nicht" and names the new menu entry;
`build-dienstplan` uses the new hub name in its `draft` visibility table. No MCP tool, param,
enum or model type changed.

### Fixed — 2026-08-05 Profilvollständigkeit verlangt eine lückenlose Berufserfahrung (alluvo#3165)
`get-profile-completeness` counted Berufserfahrung as satisfied as soon as **one**
ContactWorkExperience row existed, so a profile holding nine months of a decades-long career
reported `is_complete: true` (Ticket #1888). `ProfileCompletionService` now adds the required,
derived criterion `work_history_coverage`: the captured entries must cover the timeline from
the resolved start point (earliest education `earned_on` → license `issued_on`/`valid_from` →
earliest work-experience `start_date`) to today with no unexplained gap over 6 months. It
fails open when no start point resolves, and merges overlapping Zeitarbeit-Einsätze before
computing gaps. Profiles that read complete before this deploy can now read incomplete.
- **onboard-new-employee**: step 2's public-profile block gains the coverage criterion — the
  `public_profile.work_history_coverage` shape (`start_date`, `gaps[]`, `covered_ranges[]`,
  `start_point_known`), that `covered_ranges` is data-backed and **not** the complement of
  `gaps`, the fail-open case, and that the criterion is mirrored into `missing_required` with
  its `gaps` attached. States the fix as a **date range** — create/update the
  ContactWorkExperience (`0-184`) whose `start_date`/`end_date` closes the named span — never
  a placeholder station, and notes that a dateless entry can't close a gap. Adds
  `earliest_start_date` as a tracked Verfügbarkeit field written on **Candidate `0-81`**, and
  flags that the public bucket's fallback fix-hint points at a non-existent Contact `0-105`
  field (alluvo#2654).
- **profilvertrieb**: the Mode-B profile check now also covers work-history gaps — an
  unaccounted-for span makes the public profile report incomplete and weakens the Türöffner,
  so name the open range(s) and offer to complete the history instead of shipping it.
### Fixed — 2026-08-05 Ein Einsatz hat genau einen lebenden Dienstplan pro Zeitraum (alluvo#3186)
The "one live Dienstplan per Einsatz + overlapping date range" invariant is now enforced in code
rather than stated in a docblock, and three surfaces the skills describe moved with it.
- **build-dienstplan**: step 7 gains the **publish refusal** — `publish` asserts against the
  Einsatz's other *effective* (`draft`/`published`/`locked`) Perioden and throws when one overlaps,
  with the verbatim error, the fact that alluvo deliberately does **not** silently demote the other
  plan, and the two real ways out; that `approve` (`pending_approval → published`) carries the same
  check and is the path that actually hits it, since a pending plan may sit beside a live one until
  approval; and that inert Perioden never conflict. New box for **`superseded`** ("Ersetzt"): what
  it is, that it replaced the old silent demotion to `draft` (so "fällt zurück in Entwurf" is now
  wrong — `draft` is effective and kept booking availability and delivering Soll), that it is inert
  and terminal, the three replanning paths that write it (client-portal re-submission,
  `provisional` → WON publish, the batch builder behind both), that no operator action does, and
  that a replacement is refused outright when the retired plan has approved/invoiced Stundenzettel
  — leaving a wizard plan silently stuck in `provisional` after signing.
- **build-dienstplan**: step 3's period resolution corrected — `add-shift` resolves by
  **containment of the Schicht's date**, not by exact month boundaries, and a plan covering part of
  the month is **widened to the month** instead of a second Periode being created beside it. The
  statuses closed to a new Schicht go from three to four (`superseded` added), and the whole-month
  import's set from four to five; both list `superseded`'s misleading refusal text, which is still
  the `pending_approval` wording (alluvo#3196), so the skill tells the operator to read the real
  status rather than repeat "withdraw it from approval".
- **approve-stundenfreigabe**: new box on where Soll comes from — only `draft`, `published` and
  `locked` deliver it; `superseded`, `cancelled`, `provisional`, `pending_approval` and `rejected`
  contribute zero. A Soll that dropped after a Umplanung is the correction landing, not missing
  hours (the replaced plan used to be demoted to `draft` and kept counting alongside its
  replacement), and an approved or invoiced period can never lose its Soll this way.
- **head-of-disposition**: the Dienstplan-gap KPI notes that a delegated release can come back
  refused on an overlap — a data question, not a retryable task — and that `status: superseded`
  rows are legitimately replaced plans, not backlog.

### Fixed — 2026-08-04 Der Monatsimport verweigert einen veröffentlichten Dienstplan (alluvo#3159)
Both bulk writers in `ShiftPlanProcessingService` used to look the month's Periode up filtered by
status, so a re-import of a published month fell through to the create-branch and started a
silent second Periode. They now **refuse** instead, via `SchedulePeriodStatus::closedToBulkImport()`
= `closedToNewShifts()` + `Published` — reuse was rejected deliberately, because the bulk path
deletes and rebuilds the month and would drop shifts the employee app, Stundenfreigabe and the
client portal already point at.
- **build-dienstplan**: the shadow-period warning in step 7 is replaced by the refusal it became —
  the four statuses closed to a whole-month import (`published`, `locked`, `cancelled`,
  `pending_approval`), each with its verbatim message and named way out, that nothing is written
  when it refuses and no acknowledgement flag pushes it through, and that `draft`/`needs_revision`
  are still reused in place. Records that `provisional` is in neither set, so a bulk import over a
  pre-signature wizard plan still creates a second Periode. Adds the silent-failure case: the
  inbound ticket/email extraction path declines the same four statuses but only logs, so a
  forwarded Dienstplan for a closed month produces **no error anywhere in the UI** — check the
  Periode status before suspecting the extraction. Step 3 now notes that the bulk `create` is
  stricter than `add-shift` by exactly `published`.
- **build-dienstplan**: the note that the `publish` action's own description was stale is dropped —
  the description no longer claims draft hides the plan from the employee app or Stundenfreigabe,
  nor that a later backfill lands in a second period (alluvo#3113).

### Fixed — 2026-08-04 Stundenfreigabe im Kundenportal wird pro Kunde freigeschaltet (alluvo#3151)
`ClientPortalTimeApprovals` moved from a tenant scope to a **Company** scope: the Dienstpläne
hub, its nav entry, the dashboard approvals card and the `create-plan` / `shift-plan` portal
actions are now gated per Einsatzbetrieb, default off, with no tenant-level inheritance. The new
`client.feature` middleware aborts **404** (not 403) so a gated-off surface is indistinguishable
from one that does not exist.
- **approve-stundenfreigabe**: new section next to the portal-access rules describing this as a
  *second, independent* gate on top of the portal role — what disappears while a company is not
  activated, that the 404 must not be read as a permission or role problem, and that the legacy
  `/time-entries/approval` link falls back to the dashboard. Names the diagnostic fingerprint
  (the reminder mail's deep-link into the weekly Freigabe-Kalender is **not** gated, so "Link aus
  der Mail geht, Menüeintrag fehlt" = company never activated). States that no MCP tool and no
  Einstellungen screen activates it — hand it to alluvo, don't promise it in-session — that the
  rollout covered companies with a Rahmenvertrag in a Rahmenvertragsgruppe and every other one is
  off by design, and that (de)activating sends no mail and moves no Frist (the reminder /
  escalation / Auto-Freigabe pipeline runs off the tenant-wide Fristen setting and ignores this
  gate). Client-side triggers added to the description.
- **using-alluvo-operator**: routes "Kunde sieht keine Dienstpläne / 404 im Kundenportal" to
  `approve-stundenfreigabe`, flagging the company activation as the thing to check *before*
  anyone's portal roles.

### Fixed — 2026-08-04 Es gibt keinen primären Einsatzbetrieb mehr (alluvo#3130)
`client_sites.is_primary` was removed end-to-end (column, unique index,
`Company::primaryClientSite()`, the client-portal `setPrimary()` endpoint). Its replacement is
`ClientSite::resolveObviousSiteId()` — the company's *only active* site, or nothing at all when
the company genuinely has several. So no code picks an Einsatzbetrieb for a multi-site client.
- **manage-contract-lifecycle** (`StaffingDemandMatch` drafts): the resolution chain's last step
  is now "the company's only active Einsatzbetrieb", and it is stated that this resolves to
  nothing for a multi-site company. The `manage-model` create hint for a missing Einsatzbetrieb
  no longer passes `is_primary: true` (`0-341` + `industry_classification` only).
- **manage-contract-lifecycle** (creating an Einsatzbetrieb): new note that `is_primary` no
  longer exists on ClientSite — never pass it on create/update, never filter on it (`search-model`
  on `0-341` rejects it as unknown), and pass `client_site_id` explicitly whenever a company has
  more than one active site. Flags that some tool descriptions still say "the company's primary
  ClientSite", which now means "its only active one".
### Added — 2026-08-04 Schwerpunkte (`FocusArea` `0-369`) und personenbezogene No-Gos (alluvo#3131)
A tenant-wide catalogue of professional focus areas ("Schwerpunkte": Intensivpflege, Palliativ,
Beatmung, …), sector-neutral by design. `FocusArea` (`0-369`, slug `focus-areas`) is fully
MCP-manageable via `manage-model` (`name` required and unique tenant-wide, plus `code` unique,
`description`, `is_active`, `sort_order`); reading it needs `focus-areas.view`. Two new pairs in
`manage-association`: `0-107` CompanyDepartment → `0-369` (a department's Schwerpunkte) and
`0-105` Contact → `0-369` (a person's **No-Go**). No new tool — the MCP prompt
`manage-focus-areas-prompt` carries the rules. A No-Go acts in the **client portal only**: the
customer neither sees nor can book the person for an Abteilung carrying that active Schwerpunkt
(display filter plus a server-side gate on add, change and finalisation). Operator matching,
Dienstplan and AÜV are untouched **by design**.
- **onboard-new-employee** (new step 2c): recording a No-Go — resolve the Employee's
  `contact_id` and use `0-105` as the source (identity root, so one entry covers Employee *and*
  Candidate), `attach`/`bulk-attach` (max 50) two-stage, an Employee-sourced call is refused with
  a message naming the Contact. Plus what a No-Go does and deliberately does not do, that it is
  no substitute for a Blacklist entry, and that it is never inferred.
- **intake-personalbedarf** (Abteilung block): the catalogue and the `0-107` → `0-369`
  association, `is_active: false` as the way to retire a Schwerpunkt, and the explicit note that
  Schwerpunkte do not filter a `0-415` Bedarf.
- **match-bench-to-clients** (step 3): a No-Go does not filter the match list and does not lower
  a score — presence in a shortlist proves nothing about no-gos — but the customer will not find
  the person in the portal for that Abteilung.
- **build-dienstplan** (Umbesetzung blockers): a No-Go is not a blocker and produces no warning
  on this path; check the Abteilung's Fachlichkeit yourself rather than waiting for one.
- **using-alluvo-operator**: routing line splitting the person's No-Go from the Abteilung's
  Schwerpunkte.

### Fixed — 2026-08-04 Ein nachgetragener Tag landet im bestehenden Dienstplan des Monats (alluvo#3138)
`ShiftMutationService::resolveOrCreatePeriod()` no longer filters the month's SchedulePeriod
lookup by status: `add-shift` now joins whichever Periode already covers that month — a
`published` one included — instead of silently starting a second one. Three statuses refuse a
new Schicht outright (`SchedulePeriodStatus::closedToNewShifts()`: `locked`, `cancelled`,
`pending_approval`), as a `date` validation error prefixed `No shift can be added to Dienstplan
#<id> (<name>): …`, with no acknowledgement flag and no override reason.
- **build-dienstplan** (step 3): new blocker bullet for the three closed statuses with their
  verbatim messages and the route out of each, explicitly *not* an ArbZG block.
- **build-dienstplan** (step 7): the "finish the month, then publish" order rule is gone — a
  post-publication backfill joins the published Periode and is effective at once. The
  second-Periode hazard is now scoped to what still has it: the monthly bulk `action: "create"`,
  which continues to reuse only a `draft`/`needs_revision` Periode, so a published month is
  corrected shift by shift and never by re-importing. Notes that the `publish` action's own
  description still carries the stale sentence.
- **build-dienstplan** (step 6b): employee-side writes generalised from "refused on a Locked
  Periode" to the same three statuses.
- **approve-stundenfreigabe** (past-day box): a `locked` month refuses even the nachtragen and
  points at the Stundenklärung — i.e. at this skill; `pending_approval` must be withdrawn first.
### Fixed — 2026-08-04 Eine Rolle im Portal-Formular zu setzen lädt niemanden mehr zuverlässig ein (alluvo#3148)
`ClientPortalSchemaPageController::update()` now gates the invitation on `$hadRolesBefore`: the
mail fires only when *that* request grants the contact's first role at the company, on top of the
existing `portal_invited_at` guard. The create path is unchanged. Independently, the edit path
currently sends no invitation at all — `SendPortalInvitationAction::execute()` returns `false` in
a portal session and the controller does not read the return value, so it fails silently (open
alluvo-side defect).
- **approve-stundenfreigabe** ("Portal access is opt-in"): new callout that the portal's own
  Ansprechpartner form is not a reliable invitation path — it works on create, is deliberately
  skipped on edit for a contact who already held a role or was invited, and currently sends
  nothing on edit at all. Steers every existing-contact case to the `send-portal-invitation`
  record action, which grants the role and sends the mail in one call regardless of prior state.

### Added — 2026-08-04 Rahmenvereinbarung (`0-423`) und Arbeitsschutz-Herkunft sind über MCP lesbar (alluvo#3126)
Three read surfaces the skills previously had no way to reach: **FrameworkAgreementGroup
(`0-423`)** — the master *Rahmenvereinbarung* signed once with several houses, spawning one
Rahmenvertrag per house — is now in `availableForMcp()`; **FrameworkContractStaffingRole
(`0-344`)** was registered but returned an empty table and now exposes its fields; and
`FrameworkContract` (`0-30`) / `ClientSiteSafetyAgreement` (`0-342`) gained filterable
`framework_agreement_group_id`, `client_site_id`, `client_site_safety_agreement_id` resp.
`cloned_from_safety_agreement_id`, `accepted_at`, `accepted_by_name`. Nothing became writable —
all three types stay read-only, authored by the framework-contract wizard.
- **manage-contract-lifecycle** (three new blocks in step 1): the Rahmenvereinbarung above the
  Rahmenvertrag with its fields and the explicit "no write path, hand over the wizard" rule;
  `0-344` for role-row sweeps across contracts, with `list_roles` kept as the richer
  single-contract path; and safety-agreement provenance via `cloned_from_safety_agreement_id` /
  `accepted_at`. Notes that the three new `0-30` FKs are `hiddenByDefault` and filter as
  relationships (`in` / `not_in` / `is_null` / `is_not_null`).
- **manage-contract-lifecycle** (Arbeitsschutzvereinbarung on an FC-covered AC): reading the
  role row on `0-344` added as an alternative to the wizard's computed
  `framework_role_safety_agreement_id`.
- **triage-data-quality** (new step 3d + Related skills): four detector-less contract checks —
  role rows without a safety agreement (the gap that blocks `send_for_signoff`), Rahmenverträge
  without Einsatzbetrieb/agreement, agreements never accepted by the client, and agreements not
  cloned from a template — with the explicit note that none of it is fixable from this skill.
- **account-research** (step 5) and **call-prep** (step 4): trace a Rahmenvertrag up to its
  group-level Rahmenvereinbarung, and list the sibling houses on the same document.
- **Correction across all four:** whether two houses share an Arbeitsschutzvereinbarung must be
  read from `cloned_from_safety_agreement_id`, never inferred from the `label` — labels are
  routinely identical across unrelated agreements, so a label comparison answers it wrong.

### Changed — 2026-08-04 Kundenportal-Zugang ist Opt-in, Einladung ist eine eigene Handlung (alluvo#3011)
Portal access is no longer implied by being linked to a company: signing in now requires a
deliberate `client_portal_role_contact` role. A new Contact action `send-portal-invitation`
grants the first role *and* sends the invitation in one call, and is the only route for someone
who has never signed in — `assign-portal-roles` only appears once a contact has logged in at
least once, and an empty `roles` list there **revokes** access rather than falling back to
`viewer`. Existing portal users were backfilled to `viewer`, so this only affects new or newly
linked Ansprechpartner.
- **approve-stundenfreigabe** (new subsection under "How the client is notified"): the opt-in
  access model, both actions with their exact params and availability rule, the role list with
  `approver` called out for Stundenfreigabe, an explicit warning that clearing `roles` revokes
  access, and the note that internal operators are exempt from the last-administrator guard.
- **manage-contract-lifecycle** (recipient gate on `send_for_signoff`): a reachable recipient is
  not necessarily one who can sign — the commission wizard sits behind an authenticated portal
  session and the send gate does not check portal access, so grant it first or use the paper
  signature path.

### Added — 2026-08-04 Dienstplan veröffentlichen ist MCP-fähig (SchedulePeriod `0-110`) (alluvo#3112)
`PublishSchedulePeriodAction` is now `#[McpExposed]`, so a Dienstplan can be published through
`manage-record-action` (`operation: "execute"`, `model_type: "0-110"`, `action: "publish"`).
Before this there was no MCP publish route at all — `0-110` is read-only for `manage-model`, so
a draft Dienstplan was a dead end for the skill.
- **build-dienstplan** (new step 7, §11 AÜG notification renumbered 7 → 8): documents the
  two-stage `publish` call, that `0-110` is read-only for `manage-model` so the action is the
  only route, and that it runs **only** while the Periode is `draft`.
- **build-dienstplan** (step 7): publishing sends **no** notification — `publish()` stamps only
  `status` + `published_at`; the employee mail comes from the client-portal publish path and
  `DienstplanApproved` from the `approve` action. So it is safe on a month already worked, and
  `approve` (`pending_approval → published`, notifies) is explicitly not a substitute.
- **build-dienstplan** (step 7): publishing is per Periode, all-or-nothing — a Schicht carries
  only `cancelled_at`, so a single day cannot be published.
- **build-dienstplan** (step 7): **corrects the action's own description**, which claims a draft
  plan is hidden from the employee app and from Stundenfreigabe. Verified against `origin/main`:
  `SchedulePeriodStatus::notEffective()` does not contain `Draft`, the employee-app controllers
  and the availability sync all use `Shift::effective()`, and `TimesheetWeekBuilder` does not
  filter on period status at all — so a draft plan **is** visible to the employee, **does** book
  availability and **does** produce the Soll. A table states what `draft` actually withholds
  (client portal) versus what it does not, and names the operational risk: draft Schichten are
  not in `SchedulePeriodStatus::committed()`, so they raise no double-booking or §5-rest warning
  against a newly planned Schicht.
- **build-dienstplan** (step 7): order rule — a shift write resolves its Periode by
  (Einsatz, month, status `draft`), so a backfill after publishing creates a **second** Periode
  for the month. Finish the month's corrections first, publish last.
- **build-dienstplan** (step 5 + Output): a confirmed write leaves the Periode in `draft`; report
  the status and offer the release instead of stopping at "Dienstplan erstellt".
- **approve-stundenfreigabe** (*Which periods the employee actually sees*): new blockquote ruling
  the draft Dienstplan **out** as the cause of a missing approval period — the gate is tracked
  hours, not plan status, so publishing will not make a period appear. Points the real symptom
  (the customer cannot see the Dienstplan) at the unpublished month instead.
- **head-of-disposition** (§1d Dienstplan gaps): unpublished months as a second, quieter gap —
  `query-model` on `0-110` for `status: draft`, why it matters at manager level (the guards stay
  silent, the customer sees nothing), delegate the release to `build-dienstplan` step 7.

### Changed — 2026-08-04 Dienstplan: `ignore_warnings`-Caveat entfällt, der Prompt ist wieder eindeutig (alluvo#3105)
Follow-up to alluvo#3101, where the skill documented the shifts prompt's self-contradiction as a
caveat because the api-side fix was incomplete. `00111c9109` removed the remaining seven
`ignore_warnings` references (the declared `Argument`, the run-parameter table row, the
`$warnHint` pair, the ArbZG-Hinweis blockquote and the "Wichtige Hinweise" bullet), so there is
nothing left for the operator to ignore.
- **build-dienstplan** (step 2): drops the "the prompt still mentions `ignore_warnings` in
  places — ignore those lines" caveat and the claim that the prompt carries an `ignore_warnings`
  argument. The prompt now takes six arguments (`assignment_id`, `assignment_contract_id`,
  `employee_id`, `month`, `send_notification`, `dry_run`) and names `ignore_warnings` only to
  state that it does not exist.
- **build-dienstplan** (step 2): keeps the operative rule unchanged, since the tool surface did
  not move — there is no `ignore_warnings` parameter on `manage-shift-plan`, passing it is
  silently dropped, the full flag set is `confirmed`, `past_date_acknowledged` (+ optional
  `past_date_acknowledgement_reason`) and `availability_override_reason`, and the §3 hard limit
  is releasable by nothing at all.

### Changed — 2026-08-04 Stundenfreigabe-Backlog zählt Abrechnungszeiträume statt Kalenderwochen (alluvo#3014)
Follow-up to alluvo#3027, which brought `approve-stundenfreigabe` and
`manage-contract-lifecycle` onto the period schemes but left the manager layer and the
label's outward reach untouched.
- **head-of-disposition** (§1e Stundenfreigabe backlog): new lead paragraph — the backlog is
  counted in **Abrechnungszeiträumen, not Kalenderwochen**. The default `month_segments`
  (1–7, 8–14, 15–21, 22–end of month) means a period regularly spans parts of two ISO weeks,
  so "KW 32" is not a unit of this backlog and may mean two periods or part of one.
- **head-of-disposition** (§1e): states why the backlog is a leadership number — because no
  period crosses a month boundary, **invoicing and payroll for a month can run as soon as that
  month's last segment is approved**. An outstanding 22nd–end segment blocks the month's
  billing; an outstanding 8th–14th one does not. Rank by which month is held up, not by age.
- **head-of-disposition** (§1e): reframes the Draft/Tagesabschluss, empty-period and go-live
  bullets from "week" to "period" — the unit they describe has not been an ISO week since the
  scheme change.
- **approve-stundenfreigabe** (Abrechnungszeitraum → Labels): documents that the
  `01.08.–07.08.2026 (KW 31/32)` label is what the counterparty actually sees — the
  Tätigkeitsnachweis PDF and all **twelve** Stundenfreigabe notifications render it. Quoting a
  KW on the phone will not match the client's mail or PDF; an employee reporting "I can't find
  KW 32" is looking at a segment label, so ask for the dates on their mail.
- **onboard-new-employee**: go-live cutoff note and the `approve-stundenfreigabe` cross-link
  now say Abrechnungszeitraum/Abrechnungszeiträume instead of "week"/"approvable weeks".

### Changed — 2026-08-04 `send_for_signoff` verlangt einen erreichbaren Empfänger, nicht `signer_email` (alluvo#3102)
- **manage-contract-lifecycle**: corrects the claim added in alluvo#3084 that `signer_email`
  is "still a hard gate on `send_for_signoff`". It is **not** a send gate on either contract
  type — the Einsatzvertrag needs the stage plus **at least one recipient with an email
  address**, and the send service never reads `signer_email`. A contract with no reachable
  recipient is refused with "this assignment contract has no recipient with an email address";
  the fix is `action: "update"` with `recipient_contact_ids` / `primary_recipient_contact_id`,
  or the `add_contract_recipient` record action — never filling `signer_email`.
- **manage-contract-lifecycle** (step 4): new *Recipient gate on `send_for_signoff`* paragraph —
  states the full precondition and that both the `confirmed: false` preview and the success
  response now print the **recipient list** (`Name <mail> (primary), …`, recipients without an
  address marked "no email — will not receive the mail") instead of a single signer line.
- **manage-contract-lifecycle**: notes that `completeness` still lists "Signer contact set" as a
  gap on an unsigned Einsatzvertrag — that check belongs to the signature-readiness gate, not the
  send gate, so it never blocks sending. The Rahmenvertrag's stricter send gate (primary
  recipient needs first name, last name **and** email) is called out as the contrast.
- **manage-contract-lifecycle** (`manage-record-action` section): the recipient pre-check now
  exists on the record action too, so `send_for_signoff` via `manage-record-action` can no
  longer report success while mailing nobody. `reserve_until` validation and the Rahmenvertrag's
  ready-to-send report remain contract-tool-only.
### Changed — 2026-08-04 Nachtrag in der Vergangenheit ist eine Bestätigung, keine ArbZG-Sperre (alluvo#3101)
- **build-dienstplan** (step 3): an un-acknowledged past date is no longer described as coming
  back as a "hard warning". It has its own response, **`## Backfill confirmation required
  (<action>)`** — explicitly *not* `## Action blocked — hard limit` — which names
  `past_date_acknowledged: true` and states that `confirmed: true` alone is not enough
  (`confirmed` confirms the write, `past_date_acknowledged` the backfill). Re-sending the
  identical payload with only `confirmed: true` is refused again, every time; the skill now says
  never to answer it by moving the Schicht to another date or by reporting the day as impossible.
- **build-dienstplan** (step 3): documents the preview's own section `### Backfill — past date(s)
  (soft — confirmable, NOT an ArbZG block)`, and that the preview's closing line names **every**
  flag the confirming call needs — so a write needing both a backfill confirmation and an
  availability release names both instead of sending the caller round a second futile retry.
- **build-dienstplan** (bulk `create` box): corrects "the blocker replaces the preview" for the
  backfill case — it does not. The `confirmed: false` call returns the normal preview with the
  backfill section; the confirmation response only appears on a `confirmed: true` call that
  omitted the flag. The §3 hard block *does* still replace the preview.
- **build-dienstplan** (step 1): new *never picks the Einsatz for you* paragraph — `add-shift`/
  `create` require an `assignment_id` and have no tie-break, so write to the **existing** Einsatz
  whose Einsatzzeitraum covers the date, **ask** the operator when several qualify (naming
  Company/Abteilung + Zeitraum), and never create a new Einsatz just to park a Schicht.
- **build-dienstplan** (step 2): warns that `manage-assignment-shifts-prompt` still contains
  leftover `ignore_warnings` instructions (and the argument) while also stating the parameter does
  not exist — the tool has no such parameter, so those lines are to be ignored and step 3 is
  authoritative for the flag set.
- **build-dienstplan** (steps 4/5): a backfill is called out as a third warning category, distinct
  from ArbZG and from availability — flag, no reason needed; and the confirm step now says to send
  every flag the preview named in one call. `update-shift` accepts `past_date_acknowledged` but
  releases nothing there — a past date on that path still returns the hard-limit block.

### Changed — 2026-08-04 Unterzeichner auf dem Vertrag folgt dem Empfänger (alluvo#3084)
- **manage-contract-lifecycle**: new section *Whose name the contract prints as customer
  signer* — the full resolution order every signable document (AÜV, Einzel-AÜV, §12
  Konkretisierung, Rahmenvereinbarung, Anlage 2) now uses: frozen recorded signer once signed
  (`signed_at`, or stage `won` for imports; a Rahmenvertrag prefers `signed_by_contact_id`) →
  the portal contact viewing it **only if attached to this contract** → **the contract's own
  primary recipient** → the Rahmenvertrag's recipient/signer → a pre-filled `signer_full_name`
  on an unsigned contract, **last**.
- **manage-contract-lifecycle**: the remedy for "the contract shows the wrong name" is now to
  change the primary recipient (`action: "update"`, `recipient_contact_ids` +
  `primary_recipient_contact_id`) — overwriting `signer_full_name` on an unsigned contract has
  no visible effect while a named recipient is attached. Also records that a nameless recipient
  (or a list with no primary flag) is skipped, that `signer_email` remains a
  hard `send_for_signoff` gate without deciding the printed name, that a signed document never
  re-resolves, that the client-portal commission preview follows the same precedence, and that
  a re-rendered Anlage 2 carries `signed_at` rather than the regeneration date.
- **manage-contract-lifecycle** (step 1 send gate, step 2 unresolved-fields table, imported
  contracts): cross-links to that section — and notes that
  `complete-imported-assignment-contract-prompt` filling `signer_full_name` / `signer_email`
  stays correct for imports (stage `won` = already signed), but is not the lever on a draft.

### Changed — 2026-08-04 §5 ArbZG Ruhezeit ist eine Warnung, kein harter Block (alluvo#3010)
- **build-dienstplan** (step 3): the ArbZG hard-limit list is now **exactly one** ceiling —
  more than 10h worked on a single day (§3). A rest gap under 11h in **either** band (§5 /
  §5 Abs. 2), including below the absolute floor, is a non-blocking warning; it keeps
  `critical` severity so its seriousness stays visible, but severity is not blocking. Notes
  why: §5 is the paragraph ArbZG itself makes deviable for care (§5 Abs. 2, with compensating
  rest alluvo cannot verify), §3 has no carve-out.
- **build-dienstplan** (step 3): new box on the **plan-wide** shape of rest warnings — they are
  computed over the Einsatz's whole plan, so a single `add-shift` can name dates weeks from the
  day being written. That is pre-existing roster context, not a rejection of the write. Spells
  out the failure it prevents: the monthly bulk `create` accepts a plan whose rest gaps warn, so
  blocking later edits on those same gaps would make the roster the tool let in impossible to
  finish or correct.
- **build-dienstplan** (step 3): the past-date demotion now reads as §3-only — §5 needs no
  demotion because it never blocks, past or future.
- **build-dienstplan** (step 4): says explicitly never to state "ArbZG can never be overridden"
  without naming §3; unqualified, that reads as "this task is impossible" the moment any ArbZG
  line appears — and rest warnings are the ones that appear most often, on writes they have
  nothing to do with. Lists what actually blocks: §3, contract window, double-booking, the
  started/past-Schicht lock, an unacknowledged past date.
- **build-dienstplan** (step 6, client-portal box): records the **asymmetry** — the checkout
  guard (`ShiftGuardRailService`) still aborts a booking on a sub-floor §5 gap, while operator
  writes only warn. So a booking rejected for rest *can* be entered operator-side; the skill
  says not to offer that as a workaround for a rejected booking.
- **build-dienstplan** (steps 6b, 6c): employee-app writes hit the §3 hard limit and the same
  non-blocking §5 warnings; `reassign-shifts` (Umbesetzung) `blockers` drop the §5 floor —
  `arbzg_*` is >10h/day §3 only.
- **head-of-disposition** (AÜG/ArbZG): same split. Adds that a §5 finding is roster quality to
  review, never "planning is blocked at client X", and that eligibility checks return it as a
  **hint** — a candidate carrying one stays placeable and must not be filtered out of a
  shortlist.
- **manage-contract-lifecycle** (Krankheitsvertretung) and **record-absence**: the
  `add_replacement` Eignungsprüfung blocks on a hard ArbZG limit (>10h/day §3 only); a §5 rest
  gap is a hint, so a cover carrying one is still eligible.
### Changed — 2026-08-04 §11 Einsatzmitteilung nur noch bei unterschriebenem, laufendem Einsatz (alluvo#3093)
- **manage-contract-lifecycle** (step 5): documents the tightened gate on
  `send_assignment_notification` — it now requires **both** `stage: won` **and** `status`
  `commissioned`/`performing`. A `performed` Einsatz is refused ("the Einsatz is no longer in
  force"), an unsigned one is refused on the stage. Same gate on the web button, the contract
  tool, and the generic `manage-record-action` path; the auto-send on the `won` transition is
  unaffected. Notes that legacy imports can carry `stage: draft` with `status: performed`, so
  both fields have to be read.
- **manage-contract-lifecycle** (step 5b): flags that `add_replacement` still accepts a
  `performed` contract while the cover's §11 follow-up does not — surface that before adding
  the Vertretung, not on the third step.
- **manage-contract-lifecycle** (step 6): `mark_performed` closes the §11 window for good, so a
  still-owed corrected Einsatzmitteilung must go out first. `resend_order_confirmation`
  deliberately stays available on a `performed` contract.
- **build-dienstplan** (step 7): the "Vertrag gewonnen → Schichten bauen → Einsatzmitteilung
  senden" order still holds, but the re-send window closes once the Einsatz has ended — check
  the status before offering the send on an older roster.
- **record-absence** (Krankheitsvertretung follow-ups): same narrower gate on the cover's
  Einsatzmitteilung relative to `add_replacement`.

### Changed — 2026-08-04 transition/send_for_signoff auch über manage-record-action erreichbar (alluvo#3064)
- **manage-contract-lifecycle**: new cross-cutting section documenting that `transition` and
  `send_for_signoff` are now `#[McpExposed]` record actions on `FrameworkContract` (`0-30`) and
  `AssignmentContract` (`0-31`), so `manage-record-action` can list and execute them — and that
  both operations must still be driven from `manage-framework-contract` /
  `manage-assignment-contract`.
- **manage-contract-lifecycle**: names the concrete hazard on the generic path — the send
  service returns silently when no recipient has a usable email address, yet the action still
  transitions `approved → sent`, so `manage-record-action` reports a sent contract that no
  customer received. The contract tool refuses that call instead.
- **manage-contract-lifecycle**: records which gates live in the contract tool rather than in
  the action (Rahmenvertrag ready-to-send report, Einsatzvertrag `signer_email`,
  `reserve_until` validation and its signing-deadline clamp), that `transition` behaves
  identically on both paths (same allowed-transition graph, same `pending_review`
  re-validation), and that neither action carries a permission an operator could hold without
  already being able to use the contract tool.
- **manage-contract-lifecycle** (step 4): cross-reference to the new section, plus the note
  that `manage-record-action` `operation: "list"` on `0-30`/`0-31` stays a valid read-only way
  to see whether the two actions are currently available and why not.

### Changed — 2026-08-04 max_hours-Vorschlag rechnet Soll am Beschäftigungsrand anteilig (alluvo#3078)
- **manage-contract-lifecycle** (Einsatz section): documents that `max_hours` is **computed and
  stored** whenever `manage_einsatz` `add`/`update`/`extend` omits it, and that the result line
  reports it as `Max hours/month: X (suggested: Y)`. States the formula operators see — the
  smallest month across the Einsatz window of *(monthly Soll − hours already committed in the
  employee's other Einsätze)*.
- **manage-contract-lifecycle**: spells out the two asymmetric proration rules that make a
  suggestion look wrong. The Soll **is** prorated in the Beschäftigungszeitraum's start/end
  month, so an Einsatz spanning the Eintritts-/Austrittsmonat takes that reduced month as its
  minimum and the ceiling drops for the whole Einsatz (Austritt 14.08., 160 h Soll → 76,19 h).
  A mid-month **Einsatz** start is deliberately *not* prorated and still measures against the
  full monthly Soll — skills must stop explaining a ceiling as "half a month".
- **manage-contract-lifecycle**: an employee with no Employment Period keeps the flat Soll; an
  explicit `max_hours` overrides the suggestion and is preserved across later re-derivations.
- **manage-contract-lifecycle**: `max_hours: 0` now means **"no free capacity left"** (whole Soll
  committed elsewhere), not "nothing configured" — only `null` means no ceiling. Never report a
  0 as "no limit".
- **manage-contract-lifecycle** / **build-dienstplan**: clarifies that the ceiling guards
  *customer* bookings in the client portal and is **not** enforced on the operator planner —
  `manage-shift-plan` never refuses a Schicht for exceeding it, so no warning is to be
  announced. For a plan-only Einsatz (`with_plan`, no `hours_arrangement`) the ceiling instead
  *is* the planned total and is re-derived on every shift write.

### Changed — 2026-08-04 Abrechnungszeitraum ersetzt Rechnungsstellung auf den Vertrags-MCP-Tools (alluvo#3027)
- **manage-contract-lifecycle** (new section "Abrechnungszeitraum"): documents
  `timesheet_period_scheme` on both `manage-framework-contract` and
  `manage-assignment-contract` — the enum (`month_segments`, `half_month`, `monthly`,
  `calendar_week`), the period bounds each one cuts, and the `billing_frequency` it derives
  (`month_segments`→`weekly`, `half_month`→`biweekly`, `monthly`→`monthly`).
- **manage-contract-lifecycle**: marks `billing_frequency` **deprecated** — sending both is not
  an error, the scheme silently wins, and the frequency is what gets rendered verbatim into the
  signed AÜV §X.2 / Rahmenvereinbarung §9.2. Also states that `calendar_week` is legacy and must
  never be set on a new contract.
- **manage-contract-lifecycle**: records the inheritance chain (assignment contract → framework
  contract → company override → tenant setting `timesheet.period_scheme`, default
  `month_segments`), so an omitted field reads as "inherits", not "forgotten", and setting it on
  the Rahmenvertrag is the way to give one client a single rhythm.
- **approve-stundenfreigabe** (new section "Abrechnungszeitraum"): an approval period is no
  longer an ISO week. Documents the four schemes, the resolution order, the
  `01.08.–07.08.2026 (KW 31/32)` label (date range + spanned ISO weeks — never rebuild "KW x"
  from a week number), and that a scheme change never re-cuts existing periods: stored bounds
  are immutable, new periods clamp past them, so one short transitional period is expected.
- **approve-stundenfreigabe**: rewrites the "Which weeks the employee actually sees" section to
  periods throughout — the clamping, tracked-hours and go-live rules are unchanged, but they no
  longer imply Mon–Sun. Adds the reminder that under `month_segments` an operator asking for
  "KW 32" may mean two periods.
- **using-alluvo-operator**: routes "Abrechnungszeitraum" by intent — setting it →
  `manage-contract-lifecycle`, reading/explaining a period label →
  `approve-stundenfreigabe`.

### Changed — 2026-08-04 Umbesetzung und Krankheitsvertretung auf eigenständigen AÜVs (alluvo#3035)
- **build-dienstplan** (step 6c, Umbesetzung): removes the stale hard blocker "a signed AÜV
  **without** a Rahmenvertrag — it has to be cancelled and re-created". That blocker
  (`standalone_contract_won`) no longer exists: a signed standalone AÜV now takes the ordinary
  `konkretisierung` path and stays in force. Advising a Storno-and-recreate would void the
  client's signature for nothing.
- **build-dienstplan** (step 6c): documents the new hard blocker
  `role_requirement_unresolvable` — neither the Einsatz, nor the AÜV, nor the outgoing employee
  yields an Einsatzrolle, so fachliche Gleichwertigkeit (§ 11.3) cannot be established. Not
  acknowledgeable; the fix is to maintain the Rolle. Blocker list now names the actual codes
  (`role_mismatch`, `arbzg_*`, `blacklisted`, `outside_employment_period`,
  `shift_already_started`, `contract_terminal_stage`).
- **record-absence** (step 9, Vertretung vs. Umbesetzung): `add_replacement` now runs the **same**
  Eignungsprüfung as the Umbesetzung — role fit, Blacklist, active employment and hard ArbZG
  limits are blockers, Höchstdauer and reported absence are warnings naming
  `acknowledge_duration_override` / `acknowledge_absence_conflict`. Adds the call shape, the
  plan-form preview (`blockers` / `warnings` / `effects` / `shift_ids`), the active-contract +
  `sick_replacement` prerequisites, and the open-ended-window rule.
- **record-absence** (step 9): states that **no `shifts` parameter exists** on `add_replacement` —
  the cover inherits the replaced employee's Schichten verbatim; different times are an
  afterwards edit via `build-dienstplan`, not a parameter.
- **manage-contract-lifecycle** (new step 5b): Krankheitsvertretung on a running contract —
  `add_replacement` → `send_konkretisierung` (client, § 12 AÜG) → `send_assignment_notification`
  (cover, § 11), no Rahmenvereinbarung required, and the still-standing limit that a second
  **concurrent** person on a standalone AÜV needs a Nachtrag. Resolves the dangling
  `send_konkretisierung` cross-reference from `record-absence`.
- **manage-contract-lifecycle** (step 6, Ending a contract): swapping the deployed person is never
  a reason to Storno — including on a standalone AÜV.

### Changed — 2026-08-04 Tagesabschluss als Automatisierungs-Trigger + Tageszusammenfassung (alluvo#3037)
- **approve-stundenfreigabe** (Tagesabschluss): documents the **second** release-blocking 422 —
  a day that IS closed but whose breaks were edited below the § 4 ArbZG minimum *after* closing
  ("Pausenzeit nachträglich geändert"). Only reachable via an operator edit; remediated by
  **withdraw and re-close with a reason**, never by closing again. A closure that already carries
  a reason stays settled regardless of later edits.
- **approve-stundenfreigabe** (Changing a closed day): corrects the claim that an operator write
  leaves the release gate passing. The gate re-runs the break check **live** at release time, so
  an operator correction to a reason-less closed day can bounce the employee's next release.
- **approve-stundenfreigabe** (Tagesabschluss): the closure row now records the whole day —
  `worked_minutes`, `first_start_at`, `last_end_at`, the § 4 follow-up answers and the derived
  `break_violated` boolean — and the Einsatz owner's no-break notification carries that summary.
- **approve-stundenfreigabe** (Tagesabschluss): "no model type" corrected — the closure is
  `TimeTrackingDayClosure` (`0-422`), still off the MCP allowlist (absent from `list-model-types`;
  `query-model` / `get-model` / `manage-model` refuse it), but usable as a workflow trigger.
- **build-automation-agent** (new subsection under step 6): `trigger_model_type: "0-422"` +
  `trigger_event: "created"` = "when an employee closes a day". Covers conditioning on
  `break_violated` (the editor cannot compare two columns), the other usable fields, the
  `time_tracking_day_closure` placeholder root key, `action: "test"` working despite the type
  having no generic read tool, that an unconditioned workflow fires once per employee per working
  day, that `created` fires once per employee+date ever (withdraw-and-re-close is an update), and
  that no Slack `record_actions` buttons exist for it.
- **using-alluvo-operator**, **head-of-disposition**: route the "Pausenzeit nachträglich geändert"
  release failure and the day-close automation request to the right skill.

### Changed — 2026-08-03 Vertrags-Eingabevalidierung verschärft (alluvo#2928)
- **manage-contract-lifecycle** (step 1, write guards): `manage-framework-contract` `update` now
  validates `client_site_id` **and every entry of `client_site_ids`** for company ownership and
  Branchenzuordnung (`industry_classification`) — the same two rules `create` always enforced. A
  foreign or unclassified Einsatzbetrieb is an error instead of reaching the rendered AÜG §5
  Branchenerklärung silently. A combined `company_id` + client-site change is judged against the
  **new** company.
- **manage-contract-lifecycle** (step 1, write guards): `client_site_safety_agreement_id` on
  `add_role` / `update_role` must belong to one of the contract's Einsatzbetriebe. A nonexistent or
  foreign id returns a clean error listing the covered sites instead of a raw database failure.
- **manage-contract-lifecycle** (step 2): `manage-assignment-contract` `create` refuses a
  `company_id` that contradicts `framework_contract_id`'s company rather than silently overriding
  it — the old behavior produced an AÜV on company B pricing off company A's Rahmenvertrag.
- **manage-contract-lifecycle** (step 2, step 4, Unresolved-fields table): `contact_id` must be
  linked to the contract or its company before it can be set — enforced at preview time on
  `complete_assignment`, `manage_einsatz` and `commission_as_agreed`. Scope the Contact (`0-105`)
  search to the company or link it first via `manage-association`; a bare search hit is not enough.
- **manage-contract-lifecycle** (step 2, Einsatz bullets): `acknowledge_duration_override` and
  `duration_override_reason` are no longer accepted on `manage-assignment-contract` `update` (they
  were accepted-and-ignored) and are rejected as unrecognized fields. The §1 Abs. 1b AÜG
  Überlassungshöchstdauer is assessed on `create` (both params) and on `add_replacement`
  (`acknowledge_duration_override` only).

### Changed — 2026-08-03 Dienstplan-Nachtrag für vergangene Tage + ArbZG-Vergangenheitsdemotion (alluvo#2991)
- **build-dienstplan** (step 3, new warning class `past_date_backfill`): a past-dated Schicht is no
  longer refused outright. `create`, `add-shift` and `update-shift` take `past_date_acknowledged`
  (+ optional `past_date_acknowledgement_reason`); until it is passed the day comes back as a hard
  warning asking for confirmation, and the acknowledging operator is recorded on the Schicht. Two
  limits stay hard: dates before the backfill window (`past_date_outside_window` — the current
  tenant-local month by default) and any edit/cancel/delete of an already-persisted past Schicht.
  Never set the flag on the assistant's own initiative.
- **build-dienstplan** (step 6 lock box): corrected — `add-shift` on a past day is no longer part
  of the lock. Editing, cancelling, deleting and moving a Schicht backwards into the past stay
  hard-blocked, and the `confirmed: false` preview now names that lock instead of showing a clean
  proposal that only fails at write time.
- **build-dienstplan** (§3/§5 box): an ArbZG hard violation whose affected days lie entirely in the
  past is demoted to a non-blocking hint — one old breach no longer blocks every future write on
  the Einsatz. A violation touching today or later still hard-blocks, and the demotion never
  applies to the contract window, the double-booking guard or the backfill window.
- **build-dienstplan** (hard-limits bullet): §5 rest is measured between calendar-day envelopes,
  not between consecutive Schichten — the gap inside a geteilter Dienst is not a rest period and
  never a §5 violation. The §3 day total still counts both Teildienste, unchanged.
- **build-dienstplan** (6b): the backfill acknowledgement is an operator release; the employee app
  does not offer it, so an employee still cannot nachtragen a missed day.
- **approve-stundenfreigabe**: a past day's Schicht cannot be re-planned (settle the number in time
  tracking), but a Schicht never recorded at all can still be entered via the acknowledged backfill.
### Added — 2026-08-03 BankAccount + EmergencyContact über `manage-model`, IBAN maskiert (alluvo#3024)
- **onboard-new-employee** (new step 2b): Bankverbindung (`0-21`, BankAccount) and Notfallkontakt
  (`0-16`, EmergencyContact) are now ordinary `manage-model` types — readable via `get-model` /
  `search-model` / `query-model` / `get-model-schema`, writable via `manage-model` and
  `bulk-manage-model`. Previously both had no MCP surface and had to be left to the web app.
  Documents the exact create fields (BankAccount: `employee_id`, `account_holder_name`, `iban`
  required, `bic` / `bank_name` / `is_active` / `is_primary` optional; EmergencyContact:
  `employee_id`, `first_name`, `last_name` required, `relationship` enum + `mobile` / `phone`
  optional).
- **onboard-new-employee**: the `iban` is **masked in every MCP read** (`DE89********3000` — first
  4 + last 4 characters, one-way and unconditional). The skill must not read an IBAN back to
  confirm it, compare two IBANs, copy one between records, or present a masked value as the
  account number; a BankAccount's search/preview label is that masked IBAN and identifies nothing
  for the operator.
- **onboard-new-employee**: `iban` is mod-97 checksum-validated on create *and* update — a
  placeholder or example IBAN is rejected outright, so never invent one to clear the preview.
  Whitespace and casing are normalized on write. `is_primary: true` is server-side exclusive (the
  employee's other accounts are demoted automatically) — no manual reset call, and two primaries
  cannot be set.
- **onboard-new-employee** (step 2): disambiguated the `bank_details` **document** requirement in
  `missing_non_blocking` from the `BankAccount` **record** — filing the scanned Personalfragebogen
  page does not create the record payroll reads, and vice versa.
- **triage-data-quality**: no change — no `IssueDefinitionIdentifier` covers bank accounts or
  emergency contacts, so the data-quality catalog never reports these gaps.

### Changed — 2026-08-03 Tagesabschluss-Gate + expliziter Rückzug in der Stundenfreigabe (alluvo#3021)
- **approve-stundenfreigabe** (new section "Tagesabschluss"): releasing hours now requires the
  employee to have closed every day being released ("Tag abschließen"). The attempt fails with a
  422 naming the unclosed dates; only the days actually being released are checked (Teilfreigabe
  stays possible), days without a completed entry are skipped, and days before the employee's
  go-live are floored out. Break-compliant historical days were backfilled, so migrated and
  zvoove-imported weeks are not walled off — a past day with a short break stays open and needs
  the § 4 ArbZG reason, as the previous break gate already required.
- **approve-stundenfreigabe**: closing a short-break day is a § 4 declaration (Belehrung, reason,
  one-off yes/no, prevention measures when recurring). Einsatz owners are notified once per
  distinct declaration, and a support request raises a high-priority task due the next working
  day. The closure has **no MCP surface** — it cannot be read, created or withdrawn via a tool.
- **approve-stundenfreigabe** (new sub-section "Changing a closed day"): the lock is
  employee-side only — the five self-service write paths refuse a closed day and the employee
  withdraws the closure to correct it, which is impossible once the client signed the day or the
  week left `Draft`. Operator/MCP/zvoove writes are unaffected, do **not** reopen the day and do
  **not** re-run the break check, so re-derive the break after correcting a closed day. Explicitly
  separated from the harder "released or approved hours are locked" rule below it.
- **head-of-disposition** (§ 1e Stundenfreigabe backlog): a week stuck in `Draft` is often one
  unclosed day — chase the Tagesabschluss before delegating a full backlog chase; after the week
  leaves `Draft` the correction becomes Disposition work.
- **using-alluvo-operator**: routing entry for "Mitarbeiter kann die Stunden nicht freigeben /
  Tage sind noch nicht abgeschlossen / Abschluss zurückziehen" → `approve-stundenfreigabe`.
### Changed — 2026-08-03 Dublettenmerge: Overflow, Recency, Company-slug (alluvo#2935)
- **merge-duplicate-companies** (step 3a): a differing value is no longer automatically a
  `conflict`. Three resolutions are named — a Contact's second `phone` overflows into an empty
  `mobile` (shows up under *Columns filled from duplicate*, does not gate the merge; only a
  kept record that already has a `mobile` makes `phone` a real conflict), recency columns take
  the best value (`last_activity_at` / `last_contacted_at` = newest, `first_*` = earliest, so
  contact dates need no post-merge repair), and a merged-away email/name is absorbed into
  `alternative_emails` / `alternative_names`.
- **merge-duplicate-companies** (step 3a): `slug` is now a non-mergeable column on Company, so
  every Company merge lists it as a non-blocking `not_carried` line — the kept record's URL is
  unchanged. Company merges no longer hard-fail on `clients_slug_unique`.
- **triage-data-quality** (step 5): the `conflict` definition tightened to match, with a
  one-line pointer to the three non-loss resolutions.

### Changed — 2026-08-03 Slack-Workflow-Nachrichten mit automatischer Herkunftszeile + `{{trigger.*}}` (alluvo#3012)
- **build-automation-agent** (section "Slack delivery, and approve/reject buttons"): every
  workflow Slack message now ends with an automatic muted `context` footer naming who triggered
  the run and where the record came from (`Ausgelöst von … · Quelle: … · Automatisierung: „…"`;
  `Automatisch ausgelöst` when no human was behind it, `Quelle:` dropped when the record has no
  `record_source`). Skills must not author their own "triggered by / source" block. A config
  with only `message` and no `blocks` is now block-rendered too — its text moves into a
  `section` block so the footer can hang off it.
- **build-automation-agent**: new guidance to word a Slack message for the record's **state**,
  not for one origin path — conditions never match the path that produced the state, so a
  `stage equals won` workflow fires for a client-portal checkout *and* for an operator marking
  a contract won by hand. Add a `record_source equals client_portal` condition when a workflow
  really must fire only for self-service bookings (AssignmentContract `0-31` carries the field;
  FrameworkContract `0-30` does not).
- **build-automation-agent** (Terms + Slack section): documents the new `{{trigger.actor_name}}`,
  `{{trigger.actor_email}}`, `{{trigger.source}}`, `{{trigger.source_label}}` and
  `{{trigger.source_detail}}` placeholders — available on record-triggered runs
  (`created`/`updated` and scheduled enrollment sweeps), empty when no human triggered the
  write, absent entirely on a record-less scheduled run.

### Changed — 2026-08-03 Freigegebene/genehmigte Stunden sind unveränderlich (alluvo#2993)
- **approve-stundenfreigabe** (new section "Released or approved hours are locked"): a
  `TimeEntry` (`0-6`) is now immutable for everyone once it carries a company approval or its
  day was released against a captured client signature (an approved Stundenfreigabe week).
  `manage-model` update/delete on such an entry is refused by policy — expected behaviour,
  not a permission bug. The employee app hides the edit affordance on locked entries.
  Correction runs through the client-proposed day-correction flow (employee accepts/rejects,
  rejection escalates to the operator), never through a TimeEntry edit.
- **build-dienstplan** / **record-absence**: the "correct the actual hours in time tracking"
  guidance for started/past Schichten gains the boundary — that path holds only until the day
  is released or approved; after that, the day-correction flow is the route.

### Changed — 2026-08-03 Go-Live-Cutoff erledigt jetzt auch überfällige AU-Bescheinigungen (alluvo#2990)
- **approve-stundenfreigabe** (section "The go-live cutoff hides requests"): the per-employee
  go-live cutoff now also settles **overdue AU-Bescheinigungen** — an AU whose
  `medical_certificate_due_at` fell before the go-live is suppressed in the employee's app
  entirely (no overdue badge, no deadline line, no upload button; the absence itself stays
  visible), skipped by the app's certificate counters, and excluded from the automatic
  employee reminder mail. An AU with no recorded deadline is never auto-settled. Operator
  surfaces are deliberately unchanged. The "MCP figures do not see the cutoff" list gains
  AbsencePeriod queries.
- **record-absence** (new section "Pre-go-live AUs — you see them, the employee does not"):
  "the employee says their app shows nothing to upload" is expected for a migrated absence,
  not a bug — the operator's AU-überfällig view and AbsencePeriod queries stay unfiltered.
  Also corrected the AU-Bescheinigung field names to the real schema
  (`medical_certificate_required` / `_received` / `_received_at` / `_due_at`, read-only
  `medical_certificate_status`: `not_required` / `outstanding` / `overdue` / `received`) —
  the previously listed `certificate_submitted` / `certificate_required_by` /
  `is_follow_up_certificate` / `certificate_covers_*` do not exist.
- **onboard-new-employee** (step 6): setting a go-live date also settles pre-go-live
  AU-Bescheinigungen; the "hides requests, approves nothing" note now says no AU is marked
  received.
- **using-alluvo-operator**: routes "AU überfällig, aber der Mitarbeiter sieht in der App
  nichts zum Hochladen" to `record-absence`.
- No MCP tool, parameter, enum or schema changed — product-flow reach only.

### Changed — 2026-08-03 Stundenfreigabe: nur erfasste Wochen sind freigebbar, "Vereinbart" ist jetzt der Plan (alluvo#2981)
- **approve-stundenfreigabe** (section "Which weeks the employee actually sees", rule 2
  rewritten): the employee's approvable list *and* its badge now require **tracked** hours
  (Ist > 0 **or** `agreed` > 0), not merely *any* hours. A week that is nothing but a
  Dienstplan is filtered out — it used to list as fully selectable with a "0,00 h" badge, so an
  employee could tick it and walk a ward manager through signing nothing. `agreed` stays in the
  rule because a client or operator correction writes that span and it is what gets billed.
  Consequence written out: "the employee doesn't see week X" now also means "nobody tracked any
  time in it", and the fix is tracking, not chasing.
- **approve-stundenfreigabe** (same section, new paragraph): the nightly deadline run is
  deliberately **broader** than the employee's own list — automatic promotion Draft →
  PendingClient still needs only planned *or* tracked minutes and fires once the week's last
  planned Schicht is past. So a planned-only week can still reach the client by deadline while
  the employee cannot release it manually; "why is this week not pending client?" has two
  distinct answers to check.
- **approve-stundenfreigabe** (new section "Reading the employee's week back to them"):
  **Vereinbart** in the employee app is now the **planned** day (sum of its Schichten, net of
  the § 4 ArbZG break), not `agreed_*` — the builder writes `agreed_*` equal to the tracked
  time, so that column used to repeat Erfasst and read "-" whenever nothing was tracked, while
  the Abweichung beside it measured against a plan that was never displayed. `agreed_*` is
  unchanged and remains the **billing basis**; only what the employee is shown changed. Stated
  explicitly so an operator quoting a number off an employee's screen does not conflate the
  Dienstplan figure with the billed one.
- **approve-stundenfreigabe** (same section): a planned day is **not** flagged as a deviation
  until its Schicht has ended — the cut-off is the shift's own end, not midnight, so a
  half-tracked day or a running timer is not a shortfall either. Opening the wizard on a Monday
  used to report the rest of the week as `missing` and set `has_deviation` on the running week.
  Therefore `has_deviation` on a *current* week now means something real and must not be
  dismissed as "the week isn't over yet".
- No MCP tool, parameter, enum or schema changed — product-flow only.

### Changed — 2026-08-03 Go-Live-Datum pro Mitarbeiter; `manage-record-settings` kennt jetzt Employee (alluvo#2977)
- **approve-stundenfreigabe** (section "Which weeks the employee actually sees", extended to
  three rules): an employee's approvable weeks are now additionally floored by their **alluvo
  go-live date**. Every week that *ended* before it is dropped; a week that **straddles** the
  go-live stays offered, because it carries real tracked hours from after it. The cutoff
  **composes** with the six-week look-back — the window bounds everyone's backlog, the date
  removes more for an employee onboarded in a later migration wave. So a legitimately absent
  week now has three explanations, not two.
- **approve-stundenfreigabe** (new section "The go-live cutoff hides requests — it approves
  nothing"): resolution order is per-employee override → tenant-wide
  `employee_app.go_live_date` → no cutoff, read and written via `manage-record-settings` on
  `0-2` (`describe` / `set` / `clear`). Three things stated explicitly because getting them
  wrong is harmful: it **approves nothing** (no `TimesheetWeek` marked approved, no
  acknowledgement stamped, clearing the date brings everything back — a released week carries a
  real client signature and a hidden one has none, which matters in an AÜG-relevant record); it
  settles **Einsatzmitteilung confirmations** by the same rule, keyed on when the §11
  notification was *sent*, and never auto-settles a receipt with no recorded send date; and
  **MCP figures do not see the cutoff** — it filters the employee-app surfaces, not the data, so
  a `TimeEntry` count or a pending-Einsatzmitteilung search still includes the pre-go-live
  period. The skill's header note was corrected accordingly: it is read-only *on hours*, not
  write-free.
- **onboard-new-employee** (new step 6): setting the go-live date is now part of onboarding for a
  tenant migrating its workforce in waves, via `manage-record-settings`
  (`describe` first — keys are model-scoped) with the same "hides, never approves" caveat.
  Flagged that `manage-record-settings` has **no `confirmed` parameter**, unlike the rest of the
  skill's writes — `set` applies immediately, so name the employee and date and get an explicit
  yes first. The same value is editable on the employee's **Einstellungen** tab in the app.
- **head-of-disposition** (steps 1e + 1f): both manager backlog lists can now overstate reality
  for a migrated employee, because the cutoff is invisible to the underlying query — pre-go-live
  weeks still appear in the time-entry count and pre-go-live Einsätze still read
  `assignment_notification_acknowledgement_state: pending`. Check the employee's go-live before
  delegating a chase they cannot act on — and don't report those rows as settled either.
- **using-alluvo-operator**: routing entry for "Mitarbeiter sieht keine Stundenfreigabe" /
  "Altdaten aus dem Vorsystem ausblenden" / "Go-Live-Datum eines Mitarbeiters".
- Note for both skills: `manage-record-settings` is **no longer Company-only** — it documents
  `0-2` (Employee) alongside `0-3` (Company), and the Company side now also lists the
  `timesheet.*` hours-approval keys that were always supported but undocumented.

### Changed — 2026-08-02 Stundenfreigabe: Tagesstunden, leere Wochen und Gegenbestätigung (alluvo#2939)
- **approve-stundenfreigabe** (steps 1–2, corrected): the time-entry read path documented two
  things that do not hold. `TimeEntry` carries **no `status` field** — approval state lives on a
  separate `TimeEntryApproval` record with no MCP model type, so the previous
  `status: submitted` filter matched nothing; the real filterable fields are `employee_id`,
  `assignment_id`, `type` (`work` | `break`) and `start`. And **a worked day is several rows**:
  submitting a shift writes work → break → work, so an ordinary "06:00–14:12 with a 30-minute
  break" day is two `work` rows plus one `break` row. Group by calendar day, keep `type: work`
  and sum `duration_hours` — reading a single row as the day is how a 15,4 h weekend gets
  reported as 6,73 h. Added that the day's break is **derived** (span − summed work minutes),
  which also covers paused timers and untracked gaps, so it is that figure — not a `break`
  row's own duration — that gets compared against the § 4 ArbZG break.
- **approve-stundenfreigabe** (new section "Which weeks the employee actually sees"): weeks are
  now clamped to the Einsatz's own start/end and a week with neither planned (Soll) nor tracked
  (Ist) minutes is filtered out of the employee's approvable list and its badge. A missing week
  is therefore expected when it lies outside the Einsatz or is empty — check for a Schicht or a
  time entry before escalating. Also documented that **counter-confirmation follows a client
  edit, not a break**: the employee is asked to counter-confirm only where the agreed start,
  end or break differs from what they tracked (a scheduled break alone no longer triggers it),
  and their objection window starts when the client confirmed, independent of the client's own
  deadline.
- **head-of-disposition** (step 1e): same `status: submitted` correction for the backlog query,
  plus count `type: work` only and group by employee and date — an entry count is not a day
  count. Noted that empty or out-of-Einsatz weeks are no longer shown to the employee, so they
  are not a backlog item to delegate.

### Changed — 2026-08-02 Personalbedarf-Matching, Vorschlagsmail, Bedarfsgruppierung und ROI-Aufgabe (alluvo#2940)
- **match-bench-to-clients** (step 2 role-score note, rewritten): the standing claim that *"the
  Fachweiterbildung axis does not reach these scores yet"* is no longer true for the
  `StaffingDemand` path. A `0-415` demand now carries its required role's `specialty` into
  matching, so a same-Gruppe, same-Level candidate with the **wrong** Fachweiterbildung scores
  **0.4** on the role feature instead of counting as an exact hit, and a covering specialty
  bridges *across* Gruppen at **0.5**. Spelled out that this is a downgrade and **never** an
  exclusion (an Intensiv-Kandidat stays a legitimate Notfall-Vorschlag — read 0.4 as "fachlich
  daneben, prüfen"), that a demand naming several roles of one Gruppe with *different*
  specialties imposes no specialty constraint at all, and that the nightly
  `EmployeeStaffingOpportunity` (`0-126`) shortlists — what `get-profile` and **profilvertrieb**
  read — still carry no specialty on the requirement side, so a `0-126` role score must not be
  explained with a specialty case.
- **match-bench-to-clients** (step 3, new notes): a short or empty `0-416` shortlist is now a
  *scoring verdict*, not just the cap — a **minimum score of 25** (bucket `below_min_score`) and
  a **hard Sektor gate** (both sides state a Sektor and share none → rejected outright; fails
  open on an unknown Sektor) run **before** the shortlist cap of 10, so "keine Vorschläge" no
  longer implies an empty pool and a lone weak candidate is no longer proposed as the only
  suggestion. Added that **Freistellung** (`duties_suspended_at` on the current EmploymentPeriod)
  now excludes an employee from automated matching entirely, that the auto-drafted proposal mail
  restates the Bedarf and lists each candidate under their **own qualifying `StaffingRole`**
  (not the often-empty `current_position`), and that `get-timeline` accepts
  `subject_type: "0-415"` for the demand's own action/task/issue/ticket/email history.
- **match-bench-to-clients** + **head-of-disposition** + **bench-check** (new): the second,
  separate **"Anschlusseinsatz prüfen: <Bedarf>"** task (`0-5`) filed when a matched employee is
  verleihfrei or their Einsatz ends within ~14 days — attached to the demand (`0-415`) and the
  client Company (`0-3`), owned by the demand's creator, due on `valid_from`, body naming the
  situation plus **Zusatzstunden** and **Zusatzumsatz** with a confidence marker (no € figure
  where hours or rate are unknown — an honest gap, not a zero). Documented that it is
  deliberately independent of "Personalbedarf prüfen" (different question, closed separately),
  that its absence merely means every candidate is booked past the demand, and that an employee
  appearing both here and on the Bench is the strongest case to work first.
- **head-of-disposition** (§1c `0-416` score note): corrected the weight breakdown to include the
  new **availability 0.05** feature and added the Freistellung + Sektor gates to the gating
  order. Clarified that gemeldete Verfügbarkeit is a **bonus, not a filter** — reporting nothing
  leaves the feature inactive and never costs points, so a low score must not be read as "hat
  keine Verfügbarkeit gemeldet" — and added `below_min_score` to the no-proposal reason breakdown
  as the inverse signal of a high radius count ("people are reachable but nobody fits well").
- **head-of-disposition** (§1c) + **intake-personalbedarf** (step 1): **Bedarfe are grouped** —
  a `0-415` row is one *line*, and several lines routinely describe one Bedarf. Lines hang off an
  **anchor** (`demand_group_id` null, lines under `children`; a child never points at another
  child), folded in on create when company + Abteilung + Rolle + an overlapping/adjacent period
  match an **open** anchor. Reporting now counts anchors with the line count beside it (a raw row
  count overstated the backlog ~334 lines : ~97 Bedarfe), with the instruction to confirm
  filterability via `get-model-schema` and otherwise group the fetched rows in-memory rather than
  quoting the row count. Added that grouping happens **only on create** (correcting a line never
  re-parents it) and that proposal drafting dedupes over the group plus a 7-day
  Kontakt+Rolle+Einsatzort window — so one proposal for a multi-line group is correct, not a
  missed demand.
- **intake-personalbedarf** (step 2 + step 5): pick the role's Fachrichtung deliberately, since a
  wrong one now demotes every otherwise-suitable candidate to 0.4 and, with the minimum score,
  can be the difference between a proposal and none — and hedging with a second,
  differently-specialised role of the same Gruppe *widens* rather than narrows the shortlist.
  Step 5 now lists what matching leaves on the demand (both tasks, the restated proposal mail,
  `get-timeline` on `0-415`).
- **bench-check** (step 1 + new step 6): **freigestellte** employees are flagged "freigestellt —
  nicht vermittelbar" rather than counted as bench capacity (they appear in no shortlist however
  free their calendar looks), and a new step cross-checks the "Anschlusseinsatz prüfen" tasks via
  `get-open-tasks` — the same population seen from the demand side, with a quantified placement
  attached.
- **triage-data-quality** (step 3c): a role's `specialty` now moves Personalbedarf shortlists, so
  a mis-tagged one can drop a suitable person out of every proposal — reinforcing the existing
  "don't guess a `specialty`" rule with *why* a missing specialty is the safe state (it imposes
  no constraint).

### Changed — 2026-08-02 Lesebestätigung der Einsatzmitteilung (Zustandsfeld, Erinnerungen, Eskalation) (alluvo#2887)
- **manage-contract-lifecycle** (new step 5a *The employee's read receipt*): the dispatched §11
  Abs. 2 Satz 4 AÜG Einsatzmitteilung can now ask the deployed employee to confirm it in the
  employee app. The state sits on Assignment (`0-401`) in **two** fields that answer different
  questions: `assignment_notification_acknowledgement_state`
  (`not_requested` / `pending` / `confirmed` — **whether**) and
  `assignment_notification_acknowledged_at` (**when**). Outstanding confirmations are found
  *only* via `state: pending`; the timestamp is empty for `not_requested` exactly as it is for
  `pending`, so filtering `acknowledged_at IS NULL` reports the whole pre-feature backlog as
  overdue. Spelled out that it is a **proof of receipt, never a gate** — it blocks no dispatch,
  no Schicht, no Zeiterfassung, no Dienstplan, no commissioning — that every correction re-opens
  it (state falls back to `pending`, timestamp cleared, by design), and that **two** switches
  must both be on: a per-tenant platform feature flag that is **off by default** plus the setting
  `contract.require_assignment_notification_acknowledgement` (default true). Also documented the
  automatic cadence the skill must not duplicate: `assignment_notification_reminder_enabled`
  (true), `..._reminder_start_days_before` (7), `..._reminder_interval_days` (2),
  `..._escalation_days_before_start` (1), measured against **Einsatzbeginn** — at the escalation
  threshold, or at once for an employee with no employee-app user, employee reminders stop and a
  high-priority task goes to the Einsatzvertrag owner. No dedicated MCP tool exists; read it with
  `query-model` / `search-model` / `count-model`.
- **head-of-disposition** (new step 1f *Unbestätigte Einsatzmitteilungen* + matrix column):
  outstanding confirmations are a real work list now — `search-model` on `0-401` with
  `assignment_notification_acknowledgement_state: pending`, prioritised by `start_date`. Warns
  against the null-timestamp filter, against reporting it as a Freigabe-Gate, and notes the
  system already reminds and escalates on its own, so this is mostly a leading indicator.
  All-`not_requested` means the tenant does not have the feature on — say so instead of
  reporting "nothing outstanding".
- **build-dienstplan** (step 7): a corrected Einsatzmitteilung after a roster change re-opens the
  read receipt (`pending`, timestamp cleared). Flagged as intended rather than a regression, and
  as nothing that holds up the Dienstplan.
- **using-alluvo-operator**: routes "wer hat die Einsatzmitteilung noch nicht bestätigt / offene
  Lesebestätigungen" to `head-of-disposition`.

### Changed — 2026-08-02 Benachrichtigungs-Kanäle sind einstellbar, Kunden bekommen sie im Portal (alluvo#2912)
- **clean-inbox** (Inbox notifications): corrected the claim that per-user channel settings are
  "not editable from here" — they are. `get-notification-preferences` /
  `manage-notification-preferences` (`action: "update"`, preview → `confirmed: true`) read and
  set in-app / email / push / Slack and `email_frequency` per type, for the calling user or,
  with permission, a colleague (`user_id`). Named the two type keys this skill actually deals
  with: `inbox.ticket_created` (email, push and Slack can be switched off; in-app cannot) and
  the daily `inbox.queue_digest`. Transactional types stay always-on and are silently skipped.
- **approve-stundenfreigabe** (new *How the client is notified*): the client approver's
  "ready to confirm", deadline-reminder and auto-approved notices are no longer mail-only.
  A contact with an active client-portal account also gets them in the portal's notification
  centre and as web push, following their own channel preferences; a contact without one still
  gets mail alone — which remains the common case. The contact timeline logs an outbound Email
  either way, so `get-timeline` on `0-105` is the check before telling an operator the client
  was never informed. The mail is transactional and cannot be silenced; only push and in-app
  can, by the client in the portal.
- **using-alluvo-operator**: routes "Benachrichtigungen umstellen / keine E-Mails mehr" to
  `clean-inbox` and "hat der Kunde die Stundenfreigabe bekommen" to `approve-stundenfreigabe`.

### Changed — 2026-07-31 Blanke Relationsnamen sind gültige Filterfelder (alluvo#2872)
- **prospect-companies** (step 3) / **profilvertrieb** (step 2): pinned down how the
  `sectors` / `companySegments` filters both skills already recommend actually have to be
  written. The field is the **bare relation name** (`sectors`, not `sectors.id`) — previously
  a single-segment relation was treated as a column and the call blew up with
  `column companies.sectors does not exist`; it now resolves to the relation. The value is a
  **Sector (`0-70`) / CompanySegment (`0-198`) id**, never a name. Only `eq` / `in` / `neq` /
  `not_in` match a bare relation by id, and the negatives mean "has **none**" (a company with
  no sector at all passes a `neq`), not "has a different one". Everything else keeps its own
  handling: a text/range match needs the **dotted path** (`sectors.name` + `like`) because a
  comparison operator against the bare name fails the call rather than being skipped, while
  `is_null` / `is_not_null` work as presence checks. Scalar FK columns such as
  `staffing_role_group_id` are unaffected — a real column always wins over a same-named
  relation, so the numeric-filter rules in **triage-data-quality** stand.

### Changed — 2026-07-31 `invite-user` ist jetzt idempotentes Einladen-oder-erneut-Senden (alluvo#2864)
- **onboard-new-employee** (step 5, now *Send invitation — or resend the login link*): the
  `invite-user` record action on Employee (`0-2`) is idempotent — once the employee has a linked
  user or a non-cancelled invitation, the same action **resends** the login link instead of
  provisioning a second account (label switches to "Einladung erneut senden", the wizard drops its
  user-type step, so `user_type_slug` only applies to a first invite, and an expired or
  nearly-expired invitation gets its expiry extended). Accordingly: "already has a linked user
  account" and "invitation already pending" are no longer `unavailable_reason` blockers; the
  remaining three (no email, no employment relationship, no active Salary as Arbeitsvertrag proxy)
  gate the **first invite only**; and an inactive `EmployeeAppModule` now leaves the action listed
  but **disabled** with a readable reason instead of failing mid-execution. Also recorded that the
  Employee `resend-invitation` action was removed entirely — never call it — while the deprecated
  `invite-employee-user` fallback now accepts the resend case too. Output line updated to report
  first invite / resend / blocked-with-reason, and "Einladung erneut senden" added as a trigger
  term.

### Added — 2026-07-31 Slack-Nachrichten können Approve/Reject-Buttons tragen (alluvo#2861)
- **build-automation-agent** (new section *Slack delivery, and approve/reject buttons
  (`send_slack_message`)* under step 6): documented Slack as the third delivery target next to
  `transactional_mail` and `create_task` — `channel_id` / `user_id`, `message`, `blocks`, and the
  new `record_actions` key (`true` = every Slack-enabled action, or an explicit list like
  `["approve", "reject"]`). Plus the five non-obvious rules: the button set is **derived from the
  action catalog** and cannot be authored (a `blocks` `actions` entry only makes link-out
  buttons), it needs a triggering record so a record-less scheduled report gets none (a scheduled
  **enrollment** sweep does), a click executes as the *clicking* Slack user under their own
  permission + state checks (unmapped or unauthorized ⇒ private refusal, nothing written), the
  first click resolves the whole set and buttons expire after 7 days, and a button can carry no
  free text. Today the only Slack-enabled actions are AbsencePeriod (`0-13`) `approve` / `reject`.
- **record-absence** (new subsection *Approving or rejecting a submitted Abwesenheit* after step 6):
  the `approve` / `reject` / `request-revision` record actions with their allowed statuses and
  reason rules, and the note that `approve` / `reject` are exactly the two actions clickable from
  Slack — including that a Slack `reject` leaves `review_note` empty, so a rejection that needs an
  explanation (or a `request-revision`) belongs in the app.
- Cross-links between the two skills for the Slack-approval path.

### Added — 2026-07-31 Anweisungen des Telefonassistenten sind jetzt änderbar (alluvo#2839)
- **clean-inbox** (new section *Inbox settings: the Vapi phone assistant's instructions*): the
  `update-vapi-instructions` record action on the inbox's phone channel (`manage-record-action`,
  `model_type: "0-302"`) writes the tenant's own instruction block **and** pushes the recomposed
  prompt to Vapi in one step. Documented how to find the channel (`query-model` on `0-302` by
  `inbox_id`, then `type: phone` + `provider: vapi`), that the action only offers itself on such
  a channel with an assistant connected, the `inbox_channels.view` / `.update` permissions, and
  that `manage-model` is deliberately no alternative — a generic write would set `config` without
  pushing, leaving the live assistant on the old prompt.
- **clean-inbox** (same section): the write **replaces** the block (empty string deletes it) while
  the stored text is **not readable over MCP** — `config` is not serialized and the action's
  preview only echoes back what you passed — so the operator supplies the current text from
  Einstellungen before any edit; omitting `custom_instructions` entirely is a pure re-sync; and a
  failed Vapi push is not a failed save, so the retry is a re-sync, not a second edit. Also the
  content guardrail: tenant text may steer conversation STRATEGY (question order, weighting, tone,
  named contacts, opening hours) but never the hard rules (§ 201 recording/AI disclosure, no
  price or staffing commitments, the pinned closing sentence Vapi's hang-up detection matches).
- **clean-inbox** (*Geschäftszeiten*): corrected two claims that no longer hold — `InboxChannel`
  (`0-302`) is now readable via the generic tools (only `InboxMember` has no MCP surface), and a
  `business_hours` change **can** now be carried to the live phone assistant by re-syncing,
  instead of waiting for an engineer.
- **using-alluvo-operator**: routes "was der Telefonassistent sagt" / "Telefonassistent neu
  synchronisieren" to `clean-inbox`, explicitly not to `build-automation-agent`.
### Added — 2026-07-31 Auftragsbestätigung-Anhänge folgen jetzt `signing_method` (alluvo#2844)
- **manage-contract-lifecycle** (new step *4a. Auftragsbestätigung — what the customer receives*):
  which documents the order-confirmation mail attaches is decided by **how the contract was
  signed** (`signing_method`), not by whether the `signed_documents` collection happens to be
  non-empty. Documented the full table — `paper` → the countersigned upload, `digital` → **always**
  the generated bundle (it carries the Signature Card) even when a scan sits in `signed_documents`,
  `operator_confirmed` / unset → the operator's upload if there was one, otherwise the generated
  reference bundle — plus the safety net that an empty generated bundle falls back to
  `signed_documents` rather than sending an attachment-less mail.
- **manage-contract-lifecycle** (same section): the two operator consequences — `upload_signed_document`
  (`pdf_base64` over MCP) turns the completeness check green but does **not** swap the attachment of a
  portal-signed contract, and `commission_as_agreed` over MCP carries no upload (only `contact_id` +
  `agreed_at`), so it lands on `operator_confirmed` without one and mails the generated bundle.
- **manage-contract-lifecycle** (same section): documented the **`resend_order_confirmation`** record
  action (`manage-record-action` on `0-31` once `commissioned`/`performing`/`performed`, on `0-30`
  once `stage: won`) with its `recipient_contact_ids` / `new_recipient_contact_ids` / `bcc_emails`
  inputs — including that `new_recipient_contact_ids` adds recipients **durably** while unchecking one
  only skips this send, and that the resend follows the same attachment rule, so it must never be
  described to the operator as "resending whatever was uploaded".
- **manage-contract-lifecycle** (step 4): `commission_as_agreed` now also states that it mails the
  customer the Auftragsbestätigung, cross-linked to step 4a.

### Added — 2026-07-31 Automatisierungs-Agenten laufen jetzt auch auf Posteingängen (alluvo#2762)
- **build-automation-agent** (new section *Inbox deployments*): `manage-automation-agent` gained
  `deploy`, `undeploy` and `list-deployments`, binding an automation agent to an Inbox
  (`AgentDeployment`, model type `0-306` / `agent-deployments`) so it reacts to inbound tickets
  instead of a schedule. Documented the full param set (`inbox_id`, `inbox_channel_id`,
  `deployment_id`, `enabled_steps`, `daily_cap`, `per_ticket_daily_cap`, `is_active`), that
  `owner_id` is **required** here and must be an active *internal* user, that `confirmed: true`
  two-stage applies to `deploy`/`undeploy` **only** while `create`/`update`/`delete`/`enable`/
  `disable` stay single-shot, and the unique `(agent, inbox, channel)` slot with "all channels"
  as its own slot.
- **build-automation-agent** (same section): the operational truths an operator needs — the
  tenant feature gate is **off by default**, so a deployment can exist and silently never fire;
  the step whitelist defaults to `create_task`, `create_note`, `manage_model`,
  `enrich_relationship`, `create_staffing_requirement` and out-of-whitelist directives are
  **dropped, not queued for approval**; whitelisted steps largely execute **unattended** (only
  `send_email`/`send_invite` pause, `reassign_owner` is gated) with per-step undo from the run
  card; firing happens on *every* inbound contact message with a ~2 min debounce on
  WhatsApp/chat/web; caps default to 200/day and 5/ticket/day and silently skip when hit;
  `action: "test"` does **not** simulate the deployment path; the run reuses the agent's
  `enabled_tools` and `pseudonymize_pii` but **not** its `output_schema`; and `undeploy` is
  effectively **one-way** (the soft-deleted row keeps its uniqueness slot, so re-deploying the
  same tuple is rejected).
- **clean-inbox** (step 1 + Personalbedarf cluster + Related skills): a shared inbox may have an
  agent deployed on it whose run cards are **not** returned by `manage-ticket` `get` — the runs
  are invisible while their effects (tasks, notes, records, `StaffingDemand`) are not.
  Documented checking for existing coverage before tasking or routing a demand mail, correcting
  the previous claim that a shared inbox is always outside auto-capture scope.
- **using-alluvo-operator**: Automation entry and decision guide now route "Agent auf einen
  Posteingang setzen" / "welche Agenten laufen auf welcher Inbox" to `build-automation-agent`
  rather than `clean-inbox`.

### Changed — 2026-07-31 Pending-Anforderungen nennen jetzt ihr Wirksamkeitsdatum (alluvo#2832)
- **onboard-new-employee** (step 2, completeness): a `pending` requirement in
  `employee_operational.requirements` no longer carries the missing-case fix-hint. Its
  `fix_hint` now reads "Recorded — effective from <date>", and the new `meta` key carries
  `effective_at` (ISO `YYYY-MM-DD`) plus `href` to the record — and `label` with the future
  position's name on `current_position`. Documented naming that date when reporting a new
  hire's status instead of listing the item as an open task, that only `employment_period`,
  `salary` and `current_position` can be pending, and that pending items stay out of
  `missing` / `missing_optional` / `missing_non_blocking` and out of `is_complete`, while
  still counting against `score` until they take effect.

### Changed — 2026-07-31 Vapi-Anrufe sind jetzt Call-Records (alluvo#2771)
- **call-summary** (step 1): a Vapi-handled inbound call is now automatically recorded as a
  `call` activity (direction, outcome, duration, full transcript) the moment the ticket is
  created — before the operator ever runs this skill. Documented checking `get-timeline` on
  the contact/company for an existing matching Call before creating a new one, and using
  `action: "update"` on that `engagement_id` instead of `action: "create"` to avoid logging a
  duplicate.
- **clean-inbox** (step 3, "Always evaluate attachments"): a phone-ticket's Call is now linked
  via `ticket_activity` and visible on the contact/company timeline with its own transcript —
  documented reading that Call's transcript/`ai_summary` as the source of truth during triage
  instead of filing a duplicate Note from the ticket's `TicketMessage` text.

### Changed — 2026-07-31 Storno-Pfad für Einsatzverträge, WON→LOST gesperrt (alluvo#2772)
- **manage-contract-lifecycle** (stage machines, step 6): `manage-assignment-contract` gained
  a direct `action: "cancel"` (Storno) — two-stage, requires `cancellation_reason`, previews
  the termination cascade impact (mode, Einsätze/Schichten/SchedulePeriods counts, availability
  days released, employees notified) before confirming. Documented it as the preferred path
  over the previous `manage-record-action` `cancel_contract` (param `reason`), which still
  works underneath but was never mentioned in this tool's own action set.
- **manage-contract-lifecycle** (both stage-machine tables): `WON` now has **no onward
  transition** on either contract type — `transition` to `lost` from a signed contract is
  rejected server-side. Removed the old "`won` → `lost`" line and documented the refusal
  message's pointer to `action: "cancel"` / `mark_performed` (Einsatzvertrag) or "cancel the
  Einsatzverträge under it instead" (Rahmenvertrag, which has no Storno action of its own).

### Changed — 2026-07-30 Ticketreferenz-Formate, Betreff-Präfix und Telefon-Betreff (alluvo#2767)
- **clean-inbox** (step 1): documented that **two reference formats coexist permanently** —
  new tickets draw a sequential `TKT-000042` (six zero-padded digits) from a per-tenant
  sequence, while every pre-existing ticket keeps its random `TKT-ZZXBOLCA` form and was
  deliberately not renumbered. A reference is `TKT-` plus **six or more** letters/digits;
  take it verbatim from the row, never reconstruct it from a pattern, and never infer a
  ticket's age from its format.
- **clean-inbox** (new section "What the customer actually sees"): the outgoing subject is
  composed at send time and never written back to `tickets.subject`, so `get`/`list` **and
  the `reply`/`forward` preview all print the stored subject, not the one the customer
  receives**. Two send-time rewrites: the reference is prefixed (`[TKT-000042] <Betreff>`,
  and `[TKT-000042] Fwd: …` on forwards) on the four shared operational inboxes only — not
  on a private/custom inbox or the 1:1 path, and not a second time when the subject already
  carries it; and a phone (Vapi) ticket's **first** email goes out as "Ihre Anfrage bei
  \<Firma\>" instead of the stored "Telefonanruf von +49…", later replies using the stored
  subject again. Report the prefixed/retitled subject to the operator, and never claim the
  stored subject changed.
- **clean-inbox** (same section): inbound mail that misses on the Gmail thread id now falls
  back to the reference in the subject — gated on the **same inbox** *and* a sender address
  the ticket already knows (`contact_email`, or a linked Contact's `email` /
  `alternative_emails`). A freshly composed customer mail therefore usually rejoins the
  running Vorgang instead of opening a second one; split tickets still occur by design
  (unknown sender address, stripped reference, different inbox) and are worth reconciling
  during triage.

### Changed — 2026-07-30 Monatlicher Bulk-`create` prüft jetzt ArbZG (alluvo#2765)
- **build-dienstplan** (steps 3, 4, 6, 6a): withdrew the caveat added in alluvo#2763 — the
  monthly bulk `action: "create"` now validates §3/§5 through the same per-employee,
  cross-contract batch check as `add-shift`/`update-shift`. Documented what is specific to the
  bulk path: a hard violation refuses the **whole month atomically** (nothing is written, and
  `confirmed: true` does not push it through — the blocker replaces the preview), the rows are
  validated against **each other** and not just against persisted Schichten, rows the extraction
  left without a resolvable start/end are **skipped** by the ArbZG check (contract window still
  applies — fill those days in with `add-shift`), and hints (10–11h band, §7, §9/§10) appear in
  the preview **and** in the success response without ever blocking. A clean bulk `create` may
  now be reported as ArbZG-checked.
- **head-of-disposition** (AÜG/ArbZG section): an imported month is no longer "unverified" — it
  is refused as a whole if any day breaches a hard limit, so a month that exists is a month that
  passed.

### Changed — 2026-07-30 ArbZG rechnet pro Mitarbeiter über alle Einsätze (alluvo#2763)
- **build-dienstplan** (steps 3, 4, 6, 6a): §3/§5 are now checked against the employee's
  effective Schichten on **every other Einsatz** (any AÜV, any client), windowed to the planned
  ISO week(s) ±1 day. Documented the new hard blocks this creates (Spätdienst at client A →
  early shift at client B refused under the §5 floor; 4h + 7h at two clients = §3 breach), that
  the warning line **names the other client** (`cross_contract_conflict`), and that the foreign
  Schichten are read-only context — the fix is to move the Schicht on this side or coordinate
  with the other Einsatzvertrag's owner, never to cancel the other plan's shifts. Also recorded
  that the §3 ceiling is now the **calendar day's total** (two Teildienste of a geteilter Dienst
  add up) rather than per-interval.
- **build-dienstplan** (step 3 box, step 6): corrected a standing inaccuracy — the monthly bulk
  `action: "create"` did **not** evaluate §3/§5 at all (only contract window, double-booking,
  availability). Filed api-side as alluvo#2764. **Superseded within this release** — the gap was
  fixed before shipping; see the alluvo#2765 entry above for the behaviour that ships.
- **build-dienstplan** (step 6a): Dienstpläne originating from a **client-portal booking** are
  created as `published`, not `draft` — no silent phase, the first change notifies the employee
  (AÜG § 11 Abs. 2 S. 4). Contrasted with operator-planned Perioden (`draft` when the AÜV is
  signed, `provisional` when not). Added that portal checkout validates bookings against the
  hard guard rails (incl. §5 rest against a neighbouring day at a *different* client) **before**
  the AÜV and Schichten are written, so a rejected booking cannot be pushed through operator-side.
- **head-of-disposition** (AÜG/ArbZG section): the hard limits are per employee across Einsätze;
  such a conflict is a coordination item between the two Einsatzvertrag owners. Noted that an
  imported month must not be reported as ArbZG-checked.
- **approve-stundenfreigabe** (step 2): the §3 10h day sums every Schicht the employee worked
  that date, including hours under a different Einsatzvertrag.

### Added — 2026-07-30 Inbox folgen/entfolgen steuert die Eintreff-Benachrichtigungen (alluvo#2748)
- **clean-inbox** (new "Inbox notifications" section, description triggers): `follow-inbox` /
  `unfollow-inbox` are MCP-exposed record actions on the Inbox (`0-301`), run through
  `manage-record-action` (`list` to read the state — the offered action *is* the current
  subscription state; `execute` preview → `confirmed: true`). Documented the four things an
  operator gets wrong otherwise: both actions are **self-scoped** (no target-user parameter —
  nobody can be subscribed or silenced on their behalf); **unfollowing silences, it does not
  remove membership or access** (joining subscribes automatically, being removed unsubscribes);
  a subscription **only delivers to a member** of that inbox (or full-tenant-access), and
  `InboxMember` (`0-303`) still has no MCP surface, so membership must be added in the app
  first; and arrival notifications are **in-app + push, email off by default** — never promise
  an operator that following an inbox mails them. Also noted the per-ticket contrast
  (`follow-ticket` / `unfollow-ticket` on `0-300` cover replies and status changes on one
  ticket, not arrivals).
- **using-alluvo-operator**: `clean-inbox` entry and the inbox decision-guide line now name
  following/unfollowing alongside Weiterleitungsziele and Geschäftszeiten.

### Changed — 2026-07-30 `extend` widens the Einsatz in place; hard Overlap-/Vertragsfenster-Gates (alluvo#2740)
- **manage-contract-lifecycle** (Einsatz table, step 5, Verlängerung section): `manage_einsatz`
  `sub_action: "extend"` no longer always mints a new Einsatz. A **gap-free** continuation (new
  `start_date` on or before the source's `end_date` + 1 day, same Abteilung *and* Ansprechpartner)
  now widens the source Einsatz's `end_date` **in place** — no new Einsatz, no
  `extends_assignment_id`, and the source's `start_date` is untouched. The slice path survives only
  for a genuine break (gap ≥ 1 day) or an explicit `company_department_id`/`contact_id` change, plus
  one carve-out: a `with_plan` Einsatz with plan-derived `end_date` (Schichten, no
  `hours_arrangement`) always takes the slice path. Consequence for §11 AÜG: an in-place extension
  is an update, so **nothing auto-sends** — if the Einsatzmitteilung had already gone out it now
  understates the period, and the operator must re-send it via `send_assignment_notification` for
  the named `assignment_id`. Also corrected the claim that a Verlängerung makes the contract's
  `valid_until` "no longer a boundary": the envelope only re-derives while the contract is `draft`;
  from `sent` onward it is frozen and an over-long extension is refused with
  `CONTRACT_WINDOW_EXCEEDED` (same for an open-ended extension inside a bounded contract).
- **build-dienstplan** (step 3): the one-Einsatz-per-day overlap block is now documented as running
  on *every* write path including the monthly bulk `action: "create"` — a month import colliding on
  a single day is refused as a whole. Added the `contract_window` hard block and made explicit that
  it applies to **`with_plan` Einsätze too**: only the *Einsatz* window is plan-derived there, the
  signed *contract's* `valid_from`/`valid_until` is not, so "mit Dienstplan" never means "plan past
  the contract end" — extend the contract first, then plan.

### Added — 2026-07-30 Schicht-Umbesetzung: `reassign_shifts` on the Assignment (alluvo#2548)
- **build-dienstplan** (new step 6c, "Moving Schichten to a different employee"): documented the
  `reassign_shifts` record action on **Assignment `0-401`** via `manage-record-action` (guided by
  the `reassign-shifts-prompt`) as the only correct way to move shifts to another employee —
  cancel-and-recreate produces neither contract documents nor notifications and is now explicitly
  forbidden. Covers the two-stage `confirmed:false` → `confirmed:true` flow, the three **derived**
  modes (`konkretisierung` on a signed AÜV, `split_contract` / `replace_contract` on a pending
  one — never caller-chosen), the non-overridable blockers (role fit under `#NachUntenGehtImmer`,
  ArbZG hard limits only, blacklist, signed AÜV without Rahmenvertrag, started shift, terminal
  contract), the two acknowledgeable warnings (`acknowledge_absence_conflict`,
  `acknowledge_duration_override` — the operator's call, never the model's), and how to read the
  `effects` list (who is mailed when, and that a split/replace contract arrives as a **draft**
  still needing send-for-signature). Frontmatter now triggers on "Schicht umbesetzen" /
  "Umbesetzung". Added the boundary against `add_replacement` (Krankheitsvertretung adds a cover
  and keeps the Einsatz; an Umbesetzung moves it away).
- **manage-contract-lifecycle** (step 6): recorded a **fourth** way a pending AÜV reaches
  `cancelled` — an Umbesetzung that empties it resolves to `replace_contract`, voiding a
  signature link already sent and leaving a replacement **draft** contract for the incoming
  employee. A `cancelled` contract with a sibling draft is usually this, not a lost deal.
- **manage-contract-lifecycle** (step 5): the §11 Einsatzmitteilung now additionally carries the
  **§12 AÜG** disclosure (Tätigkeitsmerkmale, required qualification, Equal Pay / wesentliche
  Arbeitsbedingungen) — for *every* send, not only Umbesetzungen; don't describe it as a mere
  schedule notice or plan a separate mail for those terms. `assignment_id` also targets an
  employee who joined via an Umbesetzung.
- **record-absence** (new step 9): the fork after a Krankmeldung — `add_replacement` (Vertretung,
  employee keeps the Einsatz) vs. `reassign_shifts` (Umbesetzung, shifts move for good), with
  when each applies and the shared started-shift block.
- **bench-check**, **using-alluvo-operator**: route "employee drops out of a running Einsatz" to
  the Umbesetzung instead of drafting a new placement.

### Changed — 2026-07-30 StaffingRole substitution: specialty axis, new score table, level/group write guard (alluvo#2613)
- **match-bench-to-clients**, **intake-personalbedarf**: corrected the `#NachUntenGehtImmer`
  role-score table. The unknown-level case is **no longer symmetric** — an employee whose role
  carries no `level` now scores **0.0** against a demand whose level is known (was 0.6), so a
  Rollenkatalog gap drops candidates outright instead of blurring them; only an unclassified
  *demand* still falls back to 0.6. Downward substitution stays 0.8 but decays 0.05 per extra
  level of distance beyond one, floored at 0.6.
- **match-bench-to-clients**: noted that the two new specialty verdicts (cross-group bridge 0.5,
  in-group mismatch 0.4) **cannot appear in a `0-126` shortlist score** — the demand side
  carries no specialty — so they must not be used to explain a match. Specialty is enforced end
  to end in employee visibility (`get-employee-availability` view `explain`) and Einsatz
  substitution instead.
- **triage-data-quality** (step 3c, retitled "roles with no Gruppe, Level or Fachweiterbildung"):
  documented `specialty` as the third hierarchy field on `StaffingRole` (`0-100`) — writable via
  `manage-model`/`bulk-manage-model`, clearable to `null`, `hiddenByDefault`, and filterable
  only with the enum operators `in`/`not_in`/`is_null`/`is_not_null` (no `eq`), with the eleven
  allowed values. Added the **new 422 guard**: a `level` without a `staffing_role_group_id` in
  the same payload is rejected — and the group must be re-sent even for an already-grouped role,
  because validation reads the payload, not the stored row. A Gruppe without a Level stays the
  honest unclassified state. Added "don't guess a `specialty`" to the limits.
- **profilvertrieb**: disambiguated a role's `specialty` (catalog field) from an opportunity's
  `specialty_fit` (fachliche-Eignung verdict) — the former is pitch evidence, never a verdict,
  and never overrides a `conflict`.
- **using-alluvo-operator**: Rollenkatalog routing now names the Fachweiterbildung axis.

### Changed — 2026-07-30 1:1 email templates: `template_id` on `manage-1on1-email` draft (alluvo#2696)
- **call-summary**, **profilvertrieb**: `manage-1on1-email` `draft` now accepts a
  `template_id` to start from a saved EmailTemplate (new `email-templates` model type
  `"0-418"`, discoverable via `search-model`; active + shared-or-own only). Documented
  the placeholder roots (`contact.*` incl. `greeting` — du/Sie via the formality chain,
  `company.*` incl. `portal_link`, `user.*`, `tenant.*`), the per-field
  `subject`/`body_html` override, and that an unresolved placeholder blocks a
  `confirmed: true` draft until the field is overridden or a resolving `company_id` is
  passed.

### Changed — 2026-07-30 Dienstplan flow: employee shift self-service, date-scoped picker, visible § 4 breaks (alluvo#2693)
- **build-dienstplan** (new step 6b): employees can now add, retime, or cancel single
  Schichten on their own running Einsatz from the employee app, without an approval
  round-trip — the plan is no longer single-author. Documented what stays hard (ArbZG
  § 3/§ 5 limits, started/past shifts immutable, Locked Perioden refused; deletion cancels,
  never destroys) and that changes on an approved plan land in the same § 11 AÜG digest
  trail. Also noted the employee-side wizard now only offers contracts valid today, offers
  DepartmentShift presets, and displays the § 4 break with net hours.
- **approve-stundenfreigabe** (step 2): the employee wizard now displays the same
  net-of-break figure that gets billed, and a submitted plan may carry employee-originated
  shift changes — compare against the plan as it is now.
- **head-of-disposition** (step 1d): a Dienstplan gap can be employee-authored (self-service
  cancel) — check for a cancelled Schicht before treating a gap as a planning omission.

### Changed — 2026-07-30 Completeness gains a blocking axis, 5-state status, required home location (alluvo#2689)
- **onboard-new-employee** (step 2 rewritten): `get-profile-completeness`'s
  `employee_operational` block now carries two axes per requirement — `required` (is missing
  acceptable at all) and `blocks_completeness` (does a missing mandatory requirement count
  towards `score`/`is_complete`). Document-backed requirements are mandatory but non-blocking:
  reported under the new `missing_non_blocking` array as Personalakte to-dos, never as
  "employee incomplete". Never report "complete" without mentioning outstanding documents.
  Every requirement also reports a five-state `status` (`satisfied` / `missing_required` /
  `missing_optional` / `pending` / `not_applicable`): `pending` = correctly future-dated
  employment period/salary/position (a new hire is not "missing" these), `not_applicable`
  (e.g. work permit for an EU citizen) is excluded from the score. `home_location` is now a
  required field — flagged first, since without it geo-matching cannot see the employee.
- **bench-check**, **profilvertrieb**: the missing-home-location notes now say the home
  location is a *required* completeness field (the employee reports incomplete without one),
  making "add the Wohnort" the first fix to suggest.
- **triage-data-quality** (step 2): incomplete-employee issues cover missing *blocking*
  required fields only — document gaps never raise or resolve them; those live in
  `missing_non_blocking` and the coverage matrix instead.

### Changed — 2026-07-29 Spoken languages are Contact-rooted and enum-constrained (alluvo#2618)
- **onboard-new-employee** (new note in step 2): `get-profile-completeness`'s fix-hints for the
  CV buckets (Sprachen, Ausbildung, Berufserfahrung) name `source_type`/`source_id`, which
  `manage-model` does not accept — its parameters are `model_type`, `action`, `id`, `data`,
  `confirmed`. The skill now says to take the model type from the hint (`0-185` ContactLanguage,
  `0-183` ContactEducation, `0-184` ContactWorkExperience) and put the **Contact** id inside
  `data` as `contact_id`. Filed as the api-side hint-copy bug it is (alluvo#2654) and documented
  here rather than papered over.
- **onboard-new-employee**: `ContactLanguage.language` is now enum-constrained to lowercase
  ISO 639-1 codes (plus `sgn` for Gebärdensprache) instead of free text — the accepted list is
  spelled out, with the instruction to send the code, never a label like `"Türkisch"`, and to
  check `get-model-schema` for `0-185` when unsure. `proficiency` is optional (`native` …
  `basic`); leave it out rather than guessing a level.
- **enrich-contacts-from-activities** (guardrails + `references/extraction-patterns.md`): the
  same ISO vocabulary now backs two different fields, so the skill spells out the split.
  `preferred_language` remains `de` / `en` only — it is the app/UI locale alluvo renders in, not
  a spoken-language fact — and any other code is rejected on the `manage-model` preview. A third
  language the person merely speaks is reported, not written, and handed to
  `onboard-new-employee` as a ContactLanguage (`0-185`).
- No skill referenced the retired `EmployeeLanguage` type (`0-172` / `employee-languages`), so
  its removal from the MCP surface needed no prompt change.

### Added — 2026-07-29 Exclusive (non-cumulative) surcharges now change billing and contract text (alluvo#2639)
- **manage-contract-lifecycle** (new "Zuschläge: kumulativ vs. exklusiv" block in step 1):
  `is_exclusive` is now actually persisted and consumed. An exclusive surcharge is not
  stacked — of several exclusive rows applying to the same hour only the one with the highest
  effective rate is billed, with every non-exclusive row charged on top. The same flag now
  derives the §12.2 AÜV / Anlage 2 cumulation sentence (all exclusive → "nur der höchste
  Satz, keine Kumulierung"; mixed → the exclusive rows are asterisked and the note explains
  the marker; none → the classic "kumulativ" wording), so it changes the signed document, not
  just the invoice. Documents the reliable path: set it on the Rahmenvertrag role via
  `add_role`/`update_role` (`is_exclusive` / `applies_on_holidays` per surcharge row, or
  `surcharges_all_exclusive: true` to force it on every row of the role — the "Zuschläge
  nicht kumulativ" case), and let the AÜV inherit it at seeding time.
- **Known gap, documented rather than papered over:** `manage-assignment-contract`
  `sync_surcharges` drops both flags before the write and `list_surcharges` does not display
  them, so exclusivity on an individual AÜV is neither settable nor readable over MCP. The
  skill now says so, notes that existing rows keep their stored value across a sync, and
  points the operator at the contract wizard's Zuschläge editor instead of promising an MCP
  fix. Filed as alluvo#2640.

### Added — 2026-07-29 A local scan can reach the Personalakte via the temp vault (alluvo#2655)
- **clean-inbox** (new subsection in step 3, after the attachment-filing list): filing a document
  that never came through alluvo is no longer a dead end. `manage-temp-vault` now accepts **PDF**
  alongside JPEG/PNG/WebP (up to 30 MB), so the documented route for a file on the operator's own
  machine is: `create` a plain vault (no `slots`) → hand the operator the returned browser upload
  link so **they** upload it → `get` the file's public URL → pass it verbatim as `file_url` on
  `manage-employee-document` `action: "create"` → `delete` the vault once the document shows the
  copied file. Spells out why `file_base64` is not the answer for a real scan (a 4 MB PDF is
  ~5.5 MB of base64 through the conversation) and keeps the transit-not-storage rule explicit —
  an AU-Bescheinigung or ID scan must not idle out its TTL on a world-readable URL.
- **record-absence** (step 7): the same route in short form, cross-linked to `clean-inbox`.
  `from_attachment_id` stays the preferred path whenever the file already sits on a ticket or
  Email; the vault covers only the case where nothing in alluvo holds the bytes.
- Both skills now say to read the vault's public URL **back from the tool** rather than
  constructing it: vault storage follows the app's configured public disk (`s3_public` in
  production), so the old `/storage/tenant{id}/…` shape no longer holds.
- No skill uses target-bound vault **slots**, so the change that makes a slotted upload a *move*
  (transit copy deleted on auto-attach → `public_url: null` + `transit_purged: true`, use
  `media_url`) needed no prompt change. Plain, slot-less uploads — the only kind the skills use —
  keep their copy and their public URL.

### Added — 2026-07-29 Employee merge preflight unblocks Contact merges (alluvo#2619)
- **merge-duplicate-companies** (new subsection after step 3a): a Contact merge where both
  sides carry a linked Employee is no longer a dead end. `preview-merge`/`merge` return an
  `# Employee Merge Preflight` work plan instead of the normal preview — employee-level
  columns that would move, relations that would re-point (salaries, employment periods,
  tasks, assignment contracts, staffing experiences, licenses), unique-constraint collisions
  such as `employee_number`, and open decisions (a column both records set differently,
  overlapping EmploymentPeriod rows) that are surfaced but never auto-resolved. Documents the
  sequence: read the plan → resolve the open decisions by hand → `merge_employee` record
  action on the kept Employee (`0-2`, `data.source_employee_id`) → re-run the Contact merge.
  Notes that the action refuses while a decision is open, needs delete rights on the
  duplicate, and requires both the tool's `confirmed: true` and `data.confirmed: true` to
  write — and that `manage-record-action` `confirmed: false` only echoes the payload without
  running the action, so the plan only ever comes from `manage-duplicates preview-merge`.
- **triage-data-quality** (step 5): a `duplicate_employee` issue now has an MCP path instead
  of a pointer to the dashboard — worked through the two Contacts via the preflight.

### Changed — 2026-07-29 `manage-duplicates` reports discarded values and refuses conflicting merges (alluvo#2608)
- **merge-duplicate-companies**: `preview-merge` and `merge` now render a
  **"Values that will not survive this merge"** block, and a `merge` that would drop a
  differing value on a carried column is **refused** unless `confirm_data_loss: true` is
  passed. Step 3a documents the loss report and both reasons — `conflict` (both records hold
  a differing value; **blocks**) and `not_carried` (a policy-excluded column such as
  provenance held a value; reported only, never blocks, and a differing `record_source` is
  the normal case). Step 3c treats the refusal as the expected gate rather than an error and
  spells out the follow-up: read the loss block → copy what matters onto the `keep_id` record
  with `manage-model` → re-run with `confirm_data_loss: true`, only after the operator has
  seen the block and agreed. Also notes that a merge now carries the whole table minus a small
  technical/policy set, so columns that used to vanish silently (address formality, preferred
  language, consent flags, availability profile) survive.
- **merge-duplicate-companies**: corrected the Company-only merge parameter to
  `keep_einsatzbetriebe` — `client_sites_strategy` does not exist in the tool schema.
- **triage-data-quality** (step 5): the duplicate hand-off now warns that `merge` can be
  refused on a `conflict` and names the resolution, so a routed `duplicate_contact` issue
  does not dead-end on the refusal.

### Changed — 2026-07-29 `0-102` writes are no longer blocked — routing is now discipline (alluvo#2591)
- **intake-personalbedarf**, **head-of-disposition**: both skills stated that `manage-model`
  create/update on `StaffingRequirement` (`0-102`) is rejected ("cannot be created or updated").
  That is no longer true — the type is registered as MCP-manageable again, and the guard that
  used to reject the call now lets it through. `StaffingDemand` (`0-415`) remains the only
  target for **new** demand, but nothing enforces that anymore: a misrouted create silently
  files a legacy record that appears in no `0-415` view or count, and starts the old
  contact-matching pipeline instead of the demand matcher. Both skills now say so, and both
  keep the "never offer `0-102` as a fallback when a `0-415` write fails" rule. Correcting an
  *existing* legacy `0-102` record via `action: "update"` is called out as legitimate — with
  operator confirmation that they mean the historic record, not a new Bedarf.
- The api side is contradictory as of this writing: the MCP server instructions the agent reads
  at runtime still describe `0-102` as read-only. Filed as alluvo#2611; these skills document
  the behavior the code actually has and will be revisited once that is resolved.
### Changed — 2026-07-29 Duplicate warnings now cover bulk creates and name-only matches (alluvo#2616)
- **triage-data-quality** (step 3, `create_related`): `bulk-manage-model` no longer writes
  people without a duplicate check — a create batch appends one aggregated
  `⚠️ **POSSIBLE DUPLICATES**` summary ("N of M created record(s) look like they might
  already exist") naming each flagged row by its `[index]` with its candidates underneath.
  Same warning-never-a-rejection contract as the single-record block: every row was created,
  so work the flagged indexes, never re-run the batch. Removed the now-wrong advice to create
  people one at a time to get the check.
- **triage-data-quality** (step 3): an Employee/Candidate create *without* `contact_id` now
  also warns when the identity resolver found **no** match but existing Contacts share the
  same folded full name — previously the block only appeared on 2+ name **and** date-of-birth
  candidates, so a create without a date of birth silently missed look-alikes. Auto-linking
  still requires a date of birth; a bare name match warns only.
- **merge-duplicate-companies** (step 1): the hand-off note covers both entry points — the
  single `POSSIBLE DUPLICATE` block and the aggregated `POSSIBLE DUPLICATES` batch summary —
  and flags a name-only match as a weak signal to read both records before merging.

### Added — 2026-07-29 StaffingRole group filter is numeric, `is_null` now answerable (alluvo#2580)
- **triage-data-quality** (Rollenkatalog section 3c): `staffing_role_group_id` on `StaffingRole`
  (`0-100`) is advertised by `get-model-schema` (context `list`) as a **number** field, not a
  relationship — `eq` / `neq` / `gt` / `gte` / `lt` / `lte` / `between` / `is_null` /
  `is_not_null`. "Which roles have no Gruppe yet?" — the entry point of the whole catalog pass —
  is expressible over MCP for the first time; the skill now spells out the `is_null` query
  instead of pointing at the `level` example. Also recorded that there is no `in` (one Gruppe is
  `eq <id>`, several means one query each), and that an operator the field does not carry is not
  applied but reported in the response's `skipped_conditions` — a silently wider result set, not
  an error.

### Changed — 2026-07-28 § 4 ArbZG break is derived from Arbeitszeit, not the gross span (alluvo#2546)
- **build-dienstplan**: documented the statutory break auto-fill that every write path
  (`create`, `add-shift`, `update-shift`) applies — `break_minutes` is raised to the § 4 ArbZG
  minimum, so a Schicht can never persist below it. The minimum is derived from the resulting
  **Arbeitszeit** (§ 2 Abs. 1 defines it *without* the Ruhepausen), not from the raw start–end
  span: 0 min up to a 6h00 span, 30 min over 6h00 up to 9h30, 45 min beyond. A 19:10–04:40
  Schicht (9h30 span) therefore carries 30 minutes and exactly 9,0 h Arbeitszeit — the skill now
  says not to "correct" that to 45, which would shave 15 minutes of paid time with no statutory
  basis. Also recorded the two asymmetries: a break the operator set above the minimum is only
  ever raised, never trimmed, while a break that exactly matched the old minimum follows a time
  change in both directions.
- **approve-stundenfreigabe**: noted that a planned Schicht's hours are net of that break, with
  the same bands, so a 15-minute gap on a 9h–9h30 Schicht is not flagged as a deviation.

### Added — 2026-07-28 Reimbursement Freigeber authorization + clarification actions (alluvo#2575)
- **approve-stundenfreigabe** (reimbursement section): three record actions on `Reimbursement`
  (`0-20`) are now reachable over MCP via `manage-record-action` and are documented —
  `confirm_authorization`, `decline_authorization` (requires a `reason`) and
  `resolve_clarification` (optional `note`). Recorded as the two gates that make an otherwise
  valid `approve` fail: a `needs_clarification` flag, and a named Freigeber
  (`authorized_by_id`) whose `authorization_status` is not yet `confirmed`. Both are readable
  and filterable on `query-model` (`needs_clarification`, `authorization_status`:
  `pending` / `confirmed` / `declined`), so the skill checks them before promising an approval.
- **approve-stundenfreigabe**: recorded the permission boundary and the side effects that
  change what an operator sees. `confirm_authorization` / `decline_authorization` are gated to
  the named Freigeber themselves or a tenant admin on a `submitted` record — a Disponent
  cannot confirm on someone else's behalf and must route it to that person. Confirming is what
  hands the reimbursement to the owner's approval queue (notification + approval task), which
  is why one awaiting authorization is deliberately absent from that queue rather than lost.
  Declining is **not** a rejection: it moves the record to `needs_revision` for the employee to
  correct and resubmit. `resolve_clarification` only unblocks — it never approves — and its
  `note` replaces any prior `review_note`. Also noted `mark_as_paid`'s optional
  `payout_method` / `bank_account_id`, and added the German triggers ("Freigeber bestätigen",
  "Autorisierung ablehnen", "Rückfrage klären").

### Added — 2026-07-28 POSSIBLE DUPLICATE warning on person creates + umlaut-folded search (alluvo#2562)
- **triage-data-quality** (step 3 `create_related`): a `manage-model` `create` of a Contact
  (`0-105`), Employee (`0-2`) or Candidate (`0-81`) can now answer with a
  `⚠️ **POSSIBLE DUPLICATE**` block listing up to 5 look-alike records (id · name · email ·
  created date). Recorded as what it is — a **warning, never a rejection**: the record was
  created, so the skill must not retry the call or report a failure, and must show the
  candidates to the operator instead. The two paths differ and the skill says so: a direct
  Contact create matches on exact email, on phone/mobile digits, or on a full name folded
  across German umlauts ("Göbel" = "Goebel"); an Employee/Candidate create *without*
  `contact_id` warns only when the identity resolver found 2+ Contacts sharing a name **and**
  a date of birth and deliberately refused to auto-link one. An explicit `contact_id` reuses
  that Contact and never warns; an `update` never warns. Also recorded: only `manage-model`
  renders the block — `bulk-manage-model` writes the same records without it, so people
  should be created one at a time when the check is wanted.
- **merge-duplicate-companies**, **triage-data-quality** (step 5), **using-alluvo-operator**:
  corrected the merge surface. Company (`0-3`) and Contact (`0-105`) are the *only* mergeable
  model types and **both** work over MCP through `manage-duplicates`
  (`find` → `preview-merge` → `merge`) — triage-data-quality previously sent every
  `duplicate_contact` issue to the Data Quality Dashboard as though no MCP path existed. The
  merge skill now states its Contact coverage (everything applies unchanged except
  `client_sites_strategy`, which is Company-only and ignored for Contact merges; the
  parent-grouping step stays company-only) and names the POSSIBLE DUPLICATE block as one way
  an operator arrives there. Its `description` gained the German contact-Dublette triggers.
- **merge-duplicate-companies** (step 1, Option B): `search-model` now folds German umlauts
  and diacritics on both the indexed and the query side (`ö`=`oe`, `ü`=`ue`, `ä`=`ae`,
  `ß`=`ss`, plus generic accent stripping), so a spelling variant is no longer a reason a
  Dublette stays hidden during a targeted search. Flagged as folding, not fuzzy matching — a
  typo, an abbreviation or a differing legal form still needs its own query.

### Added — 2026-07-28 File an existing ticket/email attachment into a personnel record (alluvo#2567)
- **clean-inbox** (step 3), **record-absence** (new step 7): `manage-employee-document`
  (`create` / `update` / `attach_file`) gained `from_attachment_id` plus
  `from_attachment_source` (`ticket`, the default, or `email`) — the numeric id from a
  `manage-ticket` `action: "get"` 📎 line, or an Email attachment id. The bytes are copied
  server-side, so a Nachweis an employee mailed in (Impfausweis, AU-Bescheinigung, signed
  form) is now filed straight into their document record. This is the **only** working path
  for a file already in alluvo: a ticket attachment has no publicly fetchable URL for
  `file_url`, and `get-attachment` returns an image for viewing rather than as a base64
  string you could hand to `file_base64` — until now the skills could only describe a manual
  download-and-re-upload that did not exist over MCP.
- The three file sources are mutually exclusive; naming more than one now errors with
  "Provide only one of from_attachment_id, file_url, or file_base64 — not several."
- Guardrails recorded with it: resolve the ticket's Contact to the Employee before filing
  (never a guessed person), read `type_code` from `action: "list-types"` (tenant-specific),
  preview without `confirmed` then confirm, and note that access is gated by the parent
  ticket's inbox membership / the Email view policy — the same rule `get-attachment` uses,
  so an attachment you can read is one you can file and no other. clean-inbox's "never
  fabricate operational data" rule is explicitly *not* loosened: filing stores the artifact
  the sender supplied, it does not derive an absence, Schicht or reimbursement from it, and
  a blurred or ambiguous document stays a task.

### Added — 2026-07-28 Rollen-Hierarchie (#NachUntenGehtImmer) and the Rollenkatalog cleanup job (alluvo#2556)
- **match-bench-to-clients**, **intake-personalbedarf**: matching scores a role by hierarchy,
  not by label equality, and the skills now say so. Exact role `1.0`; same
  `staffing_role_group_id` with the employee's `level` at or above the demanded level `0.8`
  (valid downward substitution); same group but lower `0.0`; a different group or no group
  `0.0`; same group with either side's `level` unseeded `0.6` (symmetric fallback). Where a
  demand names several roles of one group, the **lowest** of their levels is the bar — a
  stricter role never excludes someone who satisfies a looser one. So a higher-qualified
  candidate is no longer dropped for not matching the role label exactly, and a `0.6` is read
  as an unclassified catalog rather than a mediocre fit. Also recorded: `resolve-staffing-role`
  returns neither Gruppe nor `level` — read those off `0-100`.
- **triage-data-quality** (new step 3c): `StaffingRole` (`0-100`) gained `level` and
  `staffing_role_group_id` as **writable** params (`manage-model` / `bulk-manage-model`
  previously dropped both silently into `ignored_fields`) and as **filterable**, `hiddenByDefault`
  columns — so "which roles are still unclassified" is answerable for the first time via
  `search-model` with `is_null`. `StaffingRoleGroup` (`0-345`) is now readable *and* writable
  over MCP, so a missing Gruppe can be created in place. No detector flags unclassified roles,
  hence the explicit step. Guardrails carried over: set Gruppe and `level` together, check the
  preview's `IGNORED FIELDS`, read the roles back, never guess a fachliche Rangfolge, and
  confirm before moving an already-classified role to another Gruppe.
- **using-alluvo-operator**: routes "Rollenkatalog / Rollen-Hierarchie pflegen" to
  `triage-data-quality`.
- New MCP prompt `manage-staffing-role-hierarchy-prompt` (optional `group` /
  `staffing_role_id`) referenced from the three skills for the full procedure.

### Changed — 2026-07-28 StaffingDemandMatch (`0-416`) is directly readable; StaffingRequirement (`0-102`) lost its write path (alluvo#2528)
- **head-of-disposition**, **match-bench-to-clients**: `StaffingDemandMatch` (`0-416`) is now
  readable through the generic tools on its own — `search-model` / `query-model` / `get-model`
  no longer need a parent StaffingDemand id, so cross-demand questions ("every offered match
  with `score` > 80", "is this bench employee already proposed anywhere") are one call instead
  of an include per demand. `employee_id` is exposed and filterable directly, alongside `score`,
  `outcome` (`offered` / `accepted` / `declined`) and the `employee` / `staffingDemand`
  relationship filters. Still **read-only**: `manage-model` writes are rejected and
  `mark_offered` / `accept` / `decline` stay on `manage-record-action`. Reading it needs the
  `staffing_demand_matches.view` permission.
- **intake-personalbedarf**, **head-of-disposition**: `StaffingRequirement` (`0-102`) lost its
  `manage-model` write path — create/update is now rejected outright, where the skills
  previously framed "never create demand there" as a convention. Reading `0-102` is unchanged
  and still expected for historical records and existing outreach/proposal business;
  `StaffingDemand` (`0-415`) is the only create/update target for new demand.
- No change to `StaffingRequirementContactMatch` (`0-404`) or `find-matches-prompt`: `0-404`
  scores unhired **Candidates** against a StaffingRequirement (sales/outreach), while `0-416`
  scores already-employed **Employees** for a StaffingDemand (placement/bench). Two live
  capabilities, not a migration — the matching-directions table keeps its `0-404` row.

### Changed — 2026-07-28 automation-agent `output_schema` documents `of`, and the run-time gap behind it (alluvo#2515)
- Four MCP tools (`manage-assignment-contract`, `manage-workflow`, `manage-automation-agent`,
  `manage-inbox-forwarding-targets`) were building array-of-object fields with
  `array($schema->object(...))` instead of `array()->items(...)`, so those fields reached the
  model as a bare `"array"` with no item shape. Fixed api-side — nested `required` fields on
  `work_tasks`, `shifts`, `provisional_shifts`, `conditions`, `actions`, `output_schema` and
  `targets` are now genuinely advertised. No skill hand-documented a workaround for the old
  under-specified schema, so nothing had to be unwound: **build-dienstplan**'s `shift_type` rule
  and **clean-inbox**'s `targets: [{email, label}]` shape were both already accurate and match
  what the schema now declares.
- **build-automation-agent**: the `output_schema` item shape now lists **`of`** — the nested
  `output_schema` describing one item of a `type: "array"` field — which the skill previously
  omitted while recommending structured array fields as the preferred output.
- **build-automation-agent**: documents the current run-time gap behind `of`. The agent runner
  still builds its structured-output schema through the unfixed code path, so `of` is validated
  and stored but not handed to the model — the item keys must also be named in the German
  `instructions`, and confirmed in the `test` output before a `{{key.field | table}}` placeholder
  is wired into a mail template. Tracked api-side as alluvo#2520; set `of` anyway.

### Added — 2026-07-28 Inbox (`0-301`) is MCP-reachable; Geschäftszeiten are settable (alluvo#2508)
- The **Inbox** record itself moved from "no MCP surface" to fully reachable through the
  generic tools — `get-model-schema`, `get-model`, `search-model`, `query-model` and
  `manage-model` all accept `0-301`. `InboxChannel` (`0-302`) and `InboxMember` (`0-303`)
  deliberately stayed out: channels and memberships are still not readable or writable via MCP.
- **clean-inbox** gained a `## Inbox settings: Geschäftszeiten (business hours)` section, next
  to the existing Weiterleitungsziele one. `business_hours` is a map keyed by **lowercase
  English weekday** (`monday`…`sunday`) with `start`/`end` as `H:i` strings; a weekday absent
  from the map is closed (there is no "closed" flag, and a day carrying only one bound is
  rejected, not read as closed), German keys like `montag` error out, the update **replaces the
  whole map** (read it with `get-model` first), and it needs `inboxes.edit` — `inboxes.view`
  alone is refused cleanly with nothing saved. Two-stage preview → `confirmed: true` as always.
- **clean-inbox**: the Vapi caveat is now explicit. The phone assistant's prompt is composed
  **at sync time**, so changed Geschäftszeiten do not reach the live assistant until it is
  re-synced and there is no MCP path to trigger that — the skill must tell the operator the
  value is saved and correct for Terminbuchung immediately while the assistant keeps
  announcing the old hours, and must never claim the caller-facing text changed.
- **clean-inbox**: the hours are also the fallback bookable window behind
  `get-booking-availability` (per-user setting → inbox `business_hours` → system default). The
  skill deliberately does **not** promise any SLA effect: the inbox SLA policy's
  `business_hours_only` mode reads the same map, but ticket due dates are not computed on
  ingestion today (`calculateDeadlines()` has no production caller — filed as alluvo#2514).
- **clean-inbox / using-alluvo-operator**: triggers and routing now cover the settings side of
  the inbox ("Geschäftszeiten der Inbox ändern", "Öffnungszeiten setzen", "set the inbox
  business hours"), not only ticket triage.

### Fixed — 2026-07-28 `get-employee-profile` is gone; one role-aware `get-profile` replaces it (alluvo#2511)
- **bench-check, match-bench-to-clients, onboard-new-employee, profilvertrieb,
  prospect-companies**: `get-employee-profile` no longer exists. The tool was renamed to
  **`get-profile`** and moved to the Contacts domain; it takes `model_type` (`0-2` Employee /
  `0-81` Candidate / `0-105` Contact) + `model_id` instead of a bare `employee_id`. All five
  skills now call it with the explicit pair — a call with `employee_id` fails.
- **get-profile is contact-rooted**: it resolves the identity Contact whichever role you pass
  and always returns the shared CV data (education, work experience, languages, licenses,
  staffing experiences/trainings, availability preferences, home location), plus the
  role-specific section for the `model_type` — the Employee staffing profile as before, or a
  Candidate pipeline view. The Employee section's "Staffing Opportunities" list is unchanged:
  still ranked score-first (nulls last) then by distance, with `specialty_fit: conflict`
  pre-excluded server-side.
- **onboard-new-employee**: dropped the note that `get-employee-completeness` still works as a
  deprecated alias — that shim was removed along with `get-employee-profile-url` and
  `get-candidate-profile-url`. Use `get-profile-completeness` and `get-profile-url`; the
  removed names now error.
### Fixed — 2026-07-28 a day with a planned shift can no longer be kept open on signature (alluvo#2456)
- **manage-contract-lifecycle**: `send_for_signoff`'s `keep_open_availability_day_ids` no
  longer protects every id passed. Any day this contract already plans a non-cancelled shift
  on for that employee is **dropped server-side** and books on signature — the day is worked,
  so holding it open would leave the employee bookable by other customers while deployed.
- **manage-contract-lifecycle**: the drop is silent — the `confirmed: false` preview still
  echoes the ids as passed. The skill now tells the assistant to check the contract's
  Dienstplan first and never promise the operator a hold on a shift day.
### Fixed — 2026-07-28 started Schichten are locked, and approved-Dienstplan changes notify the employee (alluvo#2458)
- **build-dienstplan**: `update-shift` and `remove-shift` now hard-block any Schicht whose
  **start time has already passed** — same class as the ArbZG ceilings, no `confirmed`, no
  permission, no reason gets past it. The skill states the exact error, notes that the
  boundary is the start time (not the date, so a Schicht later today is still editable), and
  routes corrections for running/finished Schichten to time tracking instead of the plan.
- **build-dienstplan**: new step 6a documents the employee-facing shift-change digest. On a
  Dienstplan-Periode that has left draft (`published` / `locked` / `pending_approval`), a
  time-relevant change (`date`, start, end, break), a cancellation or a deletion sends the
  employee a debounced ~15-minute digest (AÜG § 11 Abs. 2 Satz 4) — in-app/push/mail for
  employees with a portal user, mail to the Kontakt address otherwise. Skills must not
  promise "silent" edits on an approved plan: there is no suppression flag. Corrections
  should be batched (one digest per window) — drafts stay silent, and `notes`/`billing_rate`
  changes never reach the employee.
- **build-dienstplan**: step 7 now separates the two § 11 duties — the customer-facing
  Einsatzmitteilung is the operator's decision, the employee digest is automatic.
- **build-dienstplan**: the generic-tools warning now also covers `manage-record-action`.
  Shift (`0-111`) is not on the MCP model-type allowlist, so the `cancel_shift` record action
  visible on a Schicht inside alluvo is **not** reachable over MCP; cancel through
  `remove-shift` with `cancel: true`, which is the same operation (stamps `cancelled_at`,
  keeps the row) and runs both guards above.
- **record-absence**: step 7 now warns that a Krankmeldung does not retro-remove a Schicht
  that already started, and that cancelling on an approved Dienstplan notifies the employee —
  announce it and cancel in one call rather than a series.
- **manage-contract-lifecycle**: the Einsatz shift-planning notes now state that only the
  Schichten still ahead can be moved on a running Einsatz, and that post-approval re-timing
  triggers the employee digest.

### Fixed — 2026-07-28 saving an ICP now works: `sector_id` + `company_segments` are required (alluvo#2509)
- **define-icp**: the save step could never succeed. `company_segments` is `required` (min 1)
  on IdealCustomerProfile (`0-270`) create but is a relation, not an attribute — sending it
  crashed the write and rolling it back, omitting it failed validation. `manage-model` now
  syncs the relation, so the skill documents the real create contract: `name` (unique),
  `sector_id` (Sector `0-70`) and `company_segments` (flat array of CompanySegment `0-198`
  ids) are **required**; the array fields (`job_titles`, `industry`, `location`,
  `company_size`, `revenue`, `age_range`) and free text (`interests`, `pain_points`,
  `other`) are optional.
- **define-icp**: new step 4 resolves the sector and segments via `query-model` on `0-70` /
  `0-198` **before** the preview — an id that doesn't exist fails the whole write — and the
  preview now shows them by name rather than as bare ids. Steps 4/5 renumbered to 5/6.
- **define-icp**: on update, `company_segments` is a **full replace** (omit to leave
  unchanged, `[]` to clear); sending only the segment being added silently drops the rest.
- **define-icp**: the catch-all for anything the schema doesn't cover is the `other` field —
  the skill previously pointed at a "description/notes field" that does not exist on `0-270`.
- No skill referenced the other surfaces in this change, so nothing changed for them: the
  `entities` array now accepted by `manage-model` on Note (`0-200`) / Call (`0-202`) — every
  skill logs activities through `manage-activity`, which is the gated path and already
  auto-links the contact's company — and four fields that were advertised but never
  persistable and are now cleanly rejected (`Job` `hero_image_url` /
  `testimonial_avatar_url`, `Candidate` `location`, `EmployeeWorkExperience` `is_current`).
  `bench-check` already documented that a Candidate has no writable `location`; the home
  address goes on the linked Contact via `manage-location`.

### Fixed — 2026-07-27 grouped aggregates work on Employee/Candidate; `group_by` is `query-model`-only (alluvo#2504)
- `query-model` with `aggregate` + `group_by` no longer fails on **Employee (`0-2`)** and
  **Candidate (`0-81`)** — the grouped-aggregate query used to hydrate models without the
  identity FK and blew up on their default `contact` eager load. Both types are now groupable
  like any other.
- **Corrected a wrong tool reference while verifying this surface:** `head-of-disposition` and
  `head-of-sales` both told operators to pass `group_by` to **`count-model`**. That parameter
  does not exist there — `count-model` accepts only `model_type`, `filter_groups` and `search`
  and returns a single total. Grouping lives on `query-model` (`aggregate: {function: …}` plus
  a top-level `group_by`). Both skills now name the right tool, and state that an aggregate
  call returns aggregate rows *instead of* the row list, is mutually exclusive with `include`,
  and is capped at the **top 200 groups**.
- **head-of-disposition**: the expiring-assignments breakdown (`0-31`) is now an explicit
  *second* call rather than an extra parameter on the row query; the Stundenfreigabe backlog
  prefers one grouped call over a `count-model` loop; and step 1a gained a workforce-structure
  note — a grouped count on `0-2`/`0-81` gives the headcount distribution (per position, home
  location, `owner_id`) but **knows nothing about coverage**, so `get-employee-availability`
  remains the only source for who is verleihfrei.
- No skill referenced the other two surfaces in this batch, so nothing changed for them:
  the newly filterable `whatsapp_opt_in_at` / `whatsapp_opt_out_at` / `whatsapp_undeliverable_at`
  consent fields on `Contact` (`0-105`), and the new 20-item cap on action response payloads
  relayed by `manage-record-action` — the only action carrying such a payload is
  `preview_audience` on `WhatsappCampaign` (`0-411`), which no skill covers.

### Added — 2026-07-27 `get-field-history` tool + `vacation-balance` action (alluvo#2473)
- The MCP server gained `get-field-history` (101 → 102 tools): read-only field-level audit
  history for any record — `model_type` + `record_id`, optional `field` to scope to one
  attribute and `limit` (1–50, default 20 events, newest first). Returns old → new per change
  with the actor: a named user, a machine source labelled `(system)` (import, mcp, api,
  agent, …), or `⚠️ UNATTRIBUTED` when the write has neither. This closes a structural gap —
  `get-timeline` returns activities only and never shows a plain attribute change.
- **record-absence**: new step 4 — read the Urlaub balance before booking vacation, via
  `get-employee-availability` `action: "vacation-balance"` (`employee_id` required, `year`
  optional, defaults to the current year in the tenant timezone). Documents `entitlement` /
  `tariff_entitlement` / `approved` / `pending` / `remaining`, and the three ways to misread
  it: `remaining` does **not** subtract `pending`; `null` means unknown, never 0 or a deficit;
  days are working days minus public holidays, not the calendar span. Booking Urlaub that
  exceeds `remaining` now requires operator confirmation instead of going through silently.
  The skill previously booked vacation blind — an operator could enter 30 days when 6 remained.
- **triage-data-quality**: new step 3b — use `get-field-history` to tell a deliberate edit from
  an import artifact before overwriting a suspicious value, and flag `⚠️ UNATTRIBUTED` writes as
  unverified rather than as reviewed.
- **account-research**: the timeline section now states that `get-timeline` is not a change log,
  and points at `get-field-history` for "who set this field and when".
- **merge-duplicate-companies**: when two candidates disagree on a field, check its audit trail —
  a value a colleague maintained outranks one an import baked in; that now feeds the `keep_id`
  choice.
- **head-of-sales**: `stage` and `status` on `AssignmentContract` (`0-31`) are now filterable in
  `filter_groups`, so a stage cut is one server-side query instead of paging the table. `stage`
  remains **not writable** through the generic tools — it moves only via
  `manage-assignment-contract` `action: "transition"`.
- No skill referenced the other newly filterable surface (`WhatsappCampaignRecipient`, `0-414`),
  so nothing changed there.

### Added — 2026-07-27 Vorüberlassung (PriorPlacement `0-406`) is MCP-manageable (alluvo#2464)
- `PriorPlacement` (`0-406`, Vorüberlassung — Überlassungszeiten an employee served at the same
  Entleiher outside alluvo, e.g. through another Verleiher) moved from calendar-read-only to
  fully MCP-managed: it is now in `availableForMcp()` and `mcpManagedTypes()`, so
  `manage-model` / `search-model` / `get-model` / `get-model-schema` all work on it.
  Create requires `employee_id`, `company_id`, `starts_on`, `ends_on`; `source` and `notes`
  are optional.
- **`manage-contract-lifecycle`** gained a `## Vorüberlassung` section: how to record and read
  prior placements (two-stage as always), and how they change the AÜG threshold check — system
  assignments and PriorPlacement rows merge into one run **per Entleiher**, Equal Pay
  (§ 8 Abs. 4) triggers at 9 accumulated months, Überlassungshöchstdauer (§ 1 Abs. 1b) at 18,
  and an interruption of more than 3 months resets the accumulation. Recording a
  Vorüberlassung can therefore pull both trigger dates forward. Explicit guardrail: never
  delete or shorten one to silence a warning. The Verlängerung checklist now points at it —
  an extension is where the 18-month limit bites first.
- **`head-of-disposition`** — the Überlassungshöchstdauer bullet now states that the clock
  counts Vorüberlassungen too, and that "no warning" only means "no warning for what is on
  file"; if an employee plausibly worked at the client before, hand off to
  `manage-contract-lifecycle` to get it on record instead of reporting them as clear.

### Changed — 2026-07-27 11 deprecated MCP alias tools removed (alluvo#2460)
- The one-release deprecation window for 11 alias tools is over — they are no longer
  registered on the alluvo MCP server (v1.3.0, 112 → 101 tools) and a call now fails with
  "Tool not found": `manage-call` / `manage-meeting` / `manage-note` (→ `manage-activity`
  with `activity_type`), `manage-contact-avatar` / `manage-job-media` (→ `manage-media`),
  `manage-candidate-profile-link` (→ `get-profile-url`), `manage-checklist-run` /
  `manage-checklist-step` / `manage-checklist-template` (→ `manage-checklist-execution` /
  `manage-checklist-authoring`), `manage-meta-bulk-operations` / `manage-meta-targeting`
  (→ `manage-meta-campaign` / `manage-meta-audiences`).
- **manage-meta-ads**: the consolidation note no longer claims the old tool names "still
  resolve as deprecated aliases for one release" — they are removed. Action names are
  unchanged, so only the tool name has to be swapped.
- No other skill still named a removed tool; the earlier syncs (alluvo#2239, #2399) had
  already migrated them to the consolidated tools.
- **build-dienstplan**: new note that Shift **and** DepartmentShift (`0-182`, the recurring
  shift-code definitions behind `department_shift_id`) are blocked on the generic model
  tools — the error now names `manage-shift-plan` explicitly, and the ArbZG/availability
  checks only run there.

### Changed — 2026-07-27 Dienstplan ships as its own attached PDF on the AÜV (alluvo#2428)
- The concrete shift schedule was pulled **out** of the legally-numbered AÜV clauses: the
  contract text now carries only the aggregate figures (Zeitraum, Stundenregelung, or
  "Geplante Arbeitszeit laut Dienstplan"), and the bundle instead gets **one** branded
  "Dienstplan" PDF per Einsatzvertrag with a section per Einsatz.
- **manage-contract-lifecycle**: `attach_shift_plan_document` (boolean, defaults `true`) added
  to the per-Einsatz field list and to the `manage_einsatz` guidance — it decides whether an
  Einsatz appears in that PDF. Documents that `false` means the schedule reaches the customer
  in **no** document (there is no path back to the old contract-text rendering), that a
  contract where no live Einsatz is flagged simply ships without a Dienstplan PDF rather than
  an empty one, and that the PDF is regenerated with the documents (send for signoff /
  re-render / signing) — not on every shift edit.
- **build-dienstplan**: new note that the planned Schichten become a customer-facing document
  — finish the plan before the AÜV goes out for signature, and change
  `attach_shift_plan_document` via `manage-contract-lifecycle`, not from this skill.

### Changed — 2026-07-27 Batch task creation via `bulk-manage-model` (alluvo#2399)
- `manage-model` / `bulk-manage-model` now accept a polymorphic `attachments` field
  (`[{type_id, id}, …]`) on models that support it — `Task` (`0-5`) is the first. Before,
  `attachments` was rejected outright, so there was no bulk path for tasks and no way to
  link one task to more than one record. Skills that wrote tasks in a loop now write them
  in one call.
- **call-summary**: step 4 rewritten to create all Action Items in a single
  `bulk-manage-model` call (`model_type: "0-5"`, one `operations` entry each, max 50),
  attaching each task to the Contact **and** the Company at once. Documents that
  `due_at`/`reminded_at`/`wait_until` on this path need an ISO datetime **with an explicit
  offset** (`…+02:00` / `…Z`) — `manage-task`'s tenant-local `Y-m-d H:i` is rejected — and
  keeps `manage-task` for repeating follow-ups and ticket-bound tasks.
- **head-of-disposition**: coordination round writes its Disponenten tasks in one
  `bulk-manage-model` call with `owner_id` per entry and `attachments` pointing at every
  record a task concerns (`0-2`, `0-3`, `0-110`, `0-31`, `0-190`). Two-stage gate restated
  to cover both tools. Notes that attachments are **additive on update** (listing them adds
  links, never detaches) and that no MCP path detaches a task attachment today.
- **match-bench-to-clients**: step 6 batches the per-Einsatzvertrag review tasks into one
  call, each attached to Employee + Company + AssignmentContract.
- **onboard-new-employee**: step 4 batches the prospecting tasks, each attached to the
  Employee and the target Company.
- **clean-inbox**: stays on `manage-task` by default — `ticket_id` is `manage-task`-only
  and additionally cascades the ticket's primary Contact/Company onto the task, and
  `bulk-manage-model` has no `confirm_token`, so confirming resends every long task body.
  Documents when the bulk path is the better trade (many short, similar tasks).

### Changed — 2026-07-27 Contracts get their own activity timeline (alluvo#2239)
- **manage-contract-lifecycle**: new **Contract timeline** section — `manage-activity`
  `action: "create"` now accepts `subject_type: "0-30"` (Rahmenvertrag) and `"0-31"`
  (Einsatzvertrag/AÜV) for `note` / `call` / `meeting`, so a decision or memo about a
  contract is logged **on the contract** instead of parked on the client's Company record;
  `get-timeline` reads it back with the same subject. Documents the three behaviors that
  bite: a contract activity does **not** auto-link to the Company (it never shows on that
  company's timeline), logging stays available after the contract leaves `draft` (gated on
  the per-record log-activity permission, not field-editability, so it works on a `won`
  contract), and contract subjects return no follow-up suggestions.
- **call-summary**: subject list at step 3 extended to `0-30` / `0-31` with guidance on
  picking the subject by what the conversation was about (person → `0-105`, account news →
  `0-3`, one specific contract → the contract), plus the no-roll-up and no-follow-up-
  suggestions caveats. Prerequisites mention the contract subjects.
- **head-of-sales**: pipeline-review **Stale** check now names the exact `get-timeline`
  subject for a contract (`0-31` / `0-30`) and warns that contract timelines are
  object-level — activities on the Company or a Contact do not surface there, so check
  those before declaring a deal stale.
- **profilvertrieb**: follow-up documentation lists the contract subjects as available once
  a contract exists, while keeping the Contact as the normal acquisition subject.

### Changed — 2026-07-24 MCP battle-test read/discovery fixes (alluvo#2337)
- **bench-check**, **profilvertrieb**: `get-employee-availability` `action: calendar` now returns
  exactly **one row per employee** — a range spanning a month boundary is merged instead of
  yielding one row per calendar month. `available_days` is summed over the whole requested range
  and each row carries a `dates[]` day-by-day breakdown (`date`, `status` = `available` /
  `booked` / `not_available`, `assignment_id`, `notes`). bench-check step 5 now makes a single
  call with `employee_ids` instead of looping per employee, and reads free windows off `dates[]`.
- **manage-contract-lifecycle**: `manage-assignment-contract` `create` now appends an
  **"Unresolved fields"** block to both the preview and the confirmed response, naming whichever
  of staffing role / Abteilung / on-site Ansprechpartner / Empfänger / Arbeitsschutzvereinbarung
  is still open. Documented as required follow-up with the resolution path per field, including
  the Arbeitsschutzvereinbarung lookup via `search-model` on ClientSiteSafetyAgreement (`0-342`),
  and the reminder that on-site contact and recipient are two separate writes.
- **manage-contract-lifecycle**: equal-pay basis (AÜG § 8) — `collective_agreement_family_id` is
  resolved via `search-model` on the new **CollectiveAgreementFamily (`0-417`)** model type.
  It is shared tariff reference data and **read-only over MCP**; a `manage-model` create/update
  is rejected. Never invent an id or create a Tarifwerk record.
- **manage-contract-lifecycle**: dropped the blanket "do not read role ids off `get-model`" —
  a Rahmenvertrag's role rows now expose the resolved role label plus an explicit
  `staffing_role_id` and `base_price`. The row's own `id` is still the pivot id, so the role id
  must come from the `staffing_role_id` field; `list_roles` remains the path for pricing,
  surcharge, work-task and safety-agreement detail.
- **match-bench-to-clients**: filtering Employee (`0-2`) by role now accepts the bare
  **`staffingRoles`** field in `filter_groups` as sugar for `staffingRoles.id` in both
  `search-model` and `query-model`; a near-miss such as `staffingRole` returns a did-you-mean
  pointing at `staffingRoles.id`.

### Changed — 2026-07-24 Terminating an AÜV now cascades to Einsätze, Dienstplan and the employee (alluvo#2309)
- **manage-contract-lifecycle**: step 6 documents the AÜV termination cascade that `cancel_contract`,
  `mark_as_lost` and any manual `transition` to `lost`/`cancelled` now fire. Corrects the stale claim
  that ending a contract leaves everything else untouched: Einsätze flip to `Cancelled` (rows never
  deleted), the Dienstplan is **purged** (soft-deleted — never signed, no operational data) or
  **cancelled** (`cancelled_at` on Schichten, period status `cancelled`; **Locked** periods untouched),
  booked availability is released, and the StaffingDemand coverage status is recalculated. Adds the
  automatic "Einsatz beendet" mail to every employee who already had their §11 Einsatzmitteilung
  (Import contracts and never-notified Einsätze excluded), including that `cancel_contract`'s required
  `reason` reaches the employee. Flags that `lost` → `draft` restores nothing, and keeps `mark_performed`
  explicitly outside the cascade (hence `confirm_future_shifts`).
- **build-dienstplan**: check the contract stage before planning — a `lost`/`cancelled` contract's
  Schichten are no longer effective (gone from calendar, employee app, timesheets, client portal), so
  missing Schichten there are expected rather than a data gap, planning into a terminated contract is
  out, and a revived placement needs a rebuilt plan. Documents the new read-only `cancelled` ("Storniert")
  Dienstplan-Perioden status, which the cascade owns and no operator sets.

### Changed — 2026-07-24 StaffingDemand carries the reported Abteilung as text (alluvo#2141)
- **intake-personalbedarf**: documents `company_department_text` ("Gemeldete Abteilung") next to
  `company_department_id`. Inbound sources (stazzle) no longer create Abteilungs-Stammdaten —
  they link an existing department only on a case-/whitespace-insensitive name match, so a
  machine-channel demand commonly has no linked Abteilung. Read relation → text fallback, and
  don't report the unlinked Abteilung as missing data.
- **head-of-disposition**: same fallback when summarising open `0-415` demand; an unlinked
  Abteilung is not a data gap and blocks neither `qualify` nor matching (the matcher applies the
  identical fallback) — unlike a missing `client_site_id`.
- **match-bench-to-clients**: `company_department_text` does not satisfy the Einsatz's required
  `company_department_id` — check the company's Abteilungen (`0-107`) and let the operator
  confirm before a department record is created from a reported string.

### Changed — 2026-07-24 StaffingDemand (0-415) is the single write path for demand (alluvo#2293)
- **intake-personalbedarf**: rewritten off the removed `manage-staffing-requirement-prompt`.
  Intake now creates a **StaffingDemand (`0-415`)** with `manage-model` (two-stage preview →
  confirm) instead of a legacy `StaffingRequirement` (`0-102`). Documents the field map
  (`company_id`, `client_site_id`, `staffing_role_id`, `title`, `headcount`, `valid_from`/
  `valid_until`, `weekly_hours`, `contact_id`, `company_department_id`, `description`), the
  duplicate check before creating (same company + role + overlapping window on an open demand
  → update it instead), `resolve-staffing-role` for the qualification, ClientSite (`0-341`) for
  the Einsatzort with an explicit never-guess rule, the `signal` default status, and the
  `qualify` / `activate` record actions with `qualify`'s
  `valid_from` + `staffing_role_id` + `client_site_id` precondition.
- **head-of-disposition**: §1c no longer queries two demand models — `0-415` holds all current
  demand regardless of channel and is writable via `manage-model`; `0-102` is legacy, read-only
  for historical records and excluded from the open-demand count. Per-Disponent grouping on
  `0-415` uses `creator_id`, not `owner_id`.
- **match-bench-to-clients**: drops the "machine-channel demand" framing — `0-415` is where all
  demand lives now.

### Changed — 2026-07-24 Rahmenvertrag stage machine documented, `offered`/`employee_accepted` excluded (alluvo#2169)
- **manage-contract-lifecycle**: step 1 now spells out the FrameworkContract stage machine for
  `manage-framework-contract` `action: "transition"`. `manage-framework-contract`'s
  `target_stage` enum was narrowed to `draft`, `pending_review`, `approved`, `sent`, `won`,
  `lost` — `offered` and `employee_accepted` are AssignmentContract-only stages (they need an
  employee to offer an Einsatz to) and are now rejected at both the tool and the model layer.
  The skill states this explicitly and documents the only path to a `won` Rahmenvertrag —
  `approved` → `sent` → `won`, with no direct `approved` → `won` — which is what the
  `commission_as_agreed` gate in step 4 requires. `send_for_signoff` performs `approved → sent`
  itself and the customer's portal signature sets `won`, so operators should not walk the path
  by hand.

### Changed — 2026-07-24 MCP audit DX: contract stage machine + shift-plan shift ids (alluvo#2220)
- **manage-contract-lifecycle**: step 4 now spells out the full AssignmentContract stage machine
  for `manage-assignment-contract` `action: "transition"` (including the `offered` /
  `employee_accepted` employee-side leg and the fact that there is no direct `approved` → `won`),
  instead of only saying transitions are "enforced server-side". Adds two guards the tool now
  documents: `update` requires at least one field to actually change (an id-only call errors
  rather than no-opping), and `action: "delete"` is legal **only** while the stage is `draft` or
  `lost` — every other stage is rejected, so a contract that ran must be ended via
  `mark_performed` / `cancel_contract`, never deleted.
- **build-dienstplan**: documents the per-shift half of `manage-shift-plan` — `list`,
  `add-shift`, `update-shift`, `remove-shift` — including the new `shift_ids` array for
  cancelling/deleting several Schichten in one call, and the stale-id trap: shift ids are
  renumbered by a bulk `create`, so re-`list` before a series of id-based writes. Also states
  that `shift_type` is required on every `shifts[]` entry of a bulk `create`, with the free-day
  code list that is dropped automatically.
- Scope note: the drift issue also listed `query-model`/`search-model` alias-aware "did you
  mean", `manage-location` fuzzy `purpose_slug`, and new Company/User list fields. Those PRs
  are **not merged to the api's main** yet, so no skill documents them — they need their own
  sync once they land.

### Changed — 2026-07-24 Einsatz periods may overlap (alluvo#2300)
- **manage-contract-lifecycle**: the overlap guard is gone — `manage_einsatz` `add`/`update`/
  `extend` no longer refuse an Einsatz period that overlaps a sibling Einsatz, and
  `EINSATZ_OVERLAP` no longer exists. An employee alternating week by week (or day by day)
  between two deployments of the same AÜV is now a legitimate, unblocked pattern.
- **build-dienstplan**: documents the invariant's new home — `manage-shift-plan` now hard-blocks
  a Schicht on a day the employee already works a Schicht under a *different* Einsatz, even
  without a clock-time collision, while a second non-overlapping Schicht within the *same*
  Einsatz (geteilter Dienst) stays legal.

### Changed — 2026-07-24 Einsatzvertrag is multi-Einsatz (alluvo#1902)
- **manage-contract-lifecycle**: step 2 documents the multi-Einsatz model — an AÜV bundles one
  employee with n Einsätze, and Abteilung, Ansprechpartner vor Ort, Zeitraum,
  `shift_plan_choice` and the Stundenregelung live per Einsatz, not on the contract. Adds the
  `action: "manage_einsatz"` sub-action table (`list`/`add`/`update`/`remove`/`extend`), the
  open-ended-only-while-sole-Einsatz rule (incl. the explicit `end_date: ""` clear on
  `update`), and the draft-vs-active stage rules.
- **manage-contract-lifecycle**: documents the write-time guards — the overlap guard
  (preview warns, `confirmed: true` refused with `EINSATZ_OVERLAP` when the period collides
  with a sibling Einsatz), plan-derived dates (`PLAN_DERIVED_DATES`: `start_date` locked once
  a `with_plan` Einsatz has shifts; `end_date` locked only while it has no Stundenregelung),
  and the unknown-field rejection with did-you-mean (`valid_until` → `end_date`, `hours` →
  `agreed_hours`) instead of silent dropping.
- **manage-contract-lifecycle**: warns that `action: "update"` now **rejects** `valid_from`,
  `valid_until`, `hours_arrangement`, `hours`, `min_hours`, `minimum_assignment_hours`,
  `period_type`, `duration_value`, `duration_unit` and `shift_plan_choice` — the contract
  window derives as the envelope of the Einsätze.
- **manage-contract-lifecycle**: step 4 documents the per-Einsatz completeness gate on
  `send_for_signoff` (start date, Abteilung, on-site contact, shift-plan decision, plus
  Stundenregelung or — for a Dienstplan-only Einsatz — at least one planned shift); step 2
  points at `action: "completeness"` for per-gate readiness + the wizard link; step 5
  documents `assignment_id` targeting for `send_assignment_notification` and the automatic
  §11 Einsatzmitteilung that a late-added or extended Einsatz fires on a `won` contract.
- **manage-contract-lifecycle**: the Verlängerung section now routes through `manage_einsatz`
  `sub_action: "extend"` instead of hand-creating an Assignment via `manage-model`; a
  follow-on period no longer needs a new AÜV.
- **manage-contract-lifecycle**: step 2 gains resolve-what-was-named guidance (alluvo#2247):
  resolve the staffing role via `resolve-staffing-role` from the named department context,
  set the Abteilung, attach the named Ansprechpartner as on-site contact — or report what
  could not be resolved instead of leaving Einsatz fields empty.
- **build-dienstplan**: step 1 notes that a contract may carry several Einsätze and that
  Schichten belong to exactly one — list them via `manage_einsatz` `sub_action: "list"` and
  let the operator pick; `plan_provisional_shifts` takes the same `assignment_id`.
- **match-bench-to-clients**: step 5 notes that `create` seeds the first Einsatz (including
  its Stundenregelung), that a matching draft cannot be sent until that Einsatz is complete,
  and that a later match of the same employee to the same client becomes a `manage_einsatz`
  `add`/`extend` on the existing AÜV instead of a second contract.
### Changed — 2026-07-24 manage-framework-contract parity surface (alluvo#2274)
- **manage-contract-lifecycle**: step 1 now documents the Rahmenvertrag tool's guided flow —
  the read-only `completeness` action (present vs. missing grouped as Core data / Recipients /
  Roles & pricing / Safety (AÜG), per-gate readiness for **review** (`draft → pending_review`)
  and **send** (`send_for_signoff`, cumulative so review gaps are folded in) plus View / Edit
  (Wizard) links, the Edit link only while `draft`), and the fact that the same readiness
  summary and the outstanding send-gate gaps are appended automatically to every `create`,
  `update` and `transition` response. Adds the read-only `list_roles` action as the way to
  discover priced roles — it returns the pivot `framework_contract_staffing_role_id` (what
  `update_role`/`remove_role` expect) alongside the real `staffing_role_id` + label, product,
  `base_price`/`defines_base_price`, surcharge and work-task counts and the linked
  Arbeitsschutzvereinbarung — with the explicit warning that an **empty roles list means the
  Rahmenvertrag prices nothing itself** (per-AÜV pricing), not that it covers everything.
  Spells out the full `send_for_signoff` gate (client site + `industry_classification` for the
  AÜG §5 Branchenerklärung, `valid_from`, a recipient whose primary contact has first name +
  last name + email, and every role priced with a work task, a selected surcharge and a safety
  agreement) versus the weaker review gate, and the new write guards: unrecognized params are
  rejected with a did-you-mean instead of silently dropped, a `base_price` above €500/h is
  refused as `IMPLAUSIBLE_RATE` unless `acknowledge_unusual_rate: true`, and on `update`
  `valid_until: ""` clears to indefinite while `valid_from: ""` (and empty-string
  `payment_due_days` / `termination_notice_days`) is an error.
- **match-bench-to-clients**: step 2's Rahmenvertrag check points at
  `manage-framework-contract` `action: "list_roles"` to confirm the contract actually prices
  the matched role, with the same "empty list = prices nothing itself, not covers everything"
  warning — so no rate is quoted from an empty list and no match is dropped over one.

### Changed — 2026-07-23 mass-circular staffing-inquiry auto-redirect (alluvo#2232)
- **intake-personalbedarf**: documents the new `staffing_inquiry_redirect_email` key in
  the `manage-settings` `ai_takeover` group. When set, the mailbox agent answers
  mass-circular staffing inquiries (Rundmails) on personal 1:1 mailboxes with a
  deterministic redirect reply and, after the third circular from the same contact,
  creates a call task to get the Verteiler updated. Fail-closed while blank; the inquiry
  is still classified and demand-captured as usual. `manage-settings` `update` writes
  immediately (no `confirmed` flag) — confirm with the operator before calling.

### Changed — 2026-07-23 Data Quality Dashboard + new remediation kinds (alluvo#2235)
- **triage-data-quality**: `get-issues-overview` overview payload now documented in
  full — `by_category` (including the new `formatting` category), `formatting_pending`
  (pending rows per deterministic AutoFix rule), `enrichment_pending`
  (EnrichmentSuggestions awaiting review, per provider), and `dashboard_url` (deep link
  to the in-app Data Quality Dashboard with tabs `overview` / `issues` / `duplicates` /
  `formatting` / `enrichment` via `?tab=`). Step 3 gains the two new remediation kinds:
  `auto_fix` ({rule, fields, note}) and `agent_fix` ({agent, summary}) are resolved by
  the automation pipeline / operator review on the dashboard — the assistant never
  fixes them by hand. Wrap-up points formatting/enrichment backlog at the dashboard.
- **merge-duplicate-companies**: notes that the standalone Duplicate Records settings
  page now redirects to the Data Quality Dashboard's Duplicates tab.
### Changed — 2026-07-23 AC-level safety agreement fallback in the AÜV wizard (alluvo#2229)
- **manage-contract-lifecycle**: the Arbeitsschutzvereinbarung on an FC-covered
  Einsatzvertrag no longer always comes from the Rahmenvertrag. New step-2 note: when the
  FC's staffing-role row declares a safety agreement, the AC's
  `client_site_safety_agreement_id` is kept in lockstep (auto-filled, divergence rejected);
  when the role row declares **none** (or no role row exists), the operator selects the
  agreement on the AC itself (wizard step 1 or `manage-model` on `0-31`) and it is bundled +
  signed as an annex of the Einzel-AÜV at checkout — same mechanism as external-master
  Rahmenverträge. Wizard data carries server-computed `framework_role_safety_agreement_id` /
  `_label` to tell the cases apart.

### Changed — 2026-07-23 manage-inbox-forwarding-targets tool, server v1.2.13 (alluvo#2202)
- **clean-inbox**: forwarding targets are now assistant-configurable. The "Forwarding
  invoices" section documents the new `manage-inbox-forwarding-targets` tool (`list` /
  `set`, settings-manage gated): `set` is a **full replace** of one inbox's
  `targets: [{email, label}]` (label ≤ 100 chars; empty list clears all) with the standard
  two-stage `confirmed: false` preview → `confirmed: true` save. The stale instruction to
  send the operator to Einstellungen → Inbox → Weiterleitungsziele is replaced by the
  in-assistant flow: confirm the address with the operator → `set` (existing targets + new
  one) → `forward`. Targets are only ever added with explicit operator confirmation.

### Changed — 2026-07-22 mailbox agent: StaffingDemands + gated proposal drafts from inbound mail (alluvo#2147)
- **intake-personalbedarf**: where the mailbox agent is enabled (tenant feature +
  per-mailbox setting), an inbound email on a *personal* 1:1 mailbox that describes a
  Personalbedarf auto-creates a `StaffingDemand` (`0-415`, duplicate-checked, status
  `signal`/`qualified`). Before capturing an email-originated request as a
  `StaffingRequirement` (`0-102`), check `0-415` for an existing demand. Shared inboxes
  remain uncovered.
- **match-bench-to-clients**: matching on a machine-channel demand auto-drafts one
  candidate-proposal email (~15 min after matching, unless an operator offered first) and
  parks it approval-gated; matches then carry `offered_at` + `proposal_email_id` — check
  before drafting a competing proposal.
- **head-of-disposition**: personal-mailbox email intake added to the machine-channel
  list; "proposal drafted, awaiting approval" documented as a normal in-flight state
  (auto-drafter, never sends without approval; missing contact/Einsatzort yields a
  blocker task instead).
- **clean-inbox**: new cluster row — demand mails in a shared inbox are NOT auto-captured
  (agent covers personal mailboxes only); route through `intake-personalbedarf` or task.

### Changed — 2026-07-22 manage-ticket forward action / Fibu-Weiterleitung (alluvo#2116)
- **clean-inbox**: rewrote the "Forwarding invoices" section. The stale guidance said
  `reply` can only reach the ticket's own contact and mandated a task (or an out-of-assistant
  forward) for bookkeeping. The sanctioned path is now `manage-ticket` `action: "forward"` —
  preview → confirm (same as reply). `to` is **required** and must case-insensitively match
  one of the inbox's configured `forward_targets` (**Einstellungen → Inbox →
  Weiterleitungsziele**); free-text recipients are rejected, and an inbox with no targets
  errors with an operator hint. Documented `note` (optional cover note),
  `include_attachments` (default `true`), and `close_after` (requires `close_reason_id` +
  `close_reason_note` when the reason needs one) — the usual finish: forward to Fibu with
  `close_after` + a resolved reason referencing the forward.

## [0.7.0] — 2026-07-21

### Changed — 2026-07-21 commute allowance / Wegstreckenpauschale surface (alluvo#2109)
- **approve-stundenfreigabe**: new "Adjacent capability: commute allowance" section. The
  monthly Wegstreckenpauschale is live-derived and display-only (Salary tab) — **no MCP
  tool**, no approval flow, no payroll/DATEV export; it is not a `0-20` Reimbursement.
  Operators *can* set `commute_allowance_entitlement` on Salary via `manage-model`
  (create + update, preview → confirm): `contractual` / `company_policy` (default) / `none`.
  The per-employee rate override is the existing `distance_allowance_rate` field — there is
  no `commute_allowance_rate` on Salary. The Assignment `double_commute_distance` toggle and
  the tenant-wide enable/rate settings are **not** MCP-writable → directed to the app.
  Documented the attended-shifts (Dienstantritt) basis: not cancelled + Dienstplan
  Published/Locked + no approved absence overlapping the date; two shifts/day = two commutes.

### Changed — 2026-07-21 manage-task confirm_token flow, server v1.2.10 (alluvo#2096)
- **clean-inbox**, **call-summary**: documented the new `confirm_token` confirmation
  path on `manage-task` — every `create`/`update`/`bulk-update` preview returns a
  single-use token (10-minute TTL); confirming with `action` + `confirm_token` +
  `confirmed: true` replays the previewed payload, so long task bodies are not resent.
  Full-payload confirm remains as fallback. The v1.2.10 Ticket↔Candidate
  `manage-association` rejection (Contact-steering hint) needs no skill change —
  clean-inbox already resolves ticket persons via the Contact (`contact_id` on
  Employee/Candidate), and no skill attaches people to tickets directly.

### Changed — 2026-07-21 Reimbursement MCP surface, server v1.2.10 (alluvo#2094)
- **approve-stundenfreigabe**: new "Adjacent capability" section — submitted
  reimbursements (`Reimbursement`, `0-20`) can now be reviewed via MCP. Lifecycle runs
  only through `manage-record-action` with action names `submit`, `cancel`, `approve`,
  `reject`, `request_revision`, `mark_as_paid` (reject/request_revision take a `reason`;
  submit/cancel are owner-only; own reimbursements can't be approved). `manage-model`
  creates drafts only, updates are accepted only while `draft`/`needs_revision`, and
  `status` is never writable as a field. `amount` is EUR, not cents. Description gains
  the Spesen/Auslagen trigger terms.
- **clean-inbox**: the money-owed cluster row now names the concrete check — `query-model`
  on `Reimbursement` (`0-20`) by `employee_id`, with the status caveat (`draft`/
  `needs_revision` ≠ submitted; only `approved`/`paid` settles the claim). Tasks-over-
  writes invariant unchanged.

### Changed — 2026-07-21 clean-inbox: get-attachment PDF semantics (alluvo#2082)
- **clean-inbox**: documented the actual `get-attachment` PDF behavior — PDFs return
  extracted text (~30,000-char cap, truncation marked), scanned PDFs without a text layer
  render as up to 4 page images under the default `mode: "auto"`, and files over 5 MB are
  rejected with a clear error. Replaces the vague "PDF attachments come back readable
  directly" wording. The `manage-ticket` list-row timestamp relabeling mentioned in the
  drift issue has not landed on api main; no skill documents the row format, so no change
  there.

### Changed — 2026-07-21 MCP v1.2.8 surfaces (alluvo#2083)
- **enrich-contacts-from-activities** (references/mcp-recipes.md): `get-model` on a
  Contact now compacts activity relations (emails/calls/notes/…) to a count + one-line
  previews by default — documented that the recipe's direct Email-record fetch (`0-121`)
  is the correct, unaffected path for full bodies, and that `full_activities: true`
  exists but is rarely needed here.
- **clean-inbox**: `manage-task` datetimes (`due_at`/`reminded_at`/`wait_until`) are
  interpreted tenant-local, not UTC — noted on the due-date staggering guidance.
- **call-summary**: fixed the task-preview param name to `due_at` (was `due_date`),
  noted its tenant-local interpretation, and steered person-level follow-ups to the
  person's Contact taskable (not Employee).
- No change needed for `get-attachment` PDF modes (clean-inbox already describes PDFs
  as coming back readable) or for the Ticket↔Employee association rejection (no skill
  documents ticket associations).

### Changed — 2026-07-21 manage-ticket v1.2.7 additions (alluvo#2072)
- **clean-inbox**: synced to MCP v1.2.7 — `list` rows now lead with the numeric ticket id
  (`#123`) that `get`/`set_status`/`assign`/`bulk_update` need; `search` also matches
  `TKT-…` reference numbers; new `created_after`/`created_before` (Y-m-d) window the list
  instead of paging the whole inbox; `get` shows every thread message's id, so a full body
  fetch via `message_id` is always possible (not only on `[truncated]` markers). Added the
  `contact_id` filter on Employee (`0-2`)/Candidate (`0-81`) as the way to resolve a
  ticket's Contact to its Employee without email guessing.
- **enrich-contacts-from-activities** (references/mcp-recipes.md): documented the reverse
  Contact → Employee/Candidate lookup via the new filterable `contact_id` column.

### Added — 2026-07-21 clean-inbox skill
- New **clean-inbox** skill: triage a shared company inbox (General/EmployeeSupport/
  CustomerSupport/TalentHub) MCP-natively. Ports the evidence-based methodology of the
  `clean-company-inbox` dev skill onto `manage-ticket`/`get-attachment`/`manage-task` —
  no ticket closes without a `close_reason_id` + a numbers-backed `close_reason_note`, and
  no shift/absence/reimbursement is ever fabricated from ticket content; a data gap always
  becomes a task on the resolved Contact instead. Since `set_status`/`bulk_update` have no
  `confirmed: false` preview, the skill treats presenting the close plan to the operator as
  the missing checkpoint before any close.

### Changed — 2026-07-21 StaffingDemand Einsatzort (`client_site_id`) (alluvo#1967)
- **intake-personalbedarf**: noted that a machine-channel `StaffingDemand` (`0-415`) can
  arrive without an Einsatzort, that `client_site_id` gates `qualify`, proposal drafting,
  the AÜV draft and distance matching, and that a missing site must be flagged to the
  operator rather than guessed.
- **manage-contract-lifecycle**: documented the Einsatzbetrieb resolution order for an
  Einsatzvertrag draft created by `accept` on a `StaffingDemandMatch` (`0-416`) — demand's
  own `client_site_id` → Rahmenvertrag's → company's primary site — so an operator is not
  surprised which ClientSite the AÜV names for a multi-site client.

### Changed — 2026-07-21 Demand matching routed through the SSOT scorer (alluvo#1963)
- **head-of-disposition**: added a callout in "Open Personalbedarfe" explaining how a
  `StaffingDemandMatch` (`0-416`) is produced. `score` is the **deterministic 0–100 fit
  score** from the shared matching engine (role .35 / experience .25 / sector .20 /
  distance .15 / compensation .05), not the AI ranker's confidence — the AI contributes
  only `rank` and the `note`. Eligibility, blacklist, role-fit floor and travel radius are
  hard gates that run *before* ranking, and only the top ~10 scored survivors reach the
  ranker (`matching.demand_shortlist_size`), so a short shortlist is expected. Also
  documents the no-match task/Slack breakdown, including the real *außerhalb des
  Einsatzradius* count (previously always 0) and how to read it as a geo/data gap.
- No change to `match-bench-to-clients` / `bench-check` / `profilvertrieb`: those work the
  opportunity models (`0-126` / `0-403` / `0-404`) via `find-matches-prompt`, not the
  StaffingDemand match pipeline.

### Changed — 2026-07-21 StaffingRequest MCP removal (alluvo#1915)
- **intake-personalbedarf**: the removal callout now also names `StaffingRequestMatch`
  (`0-410`) and states that both retired model type IDs return not-found via MCP. Verified
  against api `origin/main`: neither case exists in `ModelTypeEnum`. Complements the
  alluvo#1903 entry below, which retired the `0-127` reference itself.

### Changed — 2026-07-21 StaffingDemand transition (alluvo#1903)
- **intake-personalbedarf**: dropped the reference to `StaffingRequest` (`0-127`) — that
  model no longer exists. Operator-captured intake still creates a **StaffingRequirement**
  (`0-102`) via `manage-staffing-requirement-prompt` — unchanged. Clarified that
  `StaffingDemand` (`0-415`) is the in-progress successor that inbound *machine* channels
  write to directly (client-portal bookings, guest profile-page requests, stazzle sync, AI
  call/email intake); it is read-only via MCP and never a `manage-model` create/update
  target.
- **head-of-disposition**: "Open Personalbedarfe" now queries **both** demand models so the
  count is not under-reported — `StaffingRequirement` (`0-102`, operator-captured) and
  `StaffingDemand` (`0-415`, machine-channel demand; open = `signal`/`qualified`/`active`).
  Documents the record actions a Disponent uses on it via `manage-record-action`: `qualify`
  and `activate` on `0-415`, `mark_offered` / `accept` / `decline` on `StaffingDemandMatch`
  (`0-416`). Notes that `qualify` requires `valid_from`, `staffing_role_id` and
  `client_site_id` (Einsatzort), and that `accept` produces a DRAFT `AssignmentContract`
  (`0-31`) only — sending/approving/signing stay in `manage-contract-lifecycle`.

### Changed — 2026-07-21 Timeline and task previews are cleaned and explicitly truncated (alluvo#2054)
- Api-side, `get-timeline` (~200 chars) and `get-open-tasks` (~150 chars) now strip HTML
  before capping the body, and mark what was cut as
  "… [truncated — N more characters. Fetch the full record with `get-model`.]" instead of a
  bare `…`. Email-type timeline entries additionally lose quoted threads, signatures and
  disclaimers. (`manage-ticket` got the same treatment plus a new `message_id` param, but no
  operator skill works on tickets, so nothing changed for that surface.)
- **enrich-contacts-from-activities** (`references/mcp-recipes.md`): explicit warning that a
  contact signature is *never* present in a timeline preview — use the timeline only to get the
  email `record_id`, then read the raw body via `get-model`.
- **account-research**: timeline entries are cleaned previews; fetch an entry with `get-model`
  before summarising it into the dossier.
- **call-prep**: pull a truncated entry in full before briefing the operator on what was agreed.
- **daily-briefing**: task bodies are ~150-char excerpts; open the task with `get-model` when
  the truncation marker appears.

### Changed — 2026-07-21 Company timelines do not roll up contact activity (alluvo#2047)
- The `get-timeline` tool description was corrected api-side: an activity appears on a
  company's timeline only when it is associated with that company itself. Activities
  logged solely on a Contact never surface there — there is no roll-up from a company's
  associated contacts (behaviour unchanged; only the documented contract was wrong).
- **account-research**: when researching a company, also pull `get-timeline` for each key
  contact (`0-105`) and merge, marking the source subject.
- **call-prep**: step 3 now loads both the company timeline (`0-3`) and each contact
  person's timeline (`0-105`) instead of the company's alone.
- **call-summary**: the pre-draft timeline check now requires the contact-level call
  (`0-105`) when the recipient is known; company-level is a fallback only.
- **profilvertrieb**: reworded the empty-company-timeline note — it is intended behaviour,
  not the bug previously referenced as api#1373. The workaround (query the contact
  directly) is unchanged.

### Changed — 2026-07-21 Employee invitation moves to a record action (alluvo#2028)
- **onboard-new-employee**: the invitation step no longer calls
  `get-employee-invitation-status` + `invite-employee-user`. It now runs the
  `invite-user` record action on the Employee (`model_type "0-2"`) through
  `manage-record-action` — `list` surfaces the gate status in
  `unavailable_reason` (has user / no email / no employment relationship /
  requires Arbeitsvertrag / pending invitation), then `execute` with
  `confirmed: false` previews and `confirmed: true` sends. `data.user_type_slug`
  defaults to `external`. The two old tools remain documented as deprecated
  fallbacks for one release.

### Changed — 2026-07-21 MCP profile-URL / completeness / media consolidation (alluvo#2027)
- **match-bench-to-clients**, **enroll-outreach**, **profilvertrieb**: `get-employee-profile-url`
  is superseded by `get-profile-url` (`model_type` `0-2` Employee / `0-81` Candidate /
  `0-105` Contact, `action: "public_url"`). The link resolves to the person's identity
  Contact regardless of the role passed in, is read-only and valid 7 days. Skills now name
  the action explicitly and restate that `action: "completion_link"` (Candidate only) is
  self-service and must never be sent to a customer.
- **onboard-new-employee**: `get-employee-completeness` is folded into the role-aware
  `get-profile-completeness` — call it with `employee_id` and read the `employee_operational`
  block for the operational score; the same call also returns the public-profile and
  non-public enrichment buckets with per-field fix-hints.
- `get-employee-profile-url`, `get-candidate-profile-url`, `manage-candidate-profile-link`,
  `get-employee-completeness`, `manage-contact-avatar` and `manage-job-media` remain
  registered as deprecated alias shims for one release — skills use the consolidated names.

### Changed — 2026-07-21 Scheduled record enrollment + date operators (alluvo#2031)
- **build-automation-agent**: a scheduled workflow with a `trigger_model_type` no longer
  ignores that model — each tick now sweeps its records, evaluates `conditions` per record
  and fires the actions once per match (capped at 500 enrollments/sweep). Documented the two
  scheduled modes (record-less vs. record enrollment), the enrollment semantics of
  `allow_reenrollment` on scheduled (once-ever vs. once-per-tick), and the ⚠️ advisory a
  condition-less enrollment workflow triggers.
- **build-automation-agent**: added the five date condition operators
  (`date_is_last_day_of_month`, `date_in_current_month`, `date_within_next_days`,
  `date_before_today`, `date_after_today`, tenant-local calendar) and the `create_task`
  keys `due_relative_to` / `due_offset_days` for record-relative due dates.
- **build-automation-agent**: `action: "test"` now dry-runs a scheduled workflow that has a
  `trigger_model_type` (record-less scheduled is still refused) — the skill previously said
  no scheduled workflow could be dry-run.
- **build-automation-agent**: notes that there is no built-in AÜV renewal reminder; an
  operator wanting one builds it as a scheduled enrollment workflow.

### Changed — 2026-07-21 Activity tools merged into `manage-activity` (alluvo#2026)
- `manage-call`, `manage-meeting` and `manage-note` are folded into a single
  `manage-activity` tool selected by `activity_type` (`call` | `meeting` | `note`) plus
  `action` (`create` | `update`). The old names stay registered as deprecated alias shims
  for one release, then go away.
- **call-summary**, **profilvertrieb**, **log-company-signal**, **enroll-outreach**: updated
  to call `manage-activity` with the correct `activity_type` / `action`, and to address the
  subject as `subject_type` + `subject_id` (`0-105` Contact, `0-3` Company) instead of
  `contact_id`. Employee/Candidate activities are logged on the linked Contact.
- **call-summary**: documents the required create fields per type (`direction` + `outcome`
  for a call, `body` for a note) and the preview's hint to log onto an existing scheduled
  meeting (`activity_type: meeting`, `action: update`) rather than creating a duplicate.
- Two-stage `confirmed:false` → `confirmed:true` write flow is unchanged.

### Changed — 2026-07-21 MCP meta folds + issues-tool merge (alluvo#2029)
- **manage-meta-ads**: the tool table drops `manage-meta-bulk-operations` and
  `manage-meta-targeting`. Their actions moved, unrenamed, into
  `manage-meta-campaign` (`bulk_pause`, `bulk_resume`, `bulk_update_budget`,
  `clone_campaign_to_accounts` — all require `confirmed: true`) and
  `manage-meta-audiences` (`list_presets`, `save_preset`, `apply_to_adset`,
  `delete_preset`). The `manage-meta-campaign` row also now lists the
  `archive`, `delete`, `update_ad_creative`, and `conversions` actions it
  already exposed. A note records that the old names survive only as deprecated
  aliases for one release and must not be called.
- **triage-data-quality**: `open-data-quality-dashboard` is folded into
  `get-issues-overview` as `action: "open-dashboard"` (`"overview"` stays the
  default). The follow-up pointer now names the consolidated call.

### Changed — 2026-07-20 §11 AÜG Einsatzmitteilung is auto-sent on commissioning (alluvo#1882)
- **manage-contract-lifecycle**: step 5 now states that the §11 Abs. 2 Satz 4 AÜG
  Einsatzmitteilung is sent **automatically** when an assignment contract becomes commissioned
  — on every operator path to `won` (portal signature, `transition`, `commission_as_agreed`)
  and on client-portal checkout. Imported contracts (`record_source: Import`) are excluded.
  Check whether it already went out before offering the on-demand send; the sent-stamp prevents
  double-sends and a later send is flagged as a correction.
- **manage-contract-lifecycle**: documented the opt-out — `manage-settings`, group `contract`,
  key `auto_send_assignment_notification_on_commission` (bool, default `true`) — as a
  tenant-wide, previewed-and-confirmed change. The client-portal booking-draft flow sends
  regardless of the flag.
- **manage-contract-lifecycle**: corrected the `commission_as_agreed` note, which claimed it
  never sends the Einsatzmitteilung.

### Changed — 2026-07-20 cancel_contract + mark_as_lost are MCP-callable (alluvo#1891)
- **manage-contract-lifecycle**: step 6 is now "Ending a contract — performed, cancelled, or
  lost" and documents all three terminal paths with a pick-by-what-happened table.
  `cancel_contract` (Storno, NEW) ends a *signed* contract that was terminated administratively
  or never came about — `stage: cancelled` + `cancelled_at`/`cancelled_reason`, derived status
  Cancelled and forecast Lost, reason required, only while `stage: won` and status
  `commissioned`/`performing`. `mark_as_lost` is now MCP-exposed and stays pre-signature only
  (`draft`…`sent`), never on a won contract. None of the three touches the §11 Einsatzmitteilung.
  Trigger terms "Vertrag stornieren" / "Storno" / "als verloren markieren" added.

### Changed — 2026-07-20 workflow transition triggers + enroll-once (alluvo#2004)
- **build-automation-agent**: documented the new firing semantics for event-triggered
  workflows (`trigger_event: "updated"`). Such a workflow now fires only on the **transition**
  into the matching state (one of the condition fields must have changed in that save), and
  each record **enrolls once** unless the new `allow_reenrollment` param (boolean, default
  `false`) is passed. Never promise "fires every time X" without setting it explicitly.
  `list` marks re-enrollment, `get` returns the flag, `create`/`update` accept it, and the
  `updated` dry-run now reports an `Enrollment:` line plus a transition note.

### Changed — 2026-07-20 Person locations are Contact-owned; Employee parent now rejected (alluvo#1987, alluvo#1996, alluvo#2011)
- **bench-check**: added the canonical "how the home location is added" recipe —
  `manage-location` `action: "create"` with `parent_type: "0-105"` + the **Contact** id.
  An Employee (`0-2`) / Candidate (`0-81`) parent is now **rejected** for the `home`
  purpose ("Purpose 'Home' is not allowed for employee"); the home lookup is strictly
  purpose-matched with no fallback, so only `purpose_slug: "home"` counts as a home
  address. Notes the required `valid_from` and `city`, the `DE` country default, the
  tenant-defined-purpose `list-purposes` escape hatch, and that `home` **auto-geocodes on
  attach** (no separate geocode step).
- **onboard-new-employee**, **profilvertrieb**: `home_location` is not a `manage-model`
  field — short Contact-parent recipe plus a pointer to `→ bench-check`.
  onboard-new-employee also routes candidates to `get-profile-completeness`
  (`contact_id` / `candidate_id` / `employee_id`, exactly one), whose per-item fix-hints
  are to be followed verbatim.
- **triage-data-quality**: the Location remediation maps the remediation prefill's
  `model_type` / `model_id` onto the tool's actual `parent_type` / `parent_id` params and
  notes the required `valid_from`; it now names which purposes are contact-only (`home`, `work-site`) vs company-side (`headquarter`, `billing-address`,
  `branch-office`, `client-site`), and that `work-site` does **not** auto-geocode.
- **enrich-contacts-from-activities**: addresses are identity data — read via `query-model`
  on `0-105` with `include: { locations: … }` (now supported on Contact), write via
  `manage-location`, never `manage-model`.

### Changed — 2026-07-17 candidate profile blocks + no-unbidden-rate guardrail (alluvo#1899)
- **profilvertrieb**: `build-profile-links-block` now also presents **candidates** — pass
  `candidate_ids` in place of `employee_ids` (one kind per call). Candidate blocks show the
  headline and **never** a rate; `include_rate` / `build-availability-block` stay employee-only.
- **profilvertrieb**: added a guardrail — build the profile block with the tool, never
  hand-assemble the link/HTML, and never lift a rate or any figure from a free-text field
  (`summary`/`bio`/notes) into a customer email. The block's `include_rate` (employees, default
  off, explicit instruction only) is the sole sanctioned rate; a candidate's desired rate is
  never customer-facing.
- No prompt change needed for the sibling api change (`manage-model` / `bulk-manage-model`
  preview now runs the same Form Request validation the confirm runs) — skills already do the
  two-stage `confirmed:false` → `true` write; the preview just catches type mismatches earlier.

### Changed — 2026-07-16 signing-deadline cap + escalating signature reminders
- **Deadline is now time-based**: the signing/reservation deadline is 12h before the first planned shift, or 24h before `valid_from` when none exists (was: start-of-day). Overdue escalation fires at that deadline.
- **Overdue handling**: once the assignment start passes still unsigned, the customer is no longer emailed; the owner gets a one-time "Unterschriftsfrist verpasst" alert and a follow-up task is opened automatically.
- **manage-contract-lifecycle**: `send_for_signoff`'s `reserve_until` is now **capped to the
  assignment start** — a value later than `valid_from` is clamped (MCP) or hard-rejected (web
  dialog), because the contract must be signed before the Überlassung begins (§ 1 Abs. 1 AÜG).
  The signing-invitation email now always carries the AÜG legal notice, and its subject/banner/
  tone escalate on the daily reminder tick (gentle ≥24h → consequences ≥48h → red "Alarmstufe
  Rot" once the start is <24h away or overdue). Skill updated to stop promising signing windows
  past `valid_from` and to set operator expectations for the escalating customer mails.

### Fixed — 2026-07-16 plugin-drift backlog sync (37 issues, #1488–#1806)
- **manage-contract-lifecycle**: external-master-FC toggle fields; ClientSite create-dedup
  handling; `send_for_signoff`'s auto-reservation (`reserve_until`,
  `keep_open_availability_day_ids`) that closes the double-booking gap from #1500/#1506; the
  `correct_client_site` record action for fixing the Einsatzbetrieb post-WON;
  `send_assignment_notification`'s `document_ids` (remembered default) + auto correction-
  marking on resend; the new `mark_performed` action to end an assignment early; and a new
  Verlängerung section distinguishing within-contract vs. beyond-contract extensions (AI
  takeover follow-up path).
- **build-dienstplan / head-of-disposition**: corrected the ArbZG guidance to the real
  hard/hint split — hard limits (>10h/day, rest below the floor) have no override, ever;
  deviation-permissible ArbZG (10–11h rest, >48h/week, Sunday work — the normal case for a
  care-sector agency) are non-blocking hints, not violations to talk operators out of.
  Documented the separate availability-guard block (`availability_override_reason` must be a
  human-typed decision, never assistant-authored).
- **record-absence**: fixed a stale field name (`absence_type` → the real `absence_type_id`)
  and pointed at the newly MCP-readable `AbsenceType` (0-14) to resolve it instead of guessing.
- **intake-personalbedarf**: documented the StaffingRequirement (0-102, operator intake) vs.
  StaffingRequest (0-127, portal/stazzle inbox, MCP-read-only) split as a known gotcha.
- **build-automation-agent**: removed the retired `model_provider`/`model_name` params;
  documented `pseudonymize_pii`, the structured-array-output + table/list placeholder
  guidance, the write-safe `(WRITE)` bridged tool (draft-only writes), the system-agent
  delete guard, and the new `yearly` schedule preset.
- **profilvertrieb / bench-check**: dropped the `score is_not_null` workaround now that MCP
  sorting is NULLS-LAST by default; noted `get-employee-profile`/`get-employee-availability`
  already rank Staffing Opportunities score-first with conflicts pre-excluded; noted the new
  `company.name`/`company.last_contacted_at` fields on EmployeeStaffingOpportunity (0-126).
- **profilvertrieb / enroll-outreach**: added the non-blocking `do_not_invest`
  account-potential advisory alongside the existing lead-status warning.
- **profilvertrieb**: fixed a leftover reference to ranking by `forecasted_revenue` in the
  Fachliche-Eignung gate (now consistent with the score-first ranking above); Step 5 now
  says explicitly to call `get-timeline` on the **contact** directly, not just the company —
  company-level `get-timeline` can come back empty while the linked decision-maker has active
  recent engagement (api#1373, still open) (alluvo#1375).
- **enrich-contacts-from-activities**: `get-timeline` now returns a `record_id` per entry and
  Contact/Company `query-model` support `include: {emails, calls, activityNotes}` — simplified
  the evidence-gathering recipe, kept the old `from_email` match as a fallback.
- **manage-meta-ads**: `manage-meta-leads get_form` now reports the form's actual Page
  binding, directly diagnosing "sync returning 0 leads" instead of assuming it's unbound.
- Reviewed and closed without a skill change: ai-takeover meeting gating (#1488 — no skill
  assumes an auto-sent invite), manage-settings email/promo fields (#1518 — no skill manages
  tenant settings), the 2026-07-08 log-audit hotfix (#1530 — no skill held a stale claim),
  the address-refactor manage-location→manage-address surface (#1535 — not yet merged to
  main; re-review once it ships), compensation-component MCP exposure (#1538/#1574 — folded
  into the automation-agent write-bridge note, no skill held the stale claim itself), KB
  engagement/related-pages (#1636/#1639), employee time-entry self-delete + KB URL move
  (#1643), feedback-template schema (#1648), VehicleInspection (#1652), WhatsApp campaigns
  (#1661), get-model-schema action-managed hints (#1671 — skills already name the correct
  actions directly), `update_candidate_profile` free-text qualification (#1672 — a WhatsApp
  AgentFlow tool, not an operator-plugin surface), assignment-forecast export (#1731 —
  already covered by the existing head-of-sales entry), Salary `equalization_allowance`
  (#1741), `resolve-staffing-role` (#1754 — no skill currently guesses a role id), and
  two-hop `filter_groups` paths (#1803 — no skill held stale one-hop-only guidance and none
  currently needs Contact-by-company-sector filtering).

## [0.6.2] — 2026-07-15 *(entry backfilled)*

### Fixed
- **Plugin-drift correction (`Doing-the-right-things/alluvo#1733`): the
  `FRAMEWORK_CONTRACT_REQUIRED` gate applies to `commission_as_agreed` only, not to
  approving or sending an Einsatzvertrag.** Corrects the previous entry below, which
  over-stated the backend rule: `manage-assignment-contract` `action: "transition"` →
  `target_stage: approved` is **not** gated, and sending an approved Einsatzvertrag for
  signature is always allowed — including for a standalone AÜV with no Rahmenvertrag
  selected, which is a normal, valid case (client signs it through the portal like any
  other). Only the operator shortcut `action: "commission_as_agreed"` (marking the
  contract `won` directly, without a portal signing flow) still requires a linked
  Rahmenvertrag that is itself `won`, covers the Einsatzvertrag's staffing role, and
  whose validity window covers the Einsatzvertrag's period; otherwise it returns
  `FRAMEWORK_CONTRACT_REQUIRED`. `manage-contract-lifecycle` and `match-bench-to-clients`
  now state this correctly.
- ~~Plugin-drift fix (`Doing-the-right-things/alluvo#1733`): Einsatzvertrag approval
  now requires a signed Rahmenvertrag.~~ *(superseded by the entry above — approving and
  sending are not gated; only `commission_as_agreed` is.)*

### Added
- **`build-automation-agent`** — new skill wrapping the new automation-agent MCP surface:
  `manage-automation-agent` (`list`/`get`/`create`/`update`/`delete`/`enable`/`disable`/
  `describe-tools`/`test`) creates a scoped AI agent (`type=automation`) with a fixed
  `enabled_tools` catalogue and an `output_schema`, whose structured output can then feed a
  new `manage-workflow` `trigger_event=scheduled` workflow (a `schedule_preset` or raw
  `schedule_cron`, no triggering model) chaining a `run_agent` action into
  `transactional_mail` (or `create_task`) via `{{agent.*}}`/`{{run.*}}` placeholders. Guides
  the operator through describe-tools → design instructions/output_schema → create (preview
  first) → dry-run via `test` (no side effects) → build + enable the scheduled workflow.
  Carries an explicit data-minimization/AÜG note for agents touching sensitive data (e.g.
  sick days), mirroring the shipped "Spendit Qualifier" example agent. Listed in
  `using-alluvo-operator` (new "Automation" category) and the README.

### Changed (manage-meta-ads overhaul)
- **`manage-meta-ads` now follows the skill conventions** — Purpose / Prerequisites
  / Output / Related skills structure, explicit MUTATING banner ("spends real
  money"), and it is now listed in the dispatcher (`using-alluvo-operator`, new
  "Marketing & recruiting ads" category) and the README.
- **Removed the shell step from the creatives workflow.** The skill no longer
  instructs a `curl` upload (skills are MCP-only — no shell, no file I/O): local
  images are uploaded by the operator to the signed `manage-temp-vault` URL;
  already-public URLs / existing media are passed directly to `upload_image`.
- Moved the "Meta tools aren't available" root-cause forensics to
  `references/troubleshooting.md` (Claude-facing), keeping the operator-facing
  guidance (remove & re-add the connector; it is not an auth problem) in the
  skill. Trimmed internal code references and tenant-specific history from the
  shipped prose.

### Fixed
- **MCP-correctness fixes** (verified against the server source):
  - Contacts (`0-105`) have no `company_id` filter — `account-research` and the
    `head-of-sales` single-threaded check now go through CompanyContactPerson
    (`0-361`) / `get-model-graph` instead.
  - Contract stage transitions: `manage-model` has no `set_stage` action —
    `manage-contract-lifecycle` now uses `manage-assignment-contract`
    `action: "transition"` with `target_stage`.
  - `log-signal` valid types are `hiring`, `expansion`, `funding`,
    `product_launch`, `partnership`, `leadership_change` — removed the invalid
    `relocation` / `prospect` / `re-engagement` types from `log-company-signal`
    and the invalid `Prospect` signal from `prospect-companies`.
  - Outreach enrollment action is `create` (plus `check`/`list`/`stats`/`pause`/
    `resume`/`unenroll` and `bulk-*`) — there is no `enroll` action.
  - Meeting datetime field is `start_at`, not `scheduled_at` (`daily-briefing`).
  - No `stage_changed_at` field on contracts — stuck-deal detection now uses the
    per-stage `marked_as_<stage>_at` timestamps (`head-of-sales`).
  - No "ShiftPlan" model type — Dienstplan-gap check clarified to query Shift
    records (`head-of-disposition`).
- **`define-icp` now stores ICPs as first-class IdealCustomerProfile records
  (`0-270`)** instead of tagged notes — matching what `profilvertrieb` reads;
  `prospect-companies` loads the segment from `0-270` too.

### Changed
- **Conventions sweep across all skills.** Every skill now states read-only vs.
  mutating explicitly near the top, carries a `## Related skills` section, and uses
  the uniform `→ skill-name` cross-link style. Manager skills (`head-of-sales`,
  `head-of-disposition`) and `call-summary` now document the on-behalf-of caveat:
  writes are attributed via `owner_id`, but permissions always remain the
  authenticated operator's own.
- **Trigger dedup.** "Profilvertrieb starten" no longer triggers
  `prospect-companies` (that phrase belongs to `profilvertrieb`); "Dubletten
  bereinigen" now triggers only `merge-duplicate-companies`. `prospect-companies`
  was retitled to "Prospect Companies (Geo + ICP Lead Shortlist)".
- **intake-personalbedarf** no longer suggests outreach enrollment for candidate
  sourcing (enrollment is client acquisition); follow-ups now route to
  `match-bench-to-clients` / `manage-contract-lifecycle`.
- README: corrected "German-first" to "English-first, German industry trigger
  terms retained" (the 0.3.0 language switch).

## [0.6.1] — 2026-07-15 *(entry backfilled)*

Bumped the same day as 0.6.2. The entries of that window carry no date of
their own, so they cannot be split between the two bumps honestly — they are
listed under 0.6.2 above.

## [0.6.0] — 2026-06-23

Respect the backend specialty-fit signal (#980) so operators never pitch a
fachlich-falsche (clinically wrong) profile — e.g. an adult-ICU nurse to a dedicated
children's hospital, the bug that motivated the backend change.

### Changed
- **Profilvertrieb consults `specialty_fit` explicitly.** Because matches are ranked by
  `forecasted_revenue` (not `score`), a backend-capped specialty `conflict` does not sink
  on its own. The skill now reads the top-level `specialty_fit` (`suitable` / `conflict` /
  `unknown`) on each `EmployeeStaffingOpportunity` (0-126) and **hard-skips `conflict`
  matches** regardless of revenue, labelling any shown ones "nicht fachlich geeignet —
  übersprungen" (with `meta.specialty_fit_reason`).
- **No false department claims.** On `suitable`, the email/sequence may reference only a
  facility department the employee's specializations actually cover (guided by
  `meta.specialty_fit_reason`); on `unknown`/absent the pitch stays general. A subject like
  "Intensivfachkraft für Ihre Neonatologie verfügbar" for a non-paediatric nurse is now
  explicitly forbidden.
- Same two rules applied to `match-bench-to-clients` (match list), `prospect-companies`
  (lead qualification), and `enroll-outreach` (before enrollment + attached-profile copy).

### Notes
- `specialty_fit` is exposed by the MCP as a top-level field on 0-126 (returned by
  `get-model`/`query-model`); `specialty_fit_reason` lives in `meta`. It is **not** in the
  0-126 FilterSchema, so the gate reads each record and excludes `conflict` in-memory —
  a backend follow-up could add an `EnumFilterField` for server-side filtering.

## [0.5.0] — 2026-06 *(entry backfilled)*

### Changed
- `manage-meta-ads`: documented the real root cause of "Meta tools aren't
  available" (a `tools/list` pagination cutoff, not a dead connection) and
  strengthened the skill's trigger phrases.

## [0.4.1] — 2026-06 *(entry backfilled)*

### Added
- `manage-meta-ads` — Meta (Facebook/Instagram) recruiting/lead campaigns for
  alluvo tenants: campaigns, ad sets, creatives, native Lead Ads (instant
  forms), conversion/optimization events, UTM scheme, and performance review —
  including the EMPLOYMENT special-ad-category and AGG "(m/w/d)" hard rules.

## [0.4.0] — 2026-06-15

Profilvertrieb / bench hardening from a live two-mode test run (preview-only) on a
real tenant — the workflow now ranks, qualifies, and signs off correctly instead of
trusting misleading inputs.

### Changed
- **Profilvertrieb ranks matches by forecasted revenue (EUR), not score.** In real
  tenants the match `score` is empty across every opportunity, so the old "sort by
  score" surfaced nothing useful. Matches are now ranked by `forecasted_revenue`, with
  score treated as an optional secondary signal.
- **Email targets now require a contact.** Most opportunities have no recommended
  contact (no addressee). Profilvertrieb now requires a contact for email outreach and
  falls back to resolving a company contact when the match has none — instead of
  drafting an email to nobody.
- **Bench inputs are filtered before anyone is marketed.** Inactive (`is_active=false`)
  and already-booked (`forecast_status=booked`) employees are excluded/flagged in both
  Profilvertrieb Step 1 and `bench-check`, so you never pitch someone who is placed or
  off the roster.
- **Availability is read from the real source of truth.** Both skills now derive free
  days from the availability block / calendar (and home city from the current location)
  rather than the bench summary, which can report "0 free days / no city" for people who
  are genuinely available.

### Added
- **Duplicate-aware qualification before cold outreach.** Before pitching a `new`
  company, Profilvertrieb (and the `prospect-companies` / `enroll-outreach` cross-refs)
  now check for sibling/duplicate records of the same site (same name root, parent-child,
  or shared address) — a `new` record can be a duplicate of one already in an open deal,
  and the skill now warns and routes to merge instead of cold-pitching into a live deal.
- **Mode B (Türöffner) enrichment check.** When the profile itself is the hook, the
  skill now warns if the employee's `bio` is empty and suggests enriching the profile
  before sending a profile-led email.
- **Sender-derived email sign-off.** The closing is now taken from the actual sender
  (authenticated user / sender) instead of a hardcoded name, preventing mismatched
  sign-offs.

## [0.3.3] — 2026-06-14

### Changed
- Brand is lowercase **alluvo** — lowercased the "Alluvo" brand token across all
  skill prose, README, and metadata (no behavior change; tool namespace
  `mcp__alluvo__*` and the `alluvo` connector key were already lowercase).

## [0.3.2] — 2026-06-14

### Fixed
- **Bundled MCP server URL** corrected from `api.alluvo.com` (does not resolve) to
  **`api.alluvo.ai`** — the production host. Fixes the "Verbindung fehlgeschlagen"
  OAuth failure when connecting the `alluvo` connector via the plugin.

## [0.3.1] — 2026-06-14

### Added
- **Bundled alluvo MCP server** — the plugin now ships a `.mcp.json` declaring the
  `alluvo` server at `https://api.alluvo.ai/mcp` (HTTP + OAuth). Installing the
  plugin wires up the MCP connection; users authenticate via OAuth and pick their
  organization on first use, instead of connecting the MCP manually.

### Changed
- `plugin.json` description: fixed SDR → BDR and reflects the English-first switch
  + bundled MCP. README install/prerequisites updated for the OAuth-on-install flow.

## [0.3.0] — 2026-06-14

### Added
- `head-of-sales` — Vertriebsleitung: pipeline / forecast / pipeline-review
  reporting and BDR coordination (assign work via `owner_id`). Folds in the
  forecast and pipeline-review concepts from the knowledge-work `sales` plugin,
  rebuilt German + MCP-only.
- `head-of-disposition` — Dispositionsleitung: utilization / expiring-assignment /
  open-demand reporting and Disponent coordination.
- `account-research`, `call-prep`, `call-summary`, `daily-briefing` — German,
  internal-data-only adaptations of the knowledge-work `sales` skills.

### Changed
- Renamed `prospect-nearby-companies` → `prospect-companies` (geo is one filter
  among ICP + signals).
- Rewrote the `using-alluvo-operator` dispatcher into a two-tier role map.
- Terminology: SDR → BDR throughout.
- Switched all operator-facing prose and section headers to **English-first**;
  `description:` triggers retain the German industry terms (verleihfrei,
  Personalbedarf, Dienstplan, Profilvertrieb, AÜG, …) so German-typed requests
  still activate the right skill.

## [0.2.0] — 2026-06-14

### Added
- `using-alluvo-operator` — dispatcher / "start here" skill that catalogs every
  workflow by category and routes the operator to the right one.
- `enrich-contacts-from-activities` — enrich sparse Contact records by mining
  their own emails / calls / meetings / notes (especially email signatures);
  review-first, writes attributed via MCP. Includes `references/` notes
  (extraction patterns, MCP recipes).

## [0.1.0] — 2026-06-13

### Added
- Initial release: 15 German-first operator workflows across staffing &
  placement, sales & outreach, ops & compliance, and data quality —
  `bench-check`, `match-bench-to-clients`, `onboard-new-employee`,
  `profilvertrieb`, `prospect-nearby-companies`, `intake-personalbedarf`,
  `manage-contract-lifecycle`, `build-dienstplan`, `record-absence`,
  `approve-stundenfreigabe`, `define-icp`, `enroll-outreach`,
  `log-company-signal`, `triage-data-quality`, `merge-duplicate-companies`.
