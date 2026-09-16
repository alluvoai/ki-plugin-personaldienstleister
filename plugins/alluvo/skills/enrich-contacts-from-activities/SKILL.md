---
name: enrich-contacts-from-activities
description: 'Enrich contact records from recent emails, signatures, calls, meetings, and notes, always proposing changes before writing them. Also record external WhatsApp consent and the contact''s du/Sie form. Use for "Kontakte anreichern", "Kontaktdaten aus Aktivitäten", "WhatsApp-Einwilligung erfassen", "Opt-in hinterlegen" or "Anrede festlegen". German triggers also include: E-Mail-Signatur auslesen.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "enrich-contacts-from-activities"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
