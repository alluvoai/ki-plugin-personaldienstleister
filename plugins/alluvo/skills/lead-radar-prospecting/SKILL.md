---
name: lead-radar-prospecting
description: 'Find employers advertising vacancies in mirrored Bundesagentur für Arbeit / Jobsuche data; inspect positions and synchronize employers, job postings and identified contacts into the CRM; export a CSV only on an explicit file request. Use for "Lead-Radar", "Agentur für Arbeit Daten", "wer sucht Pflegekräfte", "welche Firmen stellen ein", "offene Stellen im Umkreis", "ins CRM übernehmen", or — only when a file is asked for — "BA-Stellenmarkt exportieren", "Arbeitgeberliste herunterladen", "Erlaubnisinhaber exportieren", "Jobsuche-Daten herunterladen". Use research-staffing-agencies for reading AÜG permit holders. German triggers also include: Bundesagentur Jobsuche, welche Berufe werden gesucht, Arbeitgeberbedarf.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "lead-radar-prospecting"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
