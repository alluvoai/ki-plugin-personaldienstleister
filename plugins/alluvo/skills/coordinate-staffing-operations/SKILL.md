---
name: coordinate-staffing-operations
description: 'Coordinate staffing operations across available employees, expiring assignments, open staffing requests, schedule gaps, timesheet backlog, and dispatcher tasks. Use for "Dispo-Übersicht", "Auslastung", "auslaufende Einsätze", "offene Bedarfe", "Dienstplan-Lücken", "Disponenten koordinieren" or "offene Lesebestätigungen".'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "coordinate-staffing-operations"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
