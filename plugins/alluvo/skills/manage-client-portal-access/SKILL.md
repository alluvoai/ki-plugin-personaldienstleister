---
name: manage-client-portal-access
description: 'Give a client contact access to the Kundenportal, set what they may do there, read who can log in, and take access away again. Use for "Kundenportal-Zugang", "Portal-Zugang einrichten", "Kunde soll Stunden im Portal freigeben", "Portal-Einladung schicken", "Portalzugang entziehen", "wer hat Portalzugang bei Firma X" or "Portalrolle ändern". Approving hours is manage-timesheet-approvals; contract signing is manage-contract-lifecycle. German triggers also include: Ansprechpartner freischalten, Portal-Rolle, Einladung ins Portal.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-client-portal-access"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
