# AI Authority / Local Search Intelligence Module — Architecture

## Purpose

Make Straight Flush Plumbing & Leak Detection an authoritative, verifiable,
technically strong, locally relevant *entity* that search engines and AI answer
systems can accurately understand — and confidently cite as a source when
appropriate. This module is the "AI Authority / Local Search Intelligence"
layer of the larger Business Brain vision. It does **not** manipulate AI
systems; it makes the site more descriptive, consistent, and verifiable.

## Guiding principles (from the brief)

1. Legitimacy over tricks: accurate info, consistent identity, strong local SEO,
   first-party expertise, structured data, real project content.
2. No fabrication: addresses, licenses, awards, reviews, projects, partners,
   stats must all be verified. Use `[VERIFY]` placeholders.
3. Preserve working systems: this is additive, not a redesign.
4. Do not spam: no doorway pages, no fake reviews, no paid link packages.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ SITE (straightflushplumbing03/-Up2datewebsiteseo)            │
│  static HTML + gold-compatible composer                      │
│  - canonical NAP in footer/contact/schema                    │
│  - Plumber/Organization/WebSite/Breadcrumb/FAQ/Article schema│
│  - 21 city pages, 7 service pages, 20+ academy articles      │
│  - case-studies hub + real case studies                      │
│  - robots.txt welcomes AI crawlers; sitemap.xml               │
└───────────────▲───────────────────────────────▲──────────────┘
                │ generates pages via PR         │ validates/extends
┌───────────────┴───────────────────────────────┴──────────────┐
│ SFGE ENGINE (straightflushplumbing03/SEO-AI-SF) — this module │
│  modules/objects/site_data.py        canonical entity source │
│  modules/objects/schema_jsonld.py    schema builders (+org)  │
│  modules/objects/authority_page.py   master authority page   │
│  scripts/gen_authority_page.py       PR pipeline for page    │
│  scripts/ai_visibility.py            AI citation probes      │
│  scripts/audit_engine.py             technical/GEO audit     │
│  scripts/livecheck.py                live-site guardrail     │
│  scripts/sync_prs.py                 merge reconciliation    │
│  dashboard.py / weekly_report.py     reporting               │
│  docs/                              strategy + playbooks     │
└──────────────────────────────────────────────────────────────┘
```

## What "AI discoverability" means here

An AI answer system (ChatGPT, Perplexity, Gemini, Google AI Overviews) should be
able to fetch a page and answer unambiguously:

- **Who** — "Straight Flush Plumbing & Leak Detection" (consistent name everywhere)
- **Where** — Laguna Niguel, CA; South Orange County
- **What** — leak detection, slab leak detection, repiping, water heaters
- **Areas** — the 21-city service area (each page self-describes)
- **What's different** — diagnose-first, owner-operated, acoustic/thermal tools
- **When to call** — symptoms covered across service + academy pages
- **Hours / phone / contact** — identical NAP everywhere + schema

The master authority page (`/about/straight-flush-plumbing-orange-county/`)
centralizes these answers in one verifiable place.

## Business Brain integration

This module is designed as a pluggable "AI Authority / Local Search
Intelligence" component of the Business Brain vision:

- **Monitors already possible:** `ai_visibility` (citations in AI answers),
  `audit_engine` (technical/GEO findings), `sync_prs` (merge state), opportunity
  backlog (Module A).
- **Future monitoring to add:** new reviews, citation consistency, ranking
  changes, competitor changes/backlinks, service-area opportunity detection.
- **Recommendations:** the weekly report already aggregates signals; a future
  "what should Straight Flush do next" recommender is a report/dashboard
  enhancement — no external actions are automated without approval.

## External-action safety

Any action that touches an external service (create listing, respond to review,
email outreach) must be: **draft → request approval → execute only after
approval.** The engine never auto-publishes to external platforms.