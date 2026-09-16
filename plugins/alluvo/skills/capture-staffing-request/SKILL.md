---
name: capture-staffing-request
description: 'Capture a client''s staffing request end to end and maintain the client''s departments when required. Use for "neuer Personalbedarf", "Anfrage aufnehmen", "Kundenbedarf erfassen", "Stelle anlegen", "Bedarf von Kunde X", "Abteilung archivieren" or "Station stilllegen". When the operator supplies call notes to record or process, start with process-call-notes, even when the notes mention a staffing need; hand off here when a staffing-request record is requested.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "capture-staffing-request"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
