# Troubleshooting: "Meta tools aren't available"

Claude-facing diagnosis notes for the case where the Meta tools
(`manage-meta-ads`, `query-meta-ads`) appear missing from the connected alluvo MCP.

Note the stale-manifest angle cuts both ways since the nine-tool → two-tool merge: a
client still holding an old manifest will *offer* `manage-meta-campaign` and friends,
and every call fails with "Tool not found". Same remedy as below — remove and re-add
the connector.

## Why it is (almost) never an auth problem

The server registers **all Meta tools unconditionally** — there is no per-tenant
gate, no Meta-connection requirement, no feature flag on registration. If the
connector is authorized at all, the Meta tools exist server-side. An auth/scope
failure drops **all** alluvo tools, not just the Meta group. A tool list that is
missing **only** the Meta tools is therefore structurally impossible as an auth
issue — do not tell the operator the connection is dead or to re-authorize.

## The historical root cause (fixed server-side 2026-06)

`tools/list` is cursor-paginated. Older server builds capped the page size at 50
while registering ~94 tools, so the Meta group landed on **page 2** behind a
`nextCursor`. Clients that read only page 1 and don't follow the cursor
(claude.ai / Cowork at the time) never received the Meta tools at all — they were
absent from the client's manifest, which looks exactly like "not registered /
connection broken". The fix raised the pagination bounds so every tool ships on
page 1 with no `nextCursor`.

## What actually helps when the tools are missing

- **Fully remove and re-add the alluvo connector** so the client refetches
  `tools/list`. A plain off/on toggle or app relaunch often reuses the cached
  manifest and won't help.
- On clients that lazy-load tools via tool search, opening with the Meta
  job-to-be-done ("create a Meta lead-form campaign…", "check Meta campaign
  performance") can help rank/pull the group in — but only if the tools reached
  the client's manifest at all.
- If the tools are still missing after a full remove/re-add on a current server
  build, escalate to the alluvo team — that is a server/deploy question, not
  something to work around in the session.
