---
name: manage-receivables
description: Offene Posten einer Rechnung bearbeiten — Zahlung erfassen, Teilzahlung, Skonto, Restbetrag ausbuchen, Erstattung erfassen, Gutschrift erstellen, Zahlungsziel verlängern, Mahnverfahren eröffnen und Mahnstufen versenden; dazu der Rechnungslauf selbst (freigeben, stellen, stornieren, E-Rechnung exportieren). Nutze dies, wenn der Operator sagt "Zahlung erfassen", "Rechnung ist bezahlt", "offene Posten", "was schuldet der Kunde noch", "Gutschrift erstellen", "Mahnung schicken", "Zahlungsziel verlängern", "Rechnung stornieren", "Rechnung versenden", "record a payment", "mark this invoice paid", "which invoices are open", "issue a credit note", "send a dunning letter", "Erstattung erfassen", "Überzahlung zurückzahlen", "record a refund" oder "extend the due date".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-receivables"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
