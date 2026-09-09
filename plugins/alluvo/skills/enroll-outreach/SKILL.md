---
name: enroll-outreach
description: Enroll qualified companies in automated Outreach sequences and manage the enrollment lifecycle (create, check status, pause, resume, unenroll). Use this skill when the operator says "Unternehmen in Sequenz aufnehmen", "Outreach starten für Firma X", "enroll company in outreach", "Sequenz pausieren", "resume outreach", "attach profile", or wants to manage automated outreach enrollment for cold leads.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "enroll-outreach"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
