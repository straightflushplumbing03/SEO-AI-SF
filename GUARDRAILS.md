# Guardrails (non-negotiable)

These are absolute rules. Every generator, script, and future module SHALL enforce them.

1. **Never bypass human review on first launch.**
   Every generated page is a PR, never a direct push to `main`, until Lance explicitly raises
   the autonomy level. Enforced by `scripts/gen_case_study.py` (creates a branch + PR).

2. **Never publish a page without a real local detail** sourced from a real job or real review.
   A local detail = a real completed job, a real review quote, a real city landmark/neighborhood,
   or real cost-range data from actual invoices (ranges only, never identifying).
   Tier-2 (scoped) pages are allowed ONLY when tagged `needs_field_data` and scheduled for
   auto-upgrade on the next real job in that city/service.

3. **Never expose customer-identifying data.**
   No exact street addresses, no customer names without explicit consent, no exact prices tied
   to a specific property. Costs are bucketed (`cost_range_bucket`); locations are city +
   neighborhood only. This is both ethics and liability.

4. **Never regress existing site SEO work.**
   The current canonical scheme, absolute OG image URLs, lazy-loading, image dimensions,
   schema types (Plumber, Service, BreadcrumbList, Article, FAQPage, Review/AggregateRating)
   are ground truth. New pages MUST clone the gold markup exactly. Run `livecheck.py` before
   and after any PR batch.

5. **Rate-limit publishing.**
   Content velocity tracks real job/review velocity. Do not bulk-generate pages for pages' sake.

6. **Explicit sign-off before any paid API.**
   DataForSEO, SerpApi, Twilio, etc. require Lance's approval and a stated cost + free
   alternative before signup. No module may create a paid dependency silently.

## Enforcement points

- `scripts/gen_case_study.py` requires a real `job_id` (or an explicitly-marked demo run) and
  refuses to fabricate details.
- `modules/objects/case_study.py` only emits content derived from the `jobs` row + optional
  real `reviews` rows. It has no "city filler" splashes.
- `scripts/livecheck.py` compares the live site to expected canonicals/schema so regressions
  are caught before a PR batch is opened.