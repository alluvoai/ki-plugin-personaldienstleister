# alluvo – KI-Plugin für Personaldienstleister (Claude, Codex)

🇬🇧 **English version: [README.en.md](README.en.md)**

**alluvo** ist das KI-Plugin für Personaldienstleister und Zeitarbeitsfirmen. Es macht aus Claude und Codex einen Assistenten, der Disposition, Recruiting, Vertrieb, Verträge, Dienstplan und Stundenfreigabe per Sprache erledigt: direkt in Ihren alluvo-Daten, mit Vorschau vor jedem Schreibzugriff und mit den Prüfungen nach AÜG und ArbZG, die die Branche braucht.

## Für wen

- **Disponent:innen** – wer ist verleihfrei, wer passt zu welchem Kundenbedarf, Dienstpläne, Krankmeldungen, Stundenfreigabe.
- **Recruiter:innen und Personalabteilung** – Onboarding neuer Mitarbeiter, Personalfragebogen, Stammdaten, Einladung in die Mitarbeiter-App.
- **Vertrieb und BDR** – Profilvertrieb, Zielfirmen im Umkreis, Outreach-Sequenzen, Gesprächsvorbereitung und -nachbereitung.
- **Geschäftsführung und Teamleitung** – Tagesbriefing, Dispo- und Vertriebsübersicht, Aufgabenverteilung.

## Was Sie sagen können

Die Workflows starten auf natürliche Sätze, Deutsch oder Englisch:

| Sie sagen … | alluvo macht … |
|---|---|
| „Wer ist gerade verleihfrei?" | listet Mitarbeiter ohne Einsatz, nach Dringlichkeit, mit Wohnort und Qualifikation |
| „Finde Einsätze für die Bank" | matcht verleihfreie Mitarbeiter auf Kunden mit Rahmenvertrag und legt Einsatzvertragsentwürfe an |
| „Verkauf mir den Kandidaten Max Mustermann" | sucht passende Firmen im Umkreis, qualifiziert sie und startet die Outreach-Sequenz |
| „Neuer Personalbedarf von Klinikum Musterstadt" | erfasst die Anfrage vollständig und schlägt Kandidaten vor |
| „Dienstplan für Oktober erstellen" | plant die Schichten mit ArbZG-Prüfung und veröffentlicht sie |
| „Krankmeldung für Frau Beispiel ab Montag" | bucht die Abwesenheit und legt die AU in die Personalakte |
| „Stundenfreigabe prüfen" | zeigt eingereichte Stunden, Abweichungen und offene Kundenfreigaben |
| „Rahmenvertrag für die Pflegedienst GmbH anlegen" | erstellt den Vertrag, führt durch die Stufen und verschickt die §11-AÜG-Mitteilung |
| „Was steht heute an?" | Tagesbriefing aus Terminen, Aufgaben, Outreach-Antworten und Pipeline |
| „Inbox aufräumen" | triagiert das Team-Postfach, schließt mit Beleg, legt Folgeaufgaben an |

## Alle Workflows

| Bereich | Workflows |
|---|---|
| Disposition | `bench-check`, `match-bench-to-clients`, `intake-personalbedarf`, `build-dienstplan`, `record-absence`, `approve-stundenfreigabe`, `head-of-disposition` |
| Verträge | `manage-contract-lifecycle` |
| Recruiting und Personal | `onboard-new-employee`, `manage-meta-ads` |
| Vertrieb | `profilvertrieb`, `prospect-companies`, `enroll-outreach`, `define-icp`, `account-research`, `call-prep`, `call-summary`, `log-company-signal`, `head-of-sales` |
| Service und Datenqualität | `clean-inbox`, `triage-data-quality`, `merge-duplicate-companies`, `enrich-contacts-from-activities` |
| Automatisierung und Überblick | `build-automation-agent`, `daily-briefing`, `using-alluvo-operator` |
| Frei (ohne Konto) | `stellenanzeige` |

Die Auslöse-Sätze jedes Workflows stehen im [Katalog](plugins/alluvo/README.md). Jeder Workflow lässt sich auch direkt starten, zum Beispiel mit `/alluvo:bench-check`.

## Installation

### Claude Code

1. Marketplace hinzufügen (einmal pro Rechner):
   ```
   /plugin marketplace add alluvoai/ki-plugin-personaldienstleister
   ```
   Ohne GitHub geht es genauso — alluvo hostet denselben Marketplace selbst:
   `/plugin marketplace add https://api.alluvo.ai/plugins/marketplace.json`
2. Plugin installieren:
   ```
   /plugin install alluvo@alluvoai
   ```
3. Assistenten verbinden. Das Plugin bringt den alluvo-MCP-Server mit; beim ersten Aufruf fragt Claude Code nach der Anmeldung. Sie können sie auch selbst starten:
   ```
   /mcp
   ```
   **alluvo** auswählen, im Browser mit den alluvo-Zugangsdaten anmelden und die Organisation wählen.
4. Ausprobieren: „Wer ist gerade verleihfrei?"

Aktualisieren: `/plugin marketplace update alluvoai`, danach `/plugin update alluvo@alluvoai`. Die Workflow-Anleitungen selbst liefert der Assistent zur Laufzeit; dafür ist kein Plugin-Update nötig.

### Claude Cowork

**Empfohlen: den Assistenten organisationsweit verbinden.** Ein Owner Ihrer Claude-Organisation trägt unter **Organisationseinstellungen → Connectors** einen eigenen Connector mit der Adresse `https://api.alluvo.ai/mcp` ein. Mitglieder melden sich einmalig an; danach starten alle Arbeitsabläufe auch ohne Plugin, weil der alluvo-Server sie liefert.

**Das Plugin selbst geht in Cowork nur über GitHub-Sync einer eigenen Kopie.** Dieses Repository ist eine GitHub-Vorlage:

1. **„Use this template"** wählen und eine private Kopie in der GitHub-Organisation des Kunden anlegen.
2. Die **Claude GitHub App** in dieser Organisation installieren und der Kopie Zugriff geben.
3. In Cowork **Sync from GitHub** auf diese Kopie zeigen lassen.
4. Beim ersten Aufruf fragt der Assistent nach der alluvo-Anmeldung (OAuth) und der Organisation.

### Codex

1. Marketplace hinzufügen:
   ```
   codex plugin marketplace add alluvoai/ki-plugin-personaldienstleister
   ```
2. Plugin installieren:
   ```
   codex plugin add alluvo@alluvoai
   ```
3. Am mitgelieferten Assistenten anmelden:
   ```
   codex mcp login alluvo
   ```
   Falls der mitgelieferte Server nicht übernommen wird, einmalig von Hand eintragen und danach anmelden: `codex mcp add alluvo --url https://api.alluvo.ai/mcp`

### Ohne Plugin

Jeder MCP-Client kann sich direkt mit dem alluvo-Assistenten verbinden; das Plugin ergänzt nur die geführten Workflows. Claude Desktop, claude.ai und andere Clients nutzen die Connector-URL `https://api.alluvo.ai/mcp`. Details, auch der Weg über ein persönliches Zugriffstoken: [Assistenten verbinden](https://docs.alluvo.ai/de/alluvo-mcp/connect).

## Sicherheit und Compliance

- **Ihre Daten bleiben bei Ihnen.** Das Plugin enthält keine Daten und keine Anleitungen, nur die Auslöse-Sätze. Alles Weitere liefert der alluvo-Server zur Laufzeit, nach Anmeldung, im Rahmen Ihrer Berechtigungen und nur für Ihre Organisation.
- **Vorschau vor jedem Schreibzugriff.** Kein Vertrag, keine Schicht, kein Kontakt wird angelegt oder geändert, ohne dass Sie die Vorschau bestätigt haben.
- **AÜG und ArbZG eingebaut.** Dienstpläne werden gegen Höchstarbeitszeit, Ruhezeiten und Sonntagsarbeit geprüft; Überlassungshöchstdauer, Equal Pay und die §11-Mitteilung sind Teil des Vertrags-Workflows.
- **Tarifgrenzen sind sichtbar.** Ein Workflow außerhalb Ihres alluvo-Tarifs antwortet mit `MODULE_LOCKED`, nennt den nötigen Tarif und verlinkt die Testphase.

## Fehlerbehebung

| Symptom | Was tun |
|---|---|
| `alluvo … Needs authentication` unter `/mcp` | Über `/mcp` → alluvo anmelden. Tokens laufen ab; eine erneute Anmeldung behebt es. |
| Ein Workflow startet nicht | Die Auslöse-Formulierung aus dem Katalog verwenden oder den Workflow direkt starten: `/alluvo:bench-check`. |
| `MODULE_LOCKED` | Der Workflow gehört zu einem Modul, das Ihre Organisation nicht freigeschaltet hat. Die Meldung nennt den Tarif und verlinkt die Testphase. |

## Über alluvo

alluvo ist die Software für Personaldienstleister: Mitarbeiter, Kunden, Verträge, Dienstplanung, Zeiterfassung, Abrechnung und Vertrieb in einem System, mit KI-Assistent und Mitarbeiter-App. Mehr unter [alluvo.de](https://alluvo.de), Dokumentation unter [docs.alluvo.ai](https://docs.alluvo.ai/de).

Support: Ihr alluvo-Ansprechpartner.
