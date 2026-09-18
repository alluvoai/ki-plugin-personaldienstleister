---
name: onboard-new-employee
description: 'Onboard a newly added employee by checking completeness, sending and applying the digital personnel questionnaire, recording essential details, finding nearby placements, and managing self-service access. Use for "Mitarbeiter onboarden", "Personalfragebogen schicken", "Stammdaten übernehmen", "Bankverbindung anlegen", "Einladung versenden" or "Passwort zurücksetzen". Writing an employee a message is message-employee; shared-inbox ticket work belongs to manage-inbox.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "onboard-new-employee"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
