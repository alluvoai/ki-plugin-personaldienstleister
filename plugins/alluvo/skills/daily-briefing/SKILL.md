---
name: daily-briefing
description: Create a daily briefing from alluvo data with today's meetings, due tasks, outreach replies, pipeline alerts, and top priorities. Use for "was steht heute an", "Tagesbriefing", "mein Tag", "Tagesüberblick" or "was ist heute wichtig". German triggers also include: Morgenbriefing.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "daily-briefing"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
