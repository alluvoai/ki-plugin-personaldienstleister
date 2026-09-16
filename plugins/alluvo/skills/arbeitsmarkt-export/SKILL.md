---
name: arbeitsmarkt-export
description: Build a CSV of the Bundesagentur data alluvo mirrors — open positions, hiring employers or the AÜG permit register — through alluvo's export engine, and say where to download it. Use when the operator says "als CSV", "exportieren", "Liste runterladen", "in Excel", or "Export der Erlaubnisinhaber". Not for reading the data — that is the Lead-Radar itself.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "arbeitsmarkt-export"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
