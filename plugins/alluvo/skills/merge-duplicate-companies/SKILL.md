---
name: merge-duplicate-companies
description: Find, preview, and merge duplicate company or contact records (Dubletten). Use when the operator says "Dubletten bereinigen", "doppelte Firmen zusammenführen", "doppelte Kontakte zusammenführen", "Kontakt-Dublette", "merge duplicate companies", "merge duplicate contacts", "find duplicate records", "Standorte unter Muttergesellschaft gruppieren", or wants to clean up duplicate or fragmented company or contact records in alluvo — including the follow-up to a POSSIBLE DUPLICATE warning shown when a record was created.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "merge-duplicate-companies"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
