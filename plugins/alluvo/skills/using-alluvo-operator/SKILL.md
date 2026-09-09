---
name: using-alluvo-operator
description: Entry point and navigator for the alluvo Operator plugin. Shows which guided workflows (skills) are available and routes to the right one. Use when the operator asks "was kannst du", "wie fange ich an", "hilf mir", "womit kannst du helfen", "überblick", "welche workflows gibt es", "what can you do", "where do I start", greets without a concrete task, or seems unsure which skill fits. Also the reference for cross-cutting alluvo tool behaviour that belongs to no single workflow — including page access and permission sets ("gib X Zugriff auf Y", "warum sieht X den Teamkalender nicht", Berechtigung, permission set, "give someone access to a page") and access to a Wissensdatenbank ("wer darf die Wissensdatenbank sehen", "Wissensdatenbank freigeben", "knowledge base members").
---

Call the MCP tool `get-workflow-guidance` with no arguments. It returns the catalogue of
guided workflows this organization has — including the ones a higher Tarif would unlock —
and each one's trigger phrases. Route the operator to the matching workflow, then call
`get-workflow-guidance` again with that `workflow` name and follow what it returns.

For the cross-cutting conventions that belong to no single workflow — resolving a model
type from the operator's wording, the `confirmed` preview gate, addresses, tagging,
archiving, permissions, `MODULE_LOCKED` — call `get-workflow-guidance` with
`workflow: "using-alluvo-operator"` and, when it answers with a section index, again with
the `section` you need.

Do not improvise this workflow from the description above — the returned guidance is the
workflow. The catalogue is served live and follows the organization's plan.
If the tool answers MODULE_LOCKED, relay that message to the operator and stop.
