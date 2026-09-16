---
name: share-booking-link
description: Retrieve, share, send, or embed an existing booking link. Use for "schick mir meinen Terminlink", "Kalender-Link teilen", "Buchungslink per Mail senden", "Link für die Website", "Buchungslink einbetten" or "wie bekomme ich meinen Buchungslink". Use setup-booking-link to create, configure, activate, or repair the link. German triggers also include: Terminlink schicken, Buchungslink abrufen.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "share-booking-link"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
