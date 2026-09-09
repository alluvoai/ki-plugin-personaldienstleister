---
name: triage-data-quality
description: Review, prioritize, and resolve data quality problems (Datenqualität) after an import or as a regular quality routine, including Rollenkatalog hygiene (Rollen ohne Gruppe/Level/Fachweiterbildung). Use when the operator says "Datenqualität prüfen", "Issues triagieren", "nach Import aufräumen", "check data quality", "triage issues", "bulk-resolve issues", "Rollenkatalog aufräumen", "Rollen ohne Level", "Rollen ohne Fachweiterbildung", "Fachweiterbildung setzen", "Rollen-Hierarchie pflegen", "Profil aufräumen", "Berufsstation ausblenden", or wants a structured review of data quality findings. For merging duplicate companies specifically, use merge-duplicate-companies.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "triage-data-quality"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
