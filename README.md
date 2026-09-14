# SFGE — Straight Flush Growth Engine

An autonomous local-SEO + AI-search-visibility system for **Straight Flush Plumbing & Leak Detection**
(`straightflushplumbingoc.com`, an owner-operated slab-leak specialist in South Orange County, CA).

SFGE is a separate service that treats the website repo (`straightflushplumbing03/-Up2datewebsiteseo`)
as a **target it opens PRs against**. It never pushes straight to `main`.

The core thesis: every completed job is a unique, geotagged, timestamped, real piece of
proof-of-work that no competitor and no generic AI-SEO subscription can fabricate. SFGE turns
that operational data into content, schema, and internal links.

## Why this is not a generic AI-SEO clone

Generic tools auto-publish branded articles from keyword clusters. SFGE is built around
**Module F — the Job-to-Content flywheel**:

1. **F1** — a technician closes a job via a 90-second mobile form (privacy-safe: no addresses, no
   exact prices, no identifying client details).
2. **F2** — SFGE generates a real case-study page from that job's data, with proper schema and
   internal links, and opens it as a PR.
3. **F3** — real customer reviews are mined for content and schema.
4. **F4** — public housing-age data + job history predicts *which neighborhoods are statistically
   about to need slab-leak service* and don't know Straight Flush exists yet.

Guardrails (non-negotiable — see `GUARDRAILS.md`):

- Every generated page is a PR, never a direct push (until Lance explicitly raises autonomy).
- No page is published without a **real local detail** sourced from a real job/review.
- No customer-identifying data is ever exposed in generated content.
- The site's existing schema/canonical/technical SEO baseline is treated as ground truth to protect.

## Repo layout

```
sfge-engine/
├── README.md
├── GUARDRAILS.md
├── schema.sql            # Postgres-compatible DDL (SQLite-compatible statement set)
├── config.example.yaml   # site + module config (copy to config.yaml)
├── .env.example          # secrets (never commit .env)
├── data/
│   └── backfill/         # CSV templates for one-time historical job import
├── docs/                 # design notes: BACKFILL, OPERATIONS, SITE-GROUND-TRUTH
├── scripts/
│   ├── init_db.py        # create tables from schema.sql
│   ├── db.py             # thin sqlite3/psycopg wrapper
│   ├── livecheck.py      # smoke-test the live site (canonicals, sitemap, schema key)
│   ├── intake_job.py     # F1: technician job-close intake (CLI + CSV batch)
│   └── gen_case_study.py # F2: generate case-study page + PR
├── modules/
│   └── objects/          # page/schema/sitemap/link-graph/case-study builders
└── tests/                # acceptance + gold-markup regression tests
```

## Current status — Phase 1 (Job-to-Content only)

- [x] Phase 0: live-site ground truth documented (`docs/SITE-GROUND-TRUTH.md`)
- [x] `schema.sql` (jobs, reviews, opportunities, content, ai_visibility_checks, audit_findings)
- [x] `scripts/db.py` (SQLite + optional Postgres), `scripts/init_db.py`
- [x] `scripts/livecheck.py` — verifies live-site canonicals/sitemap/schema as a baseline guard
- [x] `modules/objects/page.*`, `schema.*`, `sitemap.*`, `links.*` — gold-pattern page builder
- [x] `modules/objects/case_study.py` — Tier-1 case-study generator AND Tier-2 honest scoped placeholder pages (`needs_field_data`)
- [x] `scripts/gen_case_study.py` — CLI: `job_id` -> page file + PR against site repo
- [x] `scripts/intake_job.py` — F1: CLI/CSV/SMS-ready job intake
- [ ] Pending: Lance's historical job records — run backfill, then the first real batch of Tier-1 PRs

## How to run (Phase 1)

```bash
# 0. Config + secrets (see .env.example). Never commit real values.
cp config.example.yaml config.yaml
cp .env.example .env        # set GITHUB_TOKEN, repo target, etc.

# 1. Initialize the local DB
python3 scripts/init_db.py

# 2. Smoke-check the live site baseline (optional, any time)
python3 scripts/livecheck.py

# 3. Log a completed job (replaces the technician form for MVP)
#    cost-bucket must be one of: 0-2500, 2500-5000, 5000-10000, 10000-15000, 15000-25000, 25000+
python3 scripts/intake_job.py --city "Laguna Niguel" --service "Slab Leak Detection" \
  --neighborhood "Bear Brand" --issue "Slab leak under kitchen; copper pinhole; rerouted through attic" \
  --duration-hours 6 --cost-bucket "15000-25000" --quote "Best money we've spent on this house."

# 4. Generate the case-study page + open a PR against the site repo
python3 scripts/gen_case_study.py --job-id 1
```

Every generated page is composed by `modules/objects/page.py`, which clones the **exact
head/nav/footer markup** from the published site (the gold variant shared by the site's content
pages), so output matches the live site's structure and styling. Pages are written into the site
repo as new files under `case-studies/`, wired into the hub index, and added to `sitemap.xml`;
the site repo keeps full ownership of the remaining build/deploy pipeline and Cloudflare serves
the result. Run `scripts/livecheck.py` before and after a PR batch to confirm no regression.

## Roadmap (phases per the build brief)

- **Phase 1 (now):** F1 + F2 — job-to-content flywheel, PR per page, human approves & merges.
- **Phase 2:** F3 review flywheel + basic weekly report.
- **Phase 3:** Modules A + B — keyword/opportunity engine gated by the real-local-detail rule.
- **Phase 4:** Modules C + D — schema/internal-linking automation + technical/GEO audits.
- **Phase 5:** Module E AI-visibility tracking + F4 demand-signal model (housing-age data).
- **Phase 6:** approval-gate tuning, dashboard, alerting.

See `docs/` for detailed design notes.