---
name: manage-contract-lifecycle
description: Create and manage framework and assignment contracts, transition their stages, send the §11 AÜG notification, set billing periods, and manage invoice bank accounts. Use for "Rahmenvertrag anlegen", "Einsatzvertrag erstellen", "AÜV abschließen", "Vertrag stornieren", "Abrechnungszeitraum ändern" or "Rechnungskonto anlegen".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-contract-lifecycle"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
