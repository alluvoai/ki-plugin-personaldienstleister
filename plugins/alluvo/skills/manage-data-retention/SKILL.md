---
name: manage-data-retention
description: 'Löschliste, fällige Löschungen, Löschsperre, Bewerber löschen — deletion list: due steps, holds, consents, two-stage erasure.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-data-retention"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
