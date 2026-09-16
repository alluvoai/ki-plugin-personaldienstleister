---
name: research-staffing-agencies
description: Research staffing agencies in the mirrored AÜG permit register by region, check whether a company appears as a permit holder, find newly observed register entries, and import selected companies into the CRM. Use for "Erlaubnisregister", "AÜG-Erlaubnis", "wer darf verleihen", "neu im Register", "hat die Firma eine Erlaubnis" or "Wettbewerber in meiner Region". A newly observed entry is not proof of a new company or newly issued permit. German triggers also include: Erlaubnis prüfen.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "research-staffing-agencies"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
