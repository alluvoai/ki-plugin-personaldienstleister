---
name: clean-inbox
description: Triage and clean up a shared company inbox in alluvo (tickets from Gmail/WhatsApp/Chat) — review each Vorgang, close only with evidence, create follow-up tasks for anything unclear, and manage the inbox's own forwarding, Geschäftszeiten, Buchungslinks, notifications and phone-assistant instructions. Use when the operator says "Inbox aufräumen", "Tickets aufräumen", "Zero Inbox", "Ticket weiterleiten", "Ticket in andere Inbox verschieben", "Rechnung an die Buchhaltung weiterleiten", "Geschäftszeiten der Inbox ändern", "Vorlaufzeit ändern", "Buchungslink anlegen", "Inbox folgen", "Telefonassistent-Anweisungen ändern", "Mitarbeiter anschreiben", "neues Ticket erstellen", "Ticket löschen", "als Spam melden", "clean up the inbox", "triage tickets", "forward this ticket", "move a ticket to another inbox", "create a booking link", "open a new conversation", or names a shared inbox to work through. Not for a private mailbox.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "clean-inbox"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
