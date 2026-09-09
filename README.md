# alluvo Claude Plugins

🇩🇪 **Deutsche Version: [README.de.md](README.de.md)**

The official alluvo Claude plugin marketplace. It ships the **alluvo-operator** plugin: guided workflows for dispatchers, recruiters and sales on top of the alluvo assistant, the alluvo MCP server.

## Prerequisites

- An alluvo account in your organisation.
- [Claude Code](https://claude.com/claude-code) (CLI, desktop app or IDE extension) or Claude Cowork.
- Network access to `https://api.alluvo.ai/mcp`. The assistant connects via OAuth on first use; no token is copied anywhere.

## Installation in Claude Code

1. Add the marketplace (once per machine):
   ```
   /plugin marketplace add alluvoai/alluvo-claude-plugins
   ```
2. Install the plugin:
   ```
   /plugin install alluvo-operator@alluvo-marketplace
   ```
3. Connect the assistant. The plugin brings the alluvo MCP server with it; on first use Claude Code asks you to sign in. You can also start it yourself:
   ```
   /mcp
   ```
   Choose **alluvo**, sign in with your alluvo credentials in the browser, and pick your organisation.
4. Try it:
   > Wer ist gerade verleihfrei?

   The `bench-check` workflow activates and the assistant answers from your organisation's data.

**Updating:** `/plugin marketplace update alluvo-marketplace` followed by `/plugin update alluvo-operator@alluvo-marketplace`. Workflow guidance itself is served live by the assistant and needs no plugin update.

## Installation in Claude Cowork

1. An administrator of your Claude organisation opens **Organisation settings → Plugins → Add plugin → GitHub** and selects this repository.
2. Members enable **alluvo-operator** in their plugin list.
3. On first use the assistant asks for the alluvo sign-in (OAuth) and the organisation.

## Using the assistant without the plugin

Every MCP client can connect directly; the plugin only adds the guided workflows on top. Claude Desktop, claude.ai and other clients use the custom-connector URL `https://api.alluvo.ai/mcp`. Details, including the personal-token path for clients without OAuth, are in the documentation: [Connect the Assistant](https://docs.alluvo.ai/en/alluvo-mcp/connect).

## What the plugin does

Workflows activate on natural phrases such as "wer ist verleihfrei", "create a framework contract for …" or "sell this profile". The catalogue is in [`plugins/alluvo-operator/README.md`](plugins/alluvo-operator/README.md).

The step-by-step guidance for each workflow is served live by the alluvo assistant, so it is always current and follows your organisation's plan. A workflow outside your plan answers `MODULE_LOCKED` with the plan it needs and a trial link.

## Troubleshooting

| Symptom | What to do |
|---|---|
| `alluvo … Needs authentication` in `/mcp` | Sign in via `/mcp` → alluvo. Tokens expire; signing in again fixes it. |
| A workflow does not activate | Say the German or English trigger phrase from the catalogue, or start it explicitly: `/alluvo-operator:bench-check`. |
| `MODULE_LOCKED` | The workflow belongs to a module your organisation has not enabled. The message names the plan and links to the trial. |

## Support

Your alluvo contact, or the documentation at [docs.alluvo.ai](https://docs.alluvo.ai/en/alluvo-mcp/connect).
