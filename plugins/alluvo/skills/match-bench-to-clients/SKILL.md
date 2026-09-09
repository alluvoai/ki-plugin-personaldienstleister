---
name: match-bench-to-clients
description: Match verleihfreie Mitarbeiter to clients with active Rahmenverträge, generate shareable profile URLs, draft Einsatzverträge, and create Disponent review tasks. Use when the operator says "matche die Bank", "finde Einsätze für verleihfreie Mitarbeiter", "match the bench", "create draft assignment contracts", "wer passt zu welchem Kunden", "Einsatzmöglichkeiten für den Bench", or wants to turn an availability gap into a placement.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "match-bench-to-clients"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
