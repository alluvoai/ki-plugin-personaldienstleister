---
name: approve-stundenfreigabe
description: Review and release submitted Stundenzettel (Stundenfreigabe), reimbursements and the resulting Tätigkeitsnachweis — including the Tagesabschluss gate, Abweichungsgründe, the day-level Kundenfreigabe and its revocation, and correcting a Freigabe's signer. Use when the operator says "Stundenfreigabe prüfen", "Stunden genehmigen", "eingereichte Stunden ansehen", "Tag abschließen", "Abweichungsgrund", "Teilfreigabe", "Freigabe zurücknehmen", "Ohne Kunden freigeben", "falscher Unterzeichner", "Zeitraum fehlt", "Stundennachweise", "Spesen freigeben", "Beleg für Mitarbeiter hochladen", "Sammel-Reisekostenabrechnung", "Wegstreckenpauschale", "Kunde sieht keine Stundenfreigabe", "Korrektur beantragen", "timesheet review", "approve timesheets", "close the day for an employee", "partial release", "revoke approval", "correct signer", "approve reimbursements", "upload a receipt for an employee", or asks anything about submitted working hours and their release.
---

Call the MCP tool `get-workflow-guidance` with `workflow: "approve-stundenfreigabe"` and follow exactly what it returns.
Do not improvise this workflow from the description above — the returned guidance is the workflow.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
