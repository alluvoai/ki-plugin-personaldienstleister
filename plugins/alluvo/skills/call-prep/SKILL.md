---
name: call-prep
description: Prepare for a meeting or call — account snapshot, conversation history (Calls/Meetings/Notes via Timeline), open contracts/Opportunities, suggested agenda, and discovery questions, from your own alluvo data. Use this skill when the operator says "Termin vorbereiten", "Gespräch vorbereiten", "bereite den Call mit X vor", "Meeting-Vorbereitung", "prep for my call", "call prep", or "prepare for the meeting with".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "call-prep"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
