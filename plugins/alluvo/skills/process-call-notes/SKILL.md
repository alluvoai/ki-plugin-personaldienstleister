---
name: process-call-notes
description: 'Structure supplied call notes, a transcript or a plain note, save the activity in the CRM, create follow-up tasks, and draft a follow-up email with a preview before every write. This is the entry point for every logged call and note — also when their content mentions a new staffing need; capture-staffing-request takes over for creating the staffing-request record. Use for "Gesprächsnotiz erfassen", "Notiz erfassen", "Call nachbereiten", "Gespräch zusammenfassen", "Notizen vom Telefonat", "Follow-up schreiben", "Telefonnotizen erfassen" or "Telefonnotizen nachbereiten".'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "process-call-notes"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
