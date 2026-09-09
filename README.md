# alluvo Claude Plugins

Der offizielle Claude-Plugin-Marketplace von alluvo. Er enthält das Plugin **alluvo-operator**: geführte Workflows für Disponent:innen, Recruiter:innen und Vertrieb auf Basis des alluvo-Assistenten (MCP-Server).

## Voraussetzungen

- Ein alluvo-Konto in Ihrer Organisation. Der Assistent verbindet sich beim ersten Aufruf per OAuth mit `https://api.alluvo.ai/mcp`; Sie melden sich mit Ihren alluvo-Zugangsdaten an und wählen Ihre Organisation.
- Claude Code oder Claude Cowork.

## Installation

**Claude Code**

```
/plugin marketplace add alluvoai/alluvo-claude-plugins
/plugin install alluvo-operator@alluvo-marketplace
```

**Claude Cowork**

Organisationseinstellungen → Plugins → Plugin hinzufügen → GitHub → dieses Repository auswählen. Danach steht das Plugin allen Mitgliedern der Claude-Organisation zur Verfügung.

## Was das Plugin kann

Die Workflows starten auf natürliche Sätze wie „Wer ist gerade verleihfrei?", „Leg einen Rahmenvertrag für … an" oder „Verkauf mir den Kandidaten …". Der Katalog steht in [`plugins/alluvo-operator/README.md`](plugins/alluvo-operator/README.md).

Die Anleitung zu jedem Workflow liefert der alluvo-Assistent zur Laufzeit. Sie ist damit immer aktuell und richtet sich nach dem Tarif Ihrer Organisation.

---

# alluvo Claude Plugins (English)

The official alluvo Claude plugin marketplace. It ships the **alluvo-operator** plugin: guided workflows for dispatchers, recruiters and sales on top of the alluvo assistant (MCP server).

## Prerequisites

- An alluvo account in your organisation. The assistant connects via OAuth to `https://api.alluvo.ai/mcp` on first use; sign in with your alluvo credentials and pick your organisation.
- Claude Code or Claude Cowork.

## Install

**Claude Code**

```
/plugin marketplace add alluvoai/alluvo-claude-plugins
/plugin install alluvo-operator@alluvo-marketplace
```

**Claude Cowork**

Organisation settings → Plugins → Add plugin → GitHub → select this repository. The plugin then becomes available to every member of the Claude organisation.

## What the plugin does

Workflows activate on natural phrases such as "wer ist verleihfrei", "create a framework contract for …" or "sell this profile". The catalogue is in [`plugins/alluvo-operator/README.md`](plugins/alluvo-operator/README.md).

The guidance for each workflow is served live by the alluvo assistant, so it is always current and follows your organisation's plan.
