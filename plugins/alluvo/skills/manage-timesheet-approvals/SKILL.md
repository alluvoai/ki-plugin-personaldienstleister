---
name: manage-timesheet-approvals
description: Review, approve, revoke, and correct submitted timesheets and the resulting activity record. Use for "Stundenfreigabe prüfen", "Stunden genehmigen", "Tag abschließen", "Teilfreigabe", "Freigabe zurücknehmen", "falscher Unterzeichner" or "Stundenkorrektur". Receipts, expenses, and travel costs belong to manage-reimbursements. German triggers also include: Stundenzettel prüfen.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "manage-timesheet-approvals"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
