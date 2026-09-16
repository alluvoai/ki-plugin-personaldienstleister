---
name: arbeitsmarkt-export
description: Export Bundesagentur Arbeitsmarkt data as CSV — open positions from the Lead-Radar job search, employers found in it, or slices of the AÜG Erlaubnisregister — for use outside alluvo. Use when the operator says "Stellen exportieren", "Arbeitgeber als CSV", "Erlaubnisregister exportieren", "Export aus dem Lead-Radar", "CSV der offenen Stellen", or wants Bundesagentur job-market or permit-register data exported.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "arbeitsmarkt-export"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
