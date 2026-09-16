---
name: bench-check
description: Identify employees who are verleihfrei now or will soon become available, ranked by urgency. Use for "wer ist verleihfrei", "wer hat keinen Einsatz", "wessen Einsatz läuft aus" or "Bank prüfen". This workflow reports availability; use match-bench-to-clients to match the bench to existing clients and market-talent-profiles for end-to-end profile marketing. German triggers also include: freie Mitarbeiter.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "bench-check"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
