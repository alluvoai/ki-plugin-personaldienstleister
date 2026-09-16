---
name: manage-invoices-and-payments
description: Manage invoice runs and receivables: issue, send, cancel, and export e-invoices; record payments, discounts, write-offs, refunds, and credit notes; extend due dates and run dunning. Use for "Zahlung erfassen", "offene Posten", "Gutschrift erstellen", "Mahnung schicken", "Rechnung stornieren", "E-Rechnung exportieren", "Erstattung erfassen" or "Zahlungsziel verlängern".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-invoices-and-payments"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
