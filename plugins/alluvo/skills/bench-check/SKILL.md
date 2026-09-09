---
name: bench-check
description: Identify employees who are verleihfrei (unassigned) now or about to become verleihfrei, ranked by urgency. Use when the operator asks "wer ist verleihfrei", "check the bench", "wer hat keinen Einsatz", "find unassigned employees", "wessen Einsatz läuft aus", or wants a workforce-availability overview.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "bench-check"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
