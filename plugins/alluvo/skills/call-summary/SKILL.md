---
name: call-summary
description: Capture and process call notes — structure raw notes or a transcript, save as a Call/Note in the CRM, create Action Items as tasks, and draft a follow-up email. Always writes with preview first. Use this skill when the operator says "Gesprächsnotiz erfassen", "Call nachbereiten", "fasse das Gespräch zusammen", "Notizen vom Telefonat", "log this call", "call summary", "summarize my call", or "write the follow-up".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "call-summary"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
