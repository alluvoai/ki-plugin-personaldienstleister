# alluvo connection (optional)

Applies only when the alluvo assistant (MCP server) is connected. Detect this when a tool
`get-workflow-guidance` or `manage-settings` exists. In Claude Code, MCP tools often appear only
after a tool search; search for `get-workflow-guidance` before assuming that no connection exists.

With alluvo connected, load the workflow `publish-job-posting` via
`get-workflow-guidance(workflow: "publish-job-posting")` before reading context, creating the job,
publishing to the Talent Hub or the Bundesagentur, translating it, or running the Google-for-Jobs
check. It is served live and carries the current job fields, tool calls, channels and checks; this
skill deliberately does not copy them. If `get-workflow-guidance` answers `MODULE_LOCKED` (Talent
Hub not part of the plan), say so in one sentence and deliver as a file or in the chat.

For Phase 0 the workflow's step 1 lists the read-only context sources: tone and form of address
(du/Sie), company bio, taboo words, inclusivity rules, role catalogue, branches, benefits and a
few published jobs as style references. The interview answers map to the job's contract fields
there too.
