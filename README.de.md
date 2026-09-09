# alluvo Claude Plugins

🇬🇧 **English version: [README.md](README.md)**

Der offizielle Claude-Plugin-Marketplace von alluvo. Er enthält das Plugin **alluvo**: geführte Workflows für Disposition, Recruiting und Vertrieb auf Basis des alluvo-Assistenten, des alluvo-MCP-Servers.

## Voraussetzungen

- Ein alluvo-Konto in Ihrer Organisation.
- [Claude Code](https://claude.com/claude-code) (Terminal, Desktop-App oder IDE-Erweiterung), Claude Cowork oder Codex.
- Netzwerkzugriff auf `https://api.alluvo.ai/mcp`. Der Assistent verbindet sich beim ersten Aufruf per OAuth; es wird nirgends ein Token kopiert.

## Installation in Claude Code

1. Marketplace hinzufügen (einmal pro Rechner):
   ```
   /plugin marketplace add alluvoai/alluvo-claude-plugins
   ```
2. Plugin installieren:
   ```
   /plugin install alluvo@alluvoai
   ```
3. Assistenten verbinden. Das Plugin bringt den alluvo-MCP-Server mit; beim ersten Aufruf fragt Claude Code nach der Anmeldung. Sie können sie auch selbst starten:
   ```
   /mcp
   ```
   **alluvo** auswählen, im Browser mit den alluvo-Zugangsdaten anmelden und die Organisation wählen.
4. Ausprobieren:
   > Wer ist gerade verleihfrei?

   Der Workflow `bench-check` startet, und der Assistent antwortet aus den Daten Ihrer Organisation.

**Aktualisieren:** `/plugin marketplace update alluvoai`, danach `/plugin update alluvo@alluvoai`. Die Workflow-Anleitungen selbst liefert der Assistent zur Laufzeit; dafür ist kein Plugin-Update nötig.

## Installation in Claude Cowork

1. Ein Administrator Ihrer Claude-Organisation öffnet **Organisationseinstellungen → Plugins → Plugin hinzufügen → GitHub** und wählt dieses Repository.
2. Mitglieder aktivieren **alluvo** in ihrer Plugin-Liste.
3. Beim ersten Aufruf fragt der Assistent nach der alluvo-Anmeldung (OAuth) und der Organisation.

## Installation in Codex

1. Marketplace hinzufügen (einmal pro Rechner):
   ```
   codex plugin marketplace add alluvoai/alluvo-claude-plugins
   ```
2. Plugin installieren:
   ```
   codex plugin add alluvo@alluvoai
   ```
3. Am mitgelieferten Assistenten anmelden:
   ```
   codex mcp login alluvo
   ```
   Falls der mitgelieferte Server nicht übernommen wird, einmalig von Hand eintragen und danach anmelden:
   ```
   codex mcp add alluvo --url https://api.alluvo.ai/mcp
   ```

## Assistent ohne Plugin nutzen

Jeder MCP-Client kann sich direkt verbinden; das Plugin ergänzt nur die geführten Workflows. Claude Desktop, claude.ai und andere Clients nutzen die Connector-URL `https://api.alluvo.ai/mcp`. Details, auch der Weg über ein persönliches Zugriffstoken für Clients ohne OAuth, stehen in der Dokumentation: [Assistenten verbinden](https://docs.alluvo.ai/de/alluvo-mcp/connect).

## Was das Plugin kann

Die Workflows starten auf natürliche Sätze wie „Wer ist gerade verleihfrei?", „Leg einen Rahmenvertrag für … an" oder „Verkauf mir den Kandidaten …". Der Katalog steht in [`plugins/alluvo/README.md`](plugins/alluvo/README.md).

Die Schritt-für-Schritt-Anleitung zu jedem Workflow liefert der alluvo-Assistent zur Laufzeit. Sie ist damit immer aktuell und richtet sich nach dem Tarif Ihrer Organisation. Ein Workflow außerhalb Ihres Tarifs antwortet mit `MODULE_LOCKED`, nennt den nötigen Tarif und verlinkt die Testphase.

## Fehlerbehebung

| Symptom | Was tun |
|---|---|
| `alluvo … Needs authentication` unter `/mcp` | Über `/mcp` → alluvo anmelden. Tokens laufen ab; eine erneute Anmeldung behebt es. |
| Ein Workflow startet nicht | Die deutsche oder englische Auslöse-Formulierung aus dem Katalog verwenden oder den Workflow direkt starten: `/alluvo:bench-check`. |
| `MODULE_LOCKED` | Der Workflow gehört zu einem Modul, das Ihre Organisation nicht freigeschaltet hat. Die Meldung nennt den Tarif und verlinkt die Testphase. |

## Support

Ihr alluvo-Ansprechpartner oder die Dokumentation unter [docs.alluvo.ai](https://docs.alluvo.ai/de/alluvo-mcp/connect).
