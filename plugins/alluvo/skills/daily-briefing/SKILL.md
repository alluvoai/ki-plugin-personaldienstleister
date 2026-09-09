---
name: daily-briefing
description: Daily briefing — what's on today: upcoming meetings, due tasks, Outreach replies, pipeline alerts, and top priorities pulled from your own alluvo data. Use this skill when the operator says "was steht heute an", "Tagesbriefing", "mein Tag", "Tagesüberblick", "was ist heute wichtig", "daily briefing", "what's on today", "my day", or "morning briefing".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "daily-briefing"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
