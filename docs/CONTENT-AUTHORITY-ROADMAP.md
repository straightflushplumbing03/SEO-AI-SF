# Content Authority Roadmap

Content is prioritized by the SFGE engine's Module A (opportunity scoring) and
gated by Module F (real job/review data) per guardrail 2 — never publish a page
without a real local detail. This doc is the human strategy overlay.

## Content taxonomy

- **Pillar pages** — the core services + master authority page:
  - `/services/leak-detection/` (Pillar 1)
  - `/services/slab-leak-detection/` (Pillar 2)
  - `/services/pex-repiping/` (Pillar 3)
  - `/services/water-heater-services/` (Pillar 4)
  - `/about/straight-flush-plumbing-orange-county/` (Master authority page — added in this iteration)
- **Supporting articles** — academy/ (20+ existing), each linking back to a pillar.
- **Case studies** — case-studies/ (real Module F jobs only; 2 live, more via backfill).
- **Local resources** — 21 city pages + service-areas hub (real local detail only).
- **FAQs** — FAQPage schema on service + city + academy pages.
- **Maintenance guides** — how-to/prevention content (existing academy covers much of this).

## Priority queue (human next steps)

### 1. Complete the master authority page (in progress — PR #9)
- [ ] Merge the page after review.
- [ ] Confirm license/insurance info with owner and replace `[VERIFY]` placeholders.

### 2. Strengthen leak-detection topical hub
The brief's suggested topics are almost all already covered in `academy/`:
what-is-a-slab-leak, acoustic-leak-detection-explained, thermal-imaging-leak-detection-explained,
electronic-pipe-locating-explained, how-plumbers-find-leaks-without-cutting-walls,
slab-leaks-in-older-orange-county-homes, why-is-my-water-bill-so-high, and more.
**Missing pieces to add when topics are genuinely useful:**
- [ ] Pressure-testing explainer (if the company performs pressure tests)
- [ ] "Acoustic vs thermal leak detection" comparison angle inside an existing article (link both pillars)
- [ ] Emergency-leak "what to do right now" flow page (partially covered by emergency-plumbing-checklist + emergency-plumbing service page)

### 3. Geographic content
- [ ] Each city page already links nearest-neighbors (no orphans).
- [ ] Add a real local detail to any city page currently lacking one (Module F backfill drives this).
- [ ] Do not add doorway pages for cities with no real service history.

### 4. Case studies
- [ ] Formalize the case-study framework (see /case-studies/ hub).
- [ ] Backfill historical jobs by city (Phase 0 deliverable) → more Tier 1 pages.

### 5. Reviews / trust
- [ ] Implement review-request flow (F3) once approval is granted (Twilio or existing tool).
- [ ] Only mark up reviews that genuinely exist and comply with search-engine guidelines.

## Cadence / throttling

- New case studies: one per real closed job.
- New service/city content: only past Module F's Tier-1 gate.
- Blog volume: quality-over-quantity; a useful article when a real question
  keeps coming up, not on a fixed quota.

## Guardrails reminder

- No fabricated jobs/customers/reviews/locations.
- No doorway or thin pages.
- Every page must pass: "Would a real Orange County homeowner find this useful?"