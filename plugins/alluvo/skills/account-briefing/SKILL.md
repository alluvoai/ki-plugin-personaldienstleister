---
name: account-briefing
description: 'Build an internal account dossier from alluvo master data, Timeline activity, opportunities, and contracts. Use for "Firma recherchieren", "Kontakt nachschlagen", "Infos zu Unternehmen" or "was wissen wir über Firma X". This workflow does not browse the web or prepare a specific meeting; use call-prep when the operator asks to prepare a conversation. German triggers also include: Kundendossier.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "account-briefing"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
