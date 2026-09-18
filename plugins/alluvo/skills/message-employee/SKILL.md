---
name: message-employee
description: 'Write one employee directly — choose the channel (Mitarbeiter-App or email), draft in the address form the tenant already stores, show the operator the full text, and send it as a ticket their answer comes back into. Use for "Mitarbeiter anschreiben", "Mitarbeiter fragen", "Nachricht in die App schicken", "beim Mitarbeiter nachfragen", "Rückfrage an den Mitarbeiter", "frag ihn was an dem Tag war" or "Mitarbeiter per Mail anschreiben". A shared inbox''s existing tickets belong to manage-inbox; acquisition mail to manage-outreach-enrollments; the whole Stammdaten set to onboard-new-employee''s Personalfragebogen.'
---

Call the MCP tool `get-workflow-guidance` with `workflow: "message-employee"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
