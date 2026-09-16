---
name: triage-data-quality
description: 'Review, prioritize, and resolve data-quality findings after an import or during routine maintenance, including role-catalogue hygiene. Use for "Datenqualität prüfen", "Issues triagieren", "nach Import aufräumen", "Rollenkatalog aufräumen", "Rollen ohne Level", "Fachweiterbildung setzen" or "Profil aufräumen". Use merge-duplicate-records for company or contact duplicates.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "triage-data-quality"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
