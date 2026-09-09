---
name: log-company-signal
description: Record a hiring, expansion, funding, product-launch, partnership, or leadership-change Signal on a company. Use this skill when the operator says "Signal loggen", "Firma stellt gerade ein", "Neueröffnung in Köln", "log a signal", "company is expanding", "funding round", "new location", "neue PDL", or wants to record any buying or market trigger on a company record.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "log-company-signal"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
