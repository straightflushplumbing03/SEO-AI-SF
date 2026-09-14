# Historical Backfill (Phase 0 deliverable)

The Phase-1 acceptance criterion is that **Tier-1 pages launch immediately from historical
job data** — not after new jobs trickle in. This doc explains how to get Lance's existing
records into the `jobs` / `reviews` tables.

## What to request from Lance

| Source | How used | Privacy rules |
|---|---|---|
| Invoices / service receipts (last 12–24 months) | city, neighborhood, service_type, issue_description, date | Extract **no** street address or client name. City/neighborhood only. |
| CRM export (if any) | job history, service codes | Same as above |
| Before/after photo folders | photo filenames for case studies | Upload to site `assets/img/case-studies/`; never EXIF-dump location |
| Review exports (Google/Yelp) | `reviews` rows via F3 | Only 4–5★ with specifics, or verbatim quote **with permission** |

Exact prices must be converted to `cost_range_bucket` (one of:
`0-2500, 2500-5000, 5000-10000, 10000-15000, 15000-25000, 25000+`).
Never store exact prices bound to an identifiable property.

## Columns accepted by `intake_job.py --csv`

Header names are forgiving: `service` or `service_type`; `issue` or `issue_description`;
`cost_bucket` or `cost_range_bucket`; `quote` or `customer_quote`. See
`data/backfill/jobs.example.csv` for the canonical template.

```bash
cp data/backfill/jobs.example.csv data/backfill/jobs.csv
# ... edit with real records ...
python3 scripts/intake_job.py --csv data/backfill/jobs.csv
```

## After import

```bash
# verify what landed
python3 scripts/db.py --report   # (or sqlite3 sfge.db 'select * from jobs')

# generate Tier-1 pages for a specific job
python3 scripts/gen_case_study.py --job-id 1 --no-open-pr   # inspect locally first
python3 scripts/gen_case_study.py --job-id 1                # open the PR for human review
```

## Quality rules for backfill rows

- `city` must be one of the 21 South OC cities (normalized); put anything else in `neighborhood`.
- `issue_description` should be 1–3 plain-language phrases the tech would say. This becomes the
  page's "the job" block and an FAQ answer — write it for a homeowner, not a work-order.
- Only include a `quote` if the customer said something memorable **and** you have permission to
  attribute it to "a Straight Flush customer in [city]" (never by name).
- If you're unsure about a row, leave it out. Quality > volume. A thin backfill that invents
  nothing is fine; a padded one that fabricates is not.

## Review backfill

Reviews can likewise be seeded (if Lance exports them) into `reviews` with
`approved_for_publish=1` only for vetted 4–5★ reviews that name a service or city.
They will be attached to case-study pages via `Review` schema when `job.review_id` matches.