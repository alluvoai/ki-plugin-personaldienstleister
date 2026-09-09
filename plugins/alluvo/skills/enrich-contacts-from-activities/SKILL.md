---
name: enrich-contacts-from-activities
description: Enrich alluvo Contacts (Kontakte anreichern) by mining their recent activity — emails, logged calls, meetings, notes, above all email signatures — for missing contact-info fields, then writing approved changes back through MCP so every edit is attributed to the operator. Review-first: always proposes a change table before writing. Also covers recording a WhatsApp consent given outside alluvo and pinning the du/Sie form for a contact. Use when the operator says "Kontakte anreichern", "Kontaktdaten aus Aktivitäten befüllen", "WhatsApp-Einwilligung erfassen", "Opt-in für WhatsApp hinterlegen", "Anrede festlegen", "diesen Kontakt duze ich", "enrich contacts", "fill in contact details from their emails", "pull phone numbers or LinkedIn from email signatures", "update contacts from recent activity", "record a WhatsApp opt-in", "set the formality for this contact", or wants sparse Contact records cleaned up from communication history.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "enrich-contacts-from-activities"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
