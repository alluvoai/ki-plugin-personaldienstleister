---
name: check-out-session
description: 'Hand the current AI session over to the alluvo developers for debugging — register a session checkout with triage metadata, upload the raw transcript, link it to a feedback item. Use for "check out this session", "session checkout", "export this session", "submit session feedback with full context", "Session an die Entwickler übergeben", "Session auschecken", "Session exportieren", "Session-Checkout", "Konversation an alluvo schicken" or after filing a bug report when the developers need the full conversation.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "check-out-session"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
