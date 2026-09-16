---
name: call-prep
description: 'Prepare for a specific meeting or call using the account snapshot, conversation history, contracts, opportunities, agenda, and discovery questions in alluvo. Use for "Termin vorbereiten", "Gespräch vorbereiten", "Call mit Firma X vorbereiten" or "Meeting-Vorbereitung". Use account-briefing for a general internal dossier without a scheduled conversation. German triggers also include: Call vorbereiten, Kundentermin vorbereiten.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "call-prep"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
