---
name: erlaubnisregister-prospecting
description: Find, monitor and verify holders of an AÜG Arbeitnehmerüberlassungserlaubnis from the Bundesagentur's Erlaubnisregister — spot fresh Neugründungen as the best-timed prospects, slice the register by region for competitor and market intelligence, and check whether a named company holds a permit. Use when the operator says "Erlaubnisregister", "AÜG-Erlaubnis", "wer hat eine Erlaubnis", "Neugründungen", "neue Zeitarbeitsfirmen", "Wettbewerber in <Ort>", "hat <Firma> eine Erlaubnis", or wants competitor or market intelligence from the AÜG permit register.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "erlaubnisregister-prospecting"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
