---
name: build-dienstplan
description: Create, adjust, publish or cancel a monthly Dienstplan for an Einsatz — with ArbZG compliance checks — including Umbesetzung of Schichten to another employee, the Soll/Plan comparison the employee sees, and the Begründungspflicht on employee changes to a released plan. Use when the operator says "Dienstplan erstellen", "Schichten anlegen", "Schicht stornieren", "Schicht umbesetzen", "Einsatz auf jemand anderen umbesetzen", "Dienstplan veröffentlichen", "Dienstplan ist noch im Entwurf", "Dienstplan-Vorschlag des Mitarbeiters prüfen", "die App zeigt mir X h unter Soll", "Soll-Vergleich im Dienstplan-Wizard", "die App verlangt eine Begründung", "plan the schedule", "create shifts for next month", "someone else has to take the shift", "publish the schedule", "approve the employee's shift change", or wants to build, adjust or release a monthly shift plan.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "build-dienstplan"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
