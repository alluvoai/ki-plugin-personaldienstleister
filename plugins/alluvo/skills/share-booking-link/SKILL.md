---
name: share-booking-link
description: Kalender-Link / Terminlink / Buchungslink teilen, verschicken oder einbetten. Use when the operator says "schick mir meinen Terminlink", "Kalender-Link teilen", "Buchungslink per Mail senden", "Link für die Website", "share my booking link", "send my calendar link", "embed my meeting link", "wie bekomme ich meinen Buchungslink".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "share-booking-link"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
