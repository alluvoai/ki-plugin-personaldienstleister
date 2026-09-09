---
name: manage-meta-ads
description: >-
  Manage Meta (Facebook/Instagram) advertising end-to-end for alluvo tenants —
  recruiting/lead campaigns, ad sets, creatives, audiences, automation rules,
  and the conversion tracking that makes optimization work. Use when asked to
  create/edit/launch/audit Meta ads or campaigns, build or upload ad creatives,
  set conversion/optimization events, debug "why are conversions/sessions not
  tracking", configure the Talent Hub pixel, or decide which event a campaign
  should optimize for. Triggers include "check campaign performance", "how are
  my ads doing", "create a lead ad / lead form", "build an ad creative",
  "what's my CPL / cost per lead", "launch a Meta/Facebook/Instagram campaign",
  "my Meta leads aren't becoming candidates", "map a lead form to
  Candidate/Contact", plus German phrasings such as "Werbeanzeigen",
  "Kampagnen-Performance prüfen", "Anzeigen prüfen", "Lead Ads erstellen",
  "Anzeige schalten", "Leads kommen nicht an", "Lead-Zuordnung einrichten".
  Encodes the funnel event chain, the optimization-event strategy, and how a
  lead form is mapped so submissions become records.
---

# Managing Meta Ads (alluvo)

## Purpose

alluvo runs Meta recruiting/lead campaigns per tenant against the tenant's own ad
account, driving traffic to **Talent Hub landing pages** (`/{prefix}/{slug}`,
e.g. `/c/...`) and optimizing for an on-site **Pixel + Conversions API (CAPI)**
event — or collecting leads natively via instant forms. This skill guides
campaign creation, creatives, optimization-event choice, and performance review.

> **MUTATING — and it spends real money.** Every write (`create_campaign`,
> `create_adset`, `create_ad`, budget changes, resume) is two-stage: the tool
> returns a preview without `confirmed: true`; show it, get explicit operator
> approval, then confirm. New ads launch **PAUSED** and are only resumed after
> the verify-then-launch checklist below.

## Prerequisites

- alluvo MCP connected (`mcp__alluvo__*`) — everything here assumes the
  **production** server (live ad account) unless told otherwise.
- The tenant's Meta connection is set up (ad account, page). `query-meta-ads`
  `resource: "creative"` `action: "list_pages"` reveals the available `page_id`s.
- Exclusively `mcp__alluvo__*` tools — no shell, no file I/O (see the creatives
  workflow for how local images reach the server without either).
- `manage-meta-ads` / `query-meta-ads` belong to the **Recruiting** module. If the
  tenant has not unlocked it, both tools are absent from the tool list and calling
  one by name answers `MODULE_LOCKED` — relay that German message verbatim (it names
  the required Tarif and the Testphase link) and stop; there is no workaround. Check
  first with `manage-apps` `action: "modules"`.

## ⚠️ These are JOB ADS — always set the EMPLOYMENT special ad category

Every alluvo campaign advertises **jobs** (recruiting). Meta classifies
employment as a **Special Ad Category**, so **every `create_campaign` MUST pass
`special_ad_categories: ["EMPLOYMENT"]`** (as a JSON array string). Skip this
and Meta **rejects the ads / disapproves the campaign** (and it's a policy
violation). This is set **only at campaign creation and is immutable** — you
cannot add it later; a mis-created campaign must be recreated.

```
manage-meta-ads
  resource: campaign
  action: create_campaign
  ad_account_id: act_...
  name: "..."
  objective: OUTCOME_LEADS
  daily_budget_cents: 2900
  special_ad_categories: "[\"EMPLOYMENT\"]"
```

**Because of EMPLOYMENT, we CANNOT define key demographics** — Meta blocks
them on purpose to prevent discrimination:

- **Age** — no narrowing; must be the full `18-65` (`age_min/age_max 25-64` is rejected with "Invalid parameter").
- **Gender** — cannot target by gender; all genders only.
- **Detailed interests / behaviors** — no interest or behavioral narrowing.
- **Geo** — coarser than normal (no postal-code/1-mile precision); `custom_locations` with a radius (km) around a city is the allowed lever. **The radius has a floor**: Meta rejects anything below ~24 km (15 mi) on an EMPLOYMENT ad set, so plan the catchment at **≥ 25 km** and add cities rather than tightening one circle.

So the **creative must self-select** the audience — put the role + region in the
copy ("examinierte Pflegefachkraft (m/w/d)", "Köln/Düsseldorf/Wuppertal") since you
can't target it. Verify the category is active behaviorally: an EMPLOYMENT
campaign **rejects age narrowing** on its ad sets; a non-special one accepts it.

## ⚠️ (m/w/d) — every Jobbezeichnung must be gender-neutral (AGG)

German job ads fall under the **AGG (Allgemeines Gleichbehandlungsgesetz)**: a role
designation that reads as one gender is a discrimination risk (and a common Abmahnung
target). So **every job title — in ad `message`/`headline`/`description`, on the
landing-page `headline`/`hook_text`/`cta_label`, and on any linked Job posting — must
be gender-neutral**: append **`(m/w/d)`** to the role designation.

- Add `(m/w/d)` the **first time** the role is named as a designation, e.g.
  **"examinierte Intensivpflegefachkraft (m/w/d)"**, **"Pflegefachkraft (m/w/d)"**.
  You don't need it on every repetition, nor on generic field words ("Intensivpflege",
  "die Pflege", "auf der Intensiv").
- Grammatically-neutral nouns ("Fachkraft", "Pflegekraft") **still** get `(m/w/d)` —
  this is legal best practice, not grammar.
- **Hard checklist item** before every `create_creative` / `create_ad` and
  `manage-campaign-landing-page create/update`: confirm the role designation carries
  `(m/w/d)`. Audit existing live ads/pages the same way — missing `(m/w/d)` is an
  exposure to fix, not a nice-to-have.

## MCP tools

Two Meta tools, split read vs. write, both called as `resource` + `action` (all under
`mcp__alluvo__`). Reads need no `confirmed`; writes are two-stage — without
`confirmed: true` you get a preview and nothing is written.

| `resource` | `query-meta-ads` (reads) | `manage-meta-ads` (writes) |
|---|---|---|
| `campaign` | `list_campaigns`, `conversions` (local landing-page converters — no Meta call) | `create_campaign`, `configure`, `pause`, `resume`, `archive`, `delete`, `update_budget`, `clone`, `bulk_pause`, `bulk_resume`, `bulk_update_budget`, `clone_campaign_to_accounts` |
| `ad_set` | `list_adsets`, `get_adset` | `create_adset`, `update_adset`, `pause`, `resume`, `archive`, `delete`, `update_budget`, `clone`, `bulk_pause`, `bulk_resume`, `bulk_update_budget` |
| `ad` | `list_ads` | `create_ad`, `update_ad_creative`, `pause`, `resume`, `archive`, `delete`, `clone`, `bulk_pause`, `bulk_resume` |
| `creative` | `list_creatives`, `list_pages` (→ `page_id`) | `upload_image` (url / media_id / base64), `create_creative` (link ad **or** native Lead Ad via `lead_gen_form_id`) |
| `leads` | `list`, `view`, `sync`, `stats`, `list_forms`, `get_form`, `list_mappings` | `skip`, `subscribe_page`, `create_form`, `create_mapping`, `update_mapping`, `delete_mapping`, `reprocess` |
| `audiences` | `list`, `view`, `view_size`, `list_presets` | `create_custom`, `create_lookalike`, `delete`, `save_preset`, `apply_to_adset`, `delete_preset` |
| `conversions` | `list_pixels`, `list_events`, `stats` | `create_pixel`, `update_pixel`, `delete_pixel`, `set_talent_hub_default`, `configure` |
| `automation_rules` | `list`, `test`, `history` | `create`, `update`, `delete`, `toggle` — CPL kill/scale rules |
| `campaign_insights` | `overview`, `campaigns`, `placements`, `demographics`, `creatives`, `leads`, `trend`, `recommend` (`date_preset`, default `last_30d`) | — |
| `reach` | `estimate`, `compare` — pre-launch audience size | — |
| `ad_library` | `search_by_advertiser`, `search_by_keyword`, `search_by_country` — public competitor research | — |

`manage-temp-vault` (not a Meta tool) turns a local file into a public URL the prod
server can fetch for `upload_image` — the upload itself is done by the operator, see
Creatives.

> **Taking a landing page live is not a `manage-campaign-landing-page` action.** That tool
> writes copy and runs the A/B loop (`create`, `update`, `create_variant`,
> `start_experiment`, …). Flipping the page's status is a record action:
> `manage-record-action` `operation: "execute"`, `model_type: "0-340"`,
> `record_id: <page_id>`, `action: "activate-landing-page"` (or `"deactivate-landing-page"`
> to put it back to draft), `confirmed: false` → `true`. Neither is offered when the page is
> already in that state.

> **`resource` replaces the old `entity_type`.** For the lifecycle actions shared by
> `campaign`/`ad_set`/`ad` (`pause`/`resume`/`archive`/`delete`/`update_budget`/`clone`
> and the `bulk_*` variants) there is no `entity_type` param any more — `resource`
> already says what kind of object `entity_id` points at. `entity_id` is likewise the
> target id for `get_adset` and `update_adset` (was `adset_id`), `update_ad_creative`
> (was `ad_id`) and `configure` (was `campaign_id`). Parent-scope ids keep their own
> names: `create_ad` still takes `adset_id`, `apply_to_adset` still takes `adset_id`,
> `create_adset` still takes `campaign_id` + `ad_account_id`. On `automation_rules`,
> the `entity_type`/`entity_id` of `create` still describe the **watched** Meta object
> and are unrelated to `resource`.

> **Nine tools became two.** `manage-meta-campaign`, `manage-meta-creative`,
> `manage-meta-leads`, `manage-meta-conversions`, `manage-meta-automation-rules`,
> `manage-meta-audiences`, `get-meta-campaign-insights`, `analyze-meta-reach` and
> `search-meta-ad-library` are **removed** — calling one fails with "Tool not found".
> The action names are unchanged; add the `resource` and swap the tool name.

> **Per-field docs live behind `action: "describe"`.** Both tools' own descriptions are
> now just the resource/action map — the full parameter matrix, business rules and
> Meta-specific gotchas moved into `describe` (optionally scoped with a `resource`).
> Call it before using a resource for the first time or when unsure about a field; for
> the routine flows the matrix above plus this skill is enough, so don't burn a
> round-trip on `describe` every session.

> **Diagnosing "sync is returning 0 leads."** `query-meta-ads` `resource: "leads"`
> `action: "get_form"` requests and returns the form's actual Page binding — a
> `**Page:** <name> (<id>)` line, or an explicit `⚠️ not bound to a Page` warning if the
> form genuinely has none. Use this directly instead of assuming the binding is missing;
> a form with no Page attached will never sync leads regardless of anything else being
> configured correctly.
>
> **Not the same failure as "leads sync but no candidates appear."** That one is a missing
> or inactive **mapping**, not a Page/sync problem — check `action: "list_mappings"` and
> see "Lead intake" below.

> **"Meta tools aren't available"?** This is virtually never an auth problem — an
> auth failure drops *all* alluvo tools, not just the Meta group. Usually the
> client is holding a stale cached tool manifest: **fully remove and re-add the
> alluvo connector** (a plain off/on toggle often reuses the cache). Do not tell
> the operator to re-authorize. Details: `references/troubleshooting.md`.

## Hard rules (Meta-side, immutable)

- **`special_ad_categories: ["EMPLOYMENT"]` is mandatory and immutable** — see the job-ads callout above. Set it on every `create_campaign`; it cannot be added later.
- **Campaign objective is immutable** after creation. To change `OUTCOME_TRAFFIC` → `OUTCOME_LEADS`, you must **duplicate/recreate** the campaign, not edit it.
- The conversion event a campaign optimizes for is set on the **ad set**: `optimization_goal: OFFSITE_CONVERSIONS` + `pixel_id` + `custom_event_type` (builds the `promoted_object`). `OUTCOME_LEADS` does **not** itself mean "Lead" — the ad set's `custom_event_type` picks the exact event, and it **must match an event the landing page actually fires**.
- CBO campaigns: omit ad-set budget, pass only `bid_amount_cents` (bid cap). Lowest-cost vs bid-cap matters — operators may switch to "Highest volume" in review.
- `create_adset` **requires `ad_account_id`** — it is the ad account that owns the campaign, NOT the `campaign_id`. (Passing the campaign id as the account produces a confusing "Object act_… does not exist" error.)

## Native Lead Ads (instant forms, `destination_type: ON_AD`)

A native Lead Ad collects the lead **inside Facebook/Instagram** via an instant form — no landing page. Historically this runs at a fraction of the website-funnel CPL, so prefer it for high-volume top-of-funnel recruiting unless a landing page is specifically wanted. The whole flow is MCP-native:

1. **Form** — `manage-meta-ads` `resource: "leads"` `action: "create_form"` (or reuse one via `query-meta-ads` `resource: "leads"` `action: "list_forms"` → `form_id`). Inputs: `name`, `privacy_policy_url` (mandatory — Meta rejects forms without it), `prefilled_fields` (default `FULL_NAME, EMAIL, PHONE`), `custom_questions` (`{label}` short-answer, or `{label, options:[…]}` multiple-choice — use these to qualify, e.g. preferred shift / Berufserlaubnis), optional `intro_headline`/`intro_paragraph` and `thank_you_*`. Write is two-stage (`confirmed: true`).
2. **Mapping** — `manage-meta-ads` `resource: "leads"` `action: "create_mapping"` with the `form_id` and `mapper` (`Candidate` or `Contact`). **A form without an active mapping produces no records** — every submission is stored and marked `skipped`. Do this before the ad is resumed; see "Lead intake" below.
3. **Creative** — `manage-meta-ads` `resource: "creative"` `action: "upload_image"` then `action: "create_creative"` with `lead_gen_form_id` (the form id) + `page_id`. `link` is optional and UTM tags are skipped (no landing page). CTA defaults to `SIGN_UP`.
4. **Ad set** — `manage-meta-ads` `resource: "ad_set"` `action: "create_adset"` with `optimization_goal: LEAD_GENERATION`, `destination_type: ON_AD`, and `page_id` (Meta builds the page-only `promoted_object`; no pixel involved). `ad_account_id` required.
5. **Ad** — `create_ad` pointing at the creative. Launch PAUSED, verify, then resume.

Submitted leads flow back into alluvo via the leadgen webhook (`create_form` auto-subscribes the Page) or by pulling with `query-meta-ads` `resource: "leads"` `action: "sync"` — but arriving is not the same as becoming a record; the mapping decides that. Lead Ads still advertise jobs → `special_ad_categories: ["EMPLOYMENT"]` + (m/w/d) rules apply.

## Lead intake — a mapping is what turns a lead into a Candidate/Contact

A stored `meta_leads` row is not yet a person in alluvo. A **lead-ad mapping** binds one
`form_id` to one mapper and to the question→field pairs, and **only an active mapping
converts leads**. A lead whose form has no active mapping is stored with its **full
payload** and marked `skipped` — it is recoverable, not lost, and `reprocess` turns it
into a record later with no further Meta call. So `skipped` means "waiting for a
mapping", never "gone".

**First thing to check when leads arrive but no candidates appear:** `query-meta-ads`
`resource: "leads"` `action: "list_mappings"` (optional `form_id` filter). It lists each
mapping with its mapper, active/INACTIVE state, field pairs, and the lead counts per
status — an empty list, or an `INACTIVE` mapping, is the answer. `resource: "leads"`
`action: "list"` with `status: "skipped"` shows the backlog.

Actions (all writes two-stage — preview first, then `confirmed: true`):

- **`create_mapping`** — `form_id` + `mapper` (`Candidate` or `Contact`), optional
  `page_id` (required only when several Pages are connected), `field_mappings`,
  `is_active` (default true). **Omit `field_mappings`** and the tool derives them from
  the form's own questions, so you don't have to guess Meta's key names; the preview
  names every question it could *not* map (custom qualifying questions have no column —
  they stay queryable in the lead's raw payload). One mapping per form: a second
  `create_mapping` for the same `form_id` errors and points at `update_mapping`. If
  skipped leads already exist for that form, the response says how many are waiting.
- **`update_mapping`** — `mapping_id` plus at least one of `mapper`, `field_mappings`,
  `is_active`. Use `is_active: false` to stop conversion without deleting history.
- **`delete_mapping`** — `mapping_id`. The leads themselves are kept with their raw
  payload; only the mapping goes.
- **`reprocess`** — converts stored `skipped`/`failed` leads into records. Optional
  `form_id`, `lead_id`, `limit` (default 200). Run it after fixing a mapping. Leads whose
  form still has no active mapping simply stay `skipped`; the response splits the run
  into converted / still-skipped / failed.

**Mapper fields.** `Candidate` accepts `full_name`, `first_name`, `last_name`, `email`,
`phone`, `mobile`; `Contact` adds `company` and `position`. Meta's standard `FULL_NAME`
question is the one a real form actually uses, so **`full_name` is normally the right
target** — it is split into first/last name on write, and an explicit first/last pair
from the form wins over the split. Auto-derivation maps Meta's `phone_number` question
to `mobile` and `job_title`/`company_name` to `position`/`company`.

> **`action: "describe"` is stale for this resource.** The `leads` entry still lists only
> `skip`, `subscribe_page`, `create_form` on the write side and omits `list_mappings` on
> the read side — the mapping actions work regardless (they are validated by the tools'
> own action lists). Trust this section over `describe` for lead mapping; reported to the
> alluvo team.

## Reading the stored leads directly (`MetaLead`, `0-313`)

`query-meta-ads` `resource: "leads"` is the operational view — `action: "list"` prints ids,
form, page, status and arrival time (no names), and `action: "view"` opens one lead's
answers. When the question is "wer hat sich diese Woche beworben", read the model instead:
`MetaLead` is on the MCP allowlist as **`0-313`**, so `query-model` / `get-model` /
`search-model` accept it and every row carries the applicant's own answers —
`lead_name`, `lead_email`, `lead_phone` — in one call. Resolve the type via
`list-model-types` rather than hardcoding the ID.

- **Read-only, by design.** The type is listed as `read_only`: `manage-model` create/update
  is rejected and there is no form. Leads are written only by the leadgen webhook, the
  nightly pull and the lead processor. Everything that *changes* a lead's fate stays a
  `manage-meta-ads` action — `create_mapping` / `update_mapping` / `reprocess` above.
- **Filter on the columns, not on the answers.** `lead_name` / `lead_email` / `lead_phone`
  are derived from Meta's positional `field_data` list, not stored columns — they display
  but cannot be filtered, sorted or searched. Filterable: `status`
  (`pending` / `processed` / `failed` / `skipped`), `meta_page_id`, `created_at` (labelled
  "Received At"). `search-model` matches `leadgen_id` and `error_message`. Confirm with
  `get-model-schema` (context `list`) before building a query.
- **Other useful columns:** `form_id`, `campaign_id`, `adset_id`, `ad_id`, `contact_id`,
  `mapped_model_type` / `mapped_model_id` (what the lead became), `error_message`,
  `processed_at`. A custom qualifying question has no column of its own — it lives in
  `raw_data`, which `action: "view"` renders question-by-question.
- **`0-313` is also a legal automation trigger** — "melde jeden neuen Meta-Lead in Slack" is
  a workflow on this type, but *not* on `created` (the row is stored before the payload is
  fetched, so the name is still empty then). `→ build-automation-agent` has the exact
  trigger shape.

## Which event to optimize for — start UP-funnel to exit learning, then move down

The hard constraint is volume: Meta needs ~50 conversions/ad set/week to leave the learning phase. The deep events (`CompleteRegistration`/`Lead`) are often far too sparse at a realistic recruiting budget (single digits/week), so a campaign optimizing on them never learns and burns budget on high-CTR-but-non-converting clicks.

- **The up-funnel optimization ladder (use the highest-volume event that still signals real intent):**
  `ChatEngaged` (chose Rückruf/chat or sent a message — *real engagement, not a bare open*) → `LeadCaptured`/`Contact` → `CompleteRegistration` → `QualifiedLead` → (long-term/value) `Hire`.
- **Day-one default for a low-volume campaign = `ChatEngaged`** (Custom Conversion on the `ChatEngaged` event). It has materially more volume than `Lead`/`CompleteRegistration` but, unlike `IntentModalOpened` (instant modal open) or a bare landing dwell, requires an actual action — so Meta optimizes toward genuinely interested people, not accidental modal-openers. `IntentModalOpened` is available too but is noisier (fires on open before any choice); prefer `ChatEngaged`.
- **Move the optimization event DOWN the funnel as volume builds:** once the deeper event clears ~50/week, switch `custom_event_type` to it (`ChatEngaged` → `Lead`/`CompleteRegistration` → `QualifiedLead` → value/`Hire`). Always keep the shallower events flowing (retargeting audiences + funnel analytics).
- **Note:** `custom_event_type` is set per ad set and is part of the immutable `promoted_object` — to change it you create a new ad set (or use a Custom Conversion mapped to the event). `IntentModalOpened`/`ChatEngaged` are *custom* events, so they require a Meta **Custom Conversion** before they can be selected as an optimization/conversion event.

If conversions/sessions read 0 or CAPI looks dark even though the site flow works,
that is a **developer task** (server-side tracking) — escalate to the alluvo team
rather than tweaking campaigns around it.

## UTM tracking — canonical scheme and auto-enforcement

Every creative built via `manage-meta-ads` `resource: "creative"` `action: "create_creative"` or `resource: "ad"` `action: "create_ad"` automatically receives the canonical `url_tags`:

```
utm_source=meta&utm_medium=paid_social&utm_campaign={{campaign.id}}&utm_content={{ad.id}}&utm_term={{adset.id}}
```

Meta substitutes the `{{…}}` macros at ad delivery with the real campaign / ad /
ad-set ids. **The captured `utm_campaign` in the browser equals the Meta campaign
id.** This powers `query-meta-ads` `resource: "campaign"` `action: "conversions"`, which resolves candidates by
UTM even without a landing-page tag — UTM-matched candidates appear under a
separate "(matched by utm_campaign)" bucket, so tagging landing pages is optional.

The braces must NOT be URL-encoded — Meta substitutes them literally; the tool
guarantees verbatim brace output. Operators almost never need to set `url_tags`
manually — override only for specific creative-level A/B tagging.

## Creatives workflow (images → live ads)

The skill itself never runs shell commands or reads local files. An image reaches
`upload_image` in one of three ways:

- **Already public** — pass its URL directly as `image_url`.
- **Existing media** — reuse a `media_id` / prior `image_hash` (`query-meta-ads`
  `resource: "creative"` `action: "list_creatives"`).
- **Local file on the operator's machine** — `manage-temp-vault create` returns a
  signed upload URL (production, so the prod server can fetch the bytes; a local
  URL is NOT reachable; `ttl_minutes` default 60). **The operator uploads the file
  to that URL themselves** (browser or their own HTTP client — this skill must not
  shell out), which yields the `public_url`.

Then:

1. `manage-meta-ads resource=creative action=upload_image image_url=<public_url> ad_account_id=... confirmed=true` → `image_hash` (≥600×600, JPEG/PNG, dedup by sha256).
2. `resource=creative action=create_creative` (page_id from `query-meta-ads` `resource: "creative"` `action: "list_pages"`, image_hash, `link` = the real public landing URL, message/headline/description, cta) → `creative_id`.
3. `manage-meta-ads resource=ad action=create_ad` (adset_id, creative_id) → ad is created **PAUSED**.
4. `manage-temp-vault delete` when done (Meta has copied the bytes).

Creative copy: German for DE tenants, role+region self-selecting (EMPLOYMENT), front-load the hook in the first ~125 chars (mobile fold), one emoji, ground all claims in the landing page (don't invent pay/bonus numbers — get them from the operator), align CTA to the page, and **never use the word "bewerben"** (see Copy voice below).

## Copy voice — "kennenlernen", never "bewerben"

alluvo recruiting is chat-first and conversational ("schreib uns, wir lernen uns
kennen") — a low-commitment conversation, not a formal application. **Never use
"bewerben" / "Bewerbung" / "jetzt bewerben" / "bewirb dich" in any copy** — ad
headlines, ad body, CTA buttons, or the landing pages the ads point at. Frame
every action as getting to know each other.

- **CTA / button:** "Jetzt kennenlernen" (also fine: "Jetzt unverbindlich
  kennenlernen", "Jetzt kennenlernen – in 2 Minuten"). Never "Jetzt bewerben".
- **Body / hook:** "melde dich", "schreib uns", "lernen wir uns kennen" — not
  "bewirb dich" / "jetzt bewerben".
- **Scope = both surfaces.** Meta creative copy AND the Talent Hub landing pages
  (`manage-campaign-landing-page`: `cta_label`, `headline`, `hook_text`,
  `process_steps`, `benefit_chips`, `initial_message`). The campaign landing-page
  CTA defaults to "Jetzt kennenlernen"; keep any custom `cta_label` on-brand too.
- **Before launching** a creative or activating a landing page, check the copy for
  any "bewerb…" wording and rewrite it. (The AGG-mandated "(m/w/d)" suffix is
  unrelated and stays.)

## Verify-then-launch discipline

Never unpause a conversion campaign until the optimization event is **proven to fire**:

1. Confirm the tracking setup is green (pixel set, landing page fires the event).
2. Submit a real application on each landing page (or use a Meta `test_event_code`) and confirm a row appears via `query-meta-ads` `resource: "conversions"` `action: "list_events"` / `"stats"` and `last_event_at` advances.
3. Confirm the ad set `custom_event_type` matches that event.
4. Then `resume`. Watch CPL/CPA via `query-meta-ads` `resource: "campaign_insights"` (FB feed is usually the cheapest placement; benchmark against the tenant's historical CPL).
5. Budget sanity: don't split a small daily budget across many ads — trim to a focused set or raise budget so the test isn't under-powered.

## Output

- Campaign / ad set / ad ids with status (PAUSED until verified), budget, and the
  chosen optimization event
- Creative summary (headline, hook, CTA) with the (m/w/d) + "kennenlernen" checks
  confirmed
- Performance reviews: CPL/CPA table per campaign/placement with a recommendation
  (scale / trim / fix tracking)

## Related skills

- `→ onboard-new-employee` — leads that become candidates/employees enter here.
- `→ daily-briefing` — includes waiting lead follow-ups in the morning overview.
- `→ log-company-signal` — B2B signals spotted while working ads (client-side hiring).
- `→ build-automation-agent` — alert on an incoming Meta-Lead (`0-313`) as a workflow.
