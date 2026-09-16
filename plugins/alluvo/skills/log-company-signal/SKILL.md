---
name: log-company-signal
description: Record a hiring, expansion, funding, product launch, partnership, or leadership-change signal on a company. Use for "Signal loggen", "Firma stellt gerade ein", "Neueröffnung", "neuer Standort", "Finanzierungsrunde" or "neue PDL". German triggers also include: Firma stellt ein, Führungswechsel.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "log-company-signal"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
