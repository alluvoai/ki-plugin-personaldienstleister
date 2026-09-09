---
name: intake-personalbedarf
description: Capture a client staffing requirement (Personalbedarf) end-to-end. Use when the operator says "neuer Personalbedarf", "Anfrage aufnehmen", "Kundenbedarf erfassen", "intake staffing requirement", "Stelle anlegen", "Bedarf von Kunde X", or when a client calls with a new placement request. Also covers maintaining the client's Abteilungen ("Abteilung archivieren", "Station stilllegen", "Abteilung lässt sich nicht löschen", "Wohnbereich aus dem Portal nehmen", "archivierte Abteilung wiederherstellen", "archive a department").
---

Call the MCP tool `get-workflow-guidance` with `workflow: "intake-personalbedarf"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
