---
name: onboard-new-employee
description: Onboard a newly added employee — check profile completeness, send the digitaler Personalfragebogen (guest link) and apply the returned Stammdaten, capture Bankverbindung, Notfallkontakt, bAV and No-Gos, surface nearby placement opportunities, and invite the employee to the self-service app. Use when the operator says "neuen Mitarbeiter anlegen", "Mitarbeiter onboarden", "Profil vervollständigen", "Personalfragebogen schicken", "Stammdaten übernehmen", "Bankverbindung anlegen", "Notfallkontakt erfassen", "No-Go hinterlegen", "bAV eintragen", "Go-Live-Datum setzen", "Einladung versenden", "Einladung erneut senden", "Mitarbeiter kann sich nicht anmelden", "Passwort zurücksetzen", "Mitarbeiter anschreiben", "onboard new employee", "check completeness", "message the employee in the app", or after a new employee record has been created.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "onboard-new-employee"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
