---
name: merge-duplicate-records
description: 'Find, preview, and merge duplicate company or contact records, including follow-up to a possible-duplicate warning. Use for "Dubletten bereinigen", "doppelte Firmen zusammenführen", "doppelte Kontakte zusammenführen", "Kontakt-Dublette" or "Standorte unter Muttergesellschaft gruppieren". German triggers also include: Standorte gruppieren.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "merge-duplicate-records"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
