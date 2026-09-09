---
name: manage-contract-lifecycle
description: Create a Rahmenvertrag and Einsatzvertrag, transition them through stages, and send the §11 AÜG notification. Use when the operator says "Rahmenvertrag anlegen", "Einsatzvertrag erstellen", "AÜV abschließen", "Vertrag auf Won setzen", "§11 AÜG Benachrichtigung", "Vertrag stornieren", "Storno", "Vertrag als verloren markieren", "create framework contract", "create assignment contract", or wants to manage the full staffing contract lifecycle. Also covers the billing period on a contract ("Abrechnungszeitraum setzen", "Abrechnungszeitraum ändern", "Rechnungsstellung", "halbmonatlich abrechnen", "monatlich abrechnen", "billing period", "billing frequency"). Also covers the tenant's own invoicing bank accounts ("Bankkonto für Rechnungen", "Rechnungskonto anlegen", "auf welches Konto zahlt der Kunde", "Bankverbindung der Agentur", "Standardkonto für Rechnungen", "invoice bank account", "payee account").
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-contract-lifecycle"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
