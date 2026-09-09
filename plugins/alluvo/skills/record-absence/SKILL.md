---
name: record-absence
description: Record a Krankmeldung, Urlaub, unpaid Abwesenheit, or AU-Bescheinigung for an employee, and check the remaining Urlaub balance before booking vacation. Use when the operator says "Krankmeldung eintragen", "Urlaub buchen", "AU-Bescheinigung hochladen", "AU in die Personalakte legen", "Abwesenheit erfassen", "wie viel Resturlaub hat", "Urlaubsanspruch prüfen", "record sick leave", "log absence", "employee is off sick", "how many vacation days are left", or wants to create or update an absence period.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "record-absence"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
