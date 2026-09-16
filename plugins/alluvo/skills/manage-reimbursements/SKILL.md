---
name: manage-reimbursements
description: 'File, reconcile, review, approve, reject, correct, and pay employee receipts, expenses, and travel costs, including bulk travel-expense statements. Use for "Beleg einreichen", "Belege abgleichen", "doppelt eingereicht", "Auslage ablehnen", "Spesen freigeben", "Reisekosten prüfen", "als bezahlt markieren" or "Sammel-Reisekostenabrechnung". German triggers also include: Sammelabrechnung.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-reimbursements"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
