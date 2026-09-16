# Changelog

Notable changes to the **alluvo** plugin, tenant-facing only. Format follows
[Keep a Changelog](https://keepachangelog.com/). The version is the alluvo
MCP server version.

## [1.14.0] — 2026-09-16

### Added — Bundesagentur: Erlaubnisregister, Kontakte aus Stellentexten, Export

- `erlaubnisregister-prospecting` — find, monitor and verify AÜG permit
  holders (Arbeitnehmerüberlassungserlaubnis) from the Bundesagentur's
  Erlaubnisregister: fresh Neugründungen as the best-timed prospects, region
  slices for competitor and market intelligence, and a lookup for whether a
  named company holds a permit.
- `arbeitsmarkt-export` — export Bundesagentur job-market and
  Erlaubnisregister data (open positions, employers, permit holders) as CSV.
- `lead-radar-prospecting` now also pulls contacts straight out of the
  posting text and cross-checks employers against the AÜG Erlaubnisregister.

This makes the separate `alluvo-ba` plugin superfluous — its Bundesagentur
capabilities now live here, served by the alluvo MCP server like every other
workflow in this plugin.
