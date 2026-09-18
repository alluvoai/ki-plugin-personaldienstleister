---
name: manage-inbox
description: 'Triage tickets in a shared alluvo inbox and manage forwarding, business hours, notifications, spam, and phone-assistant instructions. Use for "Inbox aufräumen", "Tickets bearbeiten", "Ticket weiterleiten", "Ticket verschieben", "Geschäftszeiten ändern", "neuen Vorgang öffnen" or "als Spam melden". Writing an employee directly is message-employee; their app access is onboard-new-employee. German triggers also include: neuer Vorgang.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-inbox"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
