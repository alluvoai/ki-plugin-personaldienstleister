---
name: manage-reimbursements
description: File, reconcile and review an employee's Belege, Auslagen and Reisekosten — including filing a receipt on the employee's behalf (from a photo, a PDF or a ticket attachment), matching a pile of new receipts against what is already submitted, telling a real Beleg from a PayPal or bank payment confirmation, rejecting duplicates with a reason, requesting a correction, approving, marking as paid, and the Sammel-Reisekostenabrechnung. Use when the operator says "Belege von X ansehen", "Beleg für Mitarbeiter einreichen", "Belege abgleichen", "doppelt eingereicht", "PayPal-Screenshot ist kein Beleg", "Auslage ablehnen", "Korrektur beantragen", "Spesen freigeben", "Reisekosten prüfen", "als bezahlt markieren", "Sammel-Reisekostenabrechnung", "Wegstreckenpauschale", "file a receipt for an employee", "review expenses", "reject a duplicate receipt", or hands over receipt photos or a ticket with receipts attached.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-reimbursements"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
