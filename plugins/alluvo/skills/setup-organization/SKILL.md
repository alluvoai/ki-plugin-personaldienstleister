---
name: setup-organization
description: 'Walk a new tenant through onboarding by reading manage-setup get_status and completing each open step with the matching MCP call — AÜG permit disclosure, first Niederlassung, priced Einsatzrollen, first client, first employee, Tarifwerk — or handing the operator a settings link for a step that is UI-only (logo, mailbox, calendar, integrations) or currently locked by plan. Use for "Organisation einrichten", "alluvo einrichten", "Onboarding durchgehen", "Ersteinrichtung", "was fehlt noch im Setup" or "Setup abschließen".'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "setup-organization"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
