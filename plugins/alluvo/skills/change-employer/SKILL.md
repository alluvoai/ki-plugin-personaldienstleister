---
name: change-employer
description: 'Move an employee to another legal entity (GmbH) of the group with the change-employer record action — new employment period at the new entity, drafted successor contracts, carry-over of vacation, working-time account and tenure. Not for a branch change inside the same legal entity (onboard-new-employee or manage-model) and not for terminations. Use for "Arbeitgeberwechsel", "Gesellschaft wechseln", "in andere GmbH versetzen", "Rechtsträger wechseln", "Mitarbeiter umhängen" or "Wechsel in der Gruppe".'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "change-employer"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
