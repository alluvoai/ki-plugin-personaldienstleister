# Alluvo Claude Plugin Marketplace

Private Claude plugin marketplace for Alluvo. Connect this repo to **Claude Cowork**
via GitHub sync (Organization settings → Plugins → Add plugin → GitHub), or add it in
Claude Code — ask your alluvo contact for the marketplace to add.

## Layout

```
.claude-plugin/marketplace.json        # marketplace manifest (relative-path sources only)
plugins/
  alluvo-operator/
    .claude-plugin/plugin.json          # plugin manifest (has version — bump on every change)
    README.md                           # operator-facing docs
    skills/<workflow>/SKILL.md          # one skill per job-to-be-done
```

## Plugins

### `alluvo-operator` (v0.1.0)

Guided, **German-first** workflows for Alluvo staffing-agency operators (Disponenten,
Recruiter, SDRs) on top of the **Alluvo MCP server**. Turns ~90 raw MCP tools into the
handful of jobs-to-be-done operators run daily. **Prerequisite:** the Alluvo MCP server
must be connected to the Claude client. Skills call only `mcp__alluvo__*` tools — no API
tokens, no shell, no internal-network access. Every mutating step previews before it writes.

| Loop | Skills |
|------|--------|
| **Staffing & placement** | `bench-check`, `match-bench-to-clients`, `onboard-new-employee`, `intake-personalbedarf` |
| **Sales & outreach** | `define-icp`, `prospect-nearby-companies`, `enroll-outreach`, `merge-duplicate-companies`, `log-company-signal` |
| **Ops & compliance** | `build-dienstplan`, `manage-contract-lifecycle`, `triage-data-quality`, `record-absence`, `approve-stundenfreigabe`, `clean-inbox` |

Per-skill detail: [`plugins/alluvo-operator/README.md`](plugins/alluvo-operator/README.md).

## Rules for changing this repo

1. **Bump the version on every change.** Edit `version` in the relevant
   `plugins/<name>/.claude-plugin/plugin.json` whenever you change *anything* in that
   plugin (a skill, the description, the manifest). The org sync **compares versions and
   skips unchanged plugins** — if you don't bump, your change will not sync. Use semver:
   patch for skill tweaks, minor for new skills, major for breaking restructures.
2. **Relative-path sources only.** Every entry in `marketplace.json` must use a
   `"source": "./plugins/<name>"` relative path. Do **not** use `github`, `url`,
   `git-subdir`, `npm`, or `pip` source types — those fail on private org sync. If source
   content lives in another private repo, copy the folders in; don't reference externally.
3. **Keep it private.** This repo must stay private/internal on github.com. No public repo,
   no GitHub Enterprise Server.
4. **Names:** lowercase, hyphen-separated, ≤64 chars. Avoid reserved names (`anthropic-*`,
   `claude-plugins-official`, `agent-skills`).
5. **Size:** keep each plugin's footprint well under 50 MB.

## Authoring constraints for skills

- **MCP-only.** Skills reference only `mcp__alluvo__*` tools (and `search-docs`). No tokens,
  no bash, no `apdc`/`adev`, no direct DB. Cowork connectors reach services over Anthropic's
  cloud (public internet) — a workflow touching a firewalled internal tool won't work as a
  connector and must be flagged.
- **German-first**, operator vocabulary; dual-language trigger phrases in each `description`.
- **Preview → confirm** on every mutating MCP step.
- **One skill per job-to-be-done**, split by workflow (not by source document). The
  `description` field is the trigger — write it as "Use when the operator says …".
- Skills run in chat **and** Cowork; hooks/sub-agents run **only** in Cowork — don't rely on
  them for behavior needed everywhere.
