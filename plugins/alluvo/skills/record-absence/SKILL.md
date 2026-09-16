---
name: record-absence
description: Record employee sickness, vacation, unpaid absence, or an AU certificate, and check remaining vacation entitlement before booking leave. Use for "Krankmeldung eintragen", "Urlaub buchen", "AU-Bescheinigung hochladen", "Abwesenheit erfassen", "Resturlaub prüfen" or "Urlaubsanspruch prüfen".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "record-absence"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
