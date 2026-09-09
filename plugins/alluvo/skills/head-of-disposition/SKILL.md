---
name: head-of-disposition
description: Disposition leadership overview and Disponent coordination — verleihfreie Mitarbeiter, expiring assignments, open Personalbedarfe, Dienstplan-Lücken, Stundenfreigabe backlog, and task delegation to Disponenten. Use this skill when the operator asks "how is utilisation looking", "Dispo-Übersicht", "who is verleihfrei", "auslaufende Einsätze", "offene Bedarfe", "Dienstplan-Lücken", "head of disposition", "disposition overview", "coordinate Disponenten", "unbestätigte Einsatzmitteilungen", "offene Lesebestätigungen". Defaults to the logged-in user; can be broken down per Disponent on request.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "head-of-disposition"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
