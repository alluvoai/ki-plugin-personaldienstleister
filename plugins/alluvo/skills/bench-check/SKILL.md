---
name: bench-check
description: 'wer ist verleihfrei, Bank prüfen, wer hat keinen Einsatz, wessen Einsatz läuft aus, freie Mitarbeiter — who is unassigned now or soon, by urgency.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "bench-check"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
