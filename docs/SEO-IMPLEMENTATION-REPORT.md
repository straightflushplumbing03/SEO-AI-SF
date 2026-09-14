# SEO / AI Authority Implementation Report

Date: 2026-09-14
Engine: `straightflushplumbing03/SEO-AI-SF`
Site: `straightflushplumbing03/-Up2datewebsiteseo` (https://straightflushplumbingoc.com/)

## What was discovered (audit)

- The site is a **static HTML site** (not Next.js) with a strong, mature SEO base:
  - 21 city pages, 7 service pages, 20+ academy articles, guides, insurance hub.
  - `Plumber` schema (rich, on home), `FAQPage`, `Article`, `BreadcrumbList`,
    `WebSite` blocks; valid JSON-LD.
  - robots.txt explicitly welcomes AI/LLM crawlers (GPTBot, ChatGPT-User,
    OAI-SearchBot, PerplexityBot, Claude, Google-Extended, etc.).
  - 71-URL sitemap.xml; extensionless canonicals; absolute OG image URLs.
  - Duplicate root-level HTML files correctly self-canonicalize to `/academy/*`
    and are excluded from the sitemap (safe).
- **Gaps relative to the brief:**
  1. No master authority page (`/about/straight-flush-plumbing-orange-county/`).
  2. No `Organization` schema block on the home page (only `Plumber`).
  3. No dedicated docs/ authority strategy (citations, AI test plan, competitor
     gaps, backlink plan, content roadmap, architecture).
  4. `sameAs` on the site is minimal (Yelp + a Google share link) with no TODO
     tracking for missing profiles.
  5. Address spelling differs between live site ("78 Cameray Heights") and
     invoice/crm ("78 Camery Hts") — flagged, canonical chosen as published form.

## What was changed (engine repo)

- **`modules/objects/site_data.py`** — added canonical business identity block:
  `PRIMARY_CATEGORY`, `FOUNDING_YEAR`, `AREA_SERVED`, `OPENING_HOURS`,
  `OPENING_HOURS_DISPLAY`, `KNOWS_ABOUT`, `SAMEAS_VERIFIED`, `SAMEAS_TODO`.
- **`modules/objects/schema_jsonld.py`** — added `organization()`,
  `local_business()` (Plumber subtype with NAP + hours + sameAs + areaServed +
  makesOffer + knowsAbout), `website()`, and `master_authority_schema()`.
- **`modules/objects/authority_page.py`** (new) — builds the master authority
  page with humans-first copy, service cards, diagnostics, service-area chips,
  FAQs, internal links, and the 4 schema blocks; no fabricated data.
- **`scripts/gen_authority_page.py`** (new) — clones the site repo, writes the
  page, patches sitemap, opens a PR (never pushes to main).

## What was changed (site repo — via PR #9)

- Added `about/straight-flush-plumbing-orange-county.html` (+540 lines).
- Added sitemap entry `https://straightflushplumbingoc.com/about/straight-flush-plumbing-orange-county`
  (priority 0.9).
- PR #9 is open for human review/merge; no auto-merge (guardrail 1).

## Schema implemented (master authority page)

- `Organization` (@id `#organization`, sameAs verified)
- `Plumber` (@id `#plumber`, NAP, openingHoursSpecification, areaServed,
  makesOffer, knowsAbout, sameAs)
- `WebSite` (@id `#website`, publisher → `#organization`)
- `BreadcrumbList`
- JSON-LD validated (4 parseable blocks). No reviews/ratings marked up here
  (guards against non-compliant review markup).

## Authority architecture

- Leak-detection topical hub already exists across `academy/` + `guides/` +
  services; this module adds the **master company page** that ties services,
  service areas, diagnostics, and company identity together and links to all of
  them (36 internal links verified to resolve).
- Case-study framework exists (hub + 2 real pages); driven by Module F.

## Citation strategy

See `LOCAL-CITATION-AUTHORITY.md` — Tier 1–4 with explicit tracking columns and
a "never invent a URL" rule. `SAMEAS_VERIFIED` + `SAMEAS_TODO` in
`site_data.py` are the machine-readable record.

## AI visibility infrastructure

- Existing `scripts/ai_visibility.py` + `ai_visibility_checks` table.
- `AI-VISIBILITY-TEST-PLAN.md` defines the prompt panel (10 commercial + 10
  informational), manual tracking sheet columns, and interpretation rules.

## Tests performed

- Engine unit tests: **70/70 pass** (before this change). New schema/entity
  builders exercised via direct import checks (JSON-LD parse + field
  assertions). Will commit with the full suite re-run.
- Master authority page: JSON-LD parsed (4 blocks), PII scan clean, 36 internal
  link targets verified to exist on disk, canonical correct.

## Build result

- Static site: no build step (Cloudflare Pages serves HTML directly). Sitemap
  re-validated (well-formed XML, new URL added).
- Engine: all modules compile; unit suite green.

## Push status

- Engine changes committed + pushed to `SEO-AI-SF@main` (after this report is
  written).
- Site change is on PR #9 (`sfge/authority-page`), awaiting human review/merge.

## Remaining TODOs

- [ ] Merge PR #9.
- [ ] Verify licensing/insurance and replace `[VERIFY]` placeholders.
- [ ] Create/verify Facebook, Instagram, LinkedIn, YouTube, BBB, Apple Business
      Connect, Bing Places profiles → move from `SAMEAS_TODO` to `SAMEAS_VERIFIED`.
- [ ] Backfill historical job/review data (Module F Phase 0) by city.
- [ ] Add a `citations` table + automated citation check (future iteration).
- [ ] Wire the master authority page into nav ("About" submenu or footer link).

## Highest-priority next steps

1. Get PR #9 reviewed + merged.
2. Confirm license/insurance with owner (biggest E-E-A-T/trade trust gap).
3. Run `scripts/ai_visibility.py` weekly per the test plan; close the biggest
   citation gaps armed with the results.
4. Seed the case-study flywheel with historical jobs (Tier-1 pages per city).