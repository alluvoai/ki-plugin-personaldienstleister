---
name: export-labor-market-data
description: 'Export a CSV of mirrored Bundesagentur vacancies, hiring employers, or AÜG permit holders only when the operator explicitly requests a file or download. Use for "Agentur-für-Arbeit-Daten als CSV", "BA-Stellenmarkt exportieren", "Arbeitgeberliste herunterladen", "Erlaubnisinhaber exportieren" or "Jobsuche-Daten herunterladen". Requests to show vacancies or advertised professions belong to lead-radar-prospecting. A generic request for Excel or CSV without a BA dataset does not select this workflow.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "export-labor-market-data"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
