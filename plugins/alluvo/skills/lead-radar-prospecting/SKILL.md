---
name: lead-radar-prospecting
description: Find employers currently advertising vacancies in mirrored Bundesagentur für Arbeit / Jobsuche data by role, place, and radius; inspect positions and import promising employers and named contacts into the CRM. Use for "Lead-Radar", "Agentur für Arbeit Daten", "wer sucht Pflegekräfte", "welche Firmen stellen ein", "offene Stellen im Umkreis" or "Arbeitgeber mit Personalbedarf". Use research-staffing-agencies for AÜG permit holders and export-labor-market-data for an explicit BA dataset export. German triggers also include: Bundesagentur Jobsuche, welche Berufe werden gesucht, Arbeitgeberbedarf.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "lead-radar-prospecting"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
