---
name: using-alluvo-operator
description: 'Navigate all available alluvo operator workflows and explain cross-cutting tool behavior, page permissions, and knowledge-base access. Use for "was kannst du", "wie fange ich an", "welche Workflows gibt es", "hilf mir", "Zugriff geben", "Berechtigung prüfen" or "Wissensdatenbank freigeben".'
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
