---
name: setup-booking-link
description: 'Create, configure, activate, or repair a booking link. Use for "Buchungslink anlegen", "Terminlink erstellen", "Kalender-Link einrichten", "Buchungslink aktivieren", "Buchungslink zeigt keine Termine" or "Terminlink funktioniert nicht". Use share-booking-link to retrieve, send, or embed an existing link. German triggers also include: Terminlink reparieren.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "setup-booking-link"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
