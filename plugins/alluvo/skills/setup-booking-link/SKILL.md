---
name: setup-booking-link
description: 'Create, configure, activate, repair, or share a booking link (MeetingBookingLink). Use for "Buchungslink anlegen", "Terminlink erstellen", "Kalender-Link einrichten", "Buchungslink aktivieren", "Buchungslink zeigt keine Termine", "Terminlink funktioniert nicht", and — for an existing link — "schick mir meinen Terminlink", "Kalender-Link teilen", "Buchungslink per Mail", "Link für die Website", "Buchungslink einbetten". German triggers also include: Terminlink reparieren, Terminlink schicken, Buchungslink abrufen.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "setup-booking-link"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
