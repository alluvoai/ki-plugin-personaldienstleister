---
name: erlaubnisregister-prospecting
description: Work the AÜG-Erlaubnisregister — every company allowed to lend out staff in Germany. Permit holders per region, whether one company holds a permit at all, the Neugründungen (a permit first seen days ago = a staffing firm setting itself up now), and the import into the CRM. Use when the operator says "Erlaubnisregister", "AÜG-Erlaubnis", "wer darf verleihen", "neue Zeitarbeitsfirmen", "Neugründungen", "hat die Firma eine Erlaubnis", or "Wettbewerber in meiner Region".
---

Call the MCP tool `get-workflow-guidance` with `workflow: "erlaubnisregister-prospecting"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
