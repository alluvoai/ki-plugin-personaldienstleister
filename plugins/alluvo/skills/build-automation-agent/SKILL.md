---
name: build-automation-agent
description: Build or adjust an AI automation agent for schedules, inbox events, or multi-step workflows, and manage the instructions given to alluvo AI agents. Use for "Automatisierungs-Agent bauen", "KI-Bericht einrichten", "Agent auf einen Posteingang setzen", "Workflow mit Wartezeit", "Baustein anlegen", "Agenten-Prompt zeigen" or "Anweisungen ändern". German triggers also include: Agent auf Posteingang setzen, Prompt ändern.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "build-automation-agent"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
