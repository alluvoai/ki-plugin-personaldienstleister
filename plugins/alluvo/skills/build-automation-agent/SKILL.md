---
name: build-automation-agent
description: Build or adjust an AI automation agent — scheduled (a recurring report or per-record reminder), deployed on an Inbox so it reacts to inbound tickets, or a multi-step workflow with waits and branches — and change what any alluvo AI agent is told (system blocks, tenant Bausteine, personal instructions, the candidate WhatsApp flow). Use when the operator says "Automatisierungs-Agent bauen", "geplanten KI-Bericht einrichten", "monatlichen Report automatisieren", "Erinnerung vor Vertragsende einrichten", "Agent auf einen Posteingang setzen", "mehrstufigen Workflow mit Wartezeit bauen", "Baustein anlegen", "Agent taggen", "zeig mir den Prompt des Agenten", "Anweisungen des Bewerber-Assistenten ändern", "meine persönliche Anweisung für die KI", "build an automation agent", "schedule an AI report", "deploy an agent to an inbox", "add a delay to a workflow", "attach an instruction block to the agent", "show an agent's prompt", or "change what the chat assistant says".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "build-automation-agent"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
