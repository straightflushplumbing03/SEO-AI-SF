# Local Citation Authority Plan

Goal: build a consistent, verifiable set of business citations so search engines
and AI answer systems can confidently connect every "Straight Flush Plumbing &
Leak Detection" mention to the same real-world entity.

## Golden rule

**Never create a listing that doesn't exist. Never pay for spam directories.
Never guess a URL.** Every listing must be created or claimed by the owner
(Lance) and verified before being recorded as "live."

## Canonical NAP to use everywhere

- **Name:** Straight Flush Plumbing & Leak Detection
- **Phone:** (949) 374-6524
- **Website:** https://straightflushplumbingoc.com/
- **Address:** 78 Cameray Heights, Laguna Niguel, CA 92677
- **Hours:** Mon–Fri 8am–7pm · Sat–Sun 9am–6pm; 24/7 emergencies
- **Category:** Plumber

> Use the full business name on every platform. Do not shorten to
> "Straight Flush" or "Straight Flush Plumbing" unless the platform's own
> character limit forces it. Keep the address spelling identical everywhere.

## Tier 1 — Major platforms (highest priority)

| Source | URL | Name | Status | Date verified | Notes |
|---|---|---|---|---|---|
| Google Business Profile | share.google/WcJBYE3uu5FsppBTR | Straight Flush Plumbing & Leak Detection | **claimed (live link on site schema)** | 2026-09-14 | Verify exact address spelling + service area |
| Bing Places | bingplaces.com | — | open | — | Claim and mirror GBP |
| Apple Business Connect | businessconnect.apple.com | — | open | — | Claim for Apple Maps/Siri |
| Yelp | yelp.com/biz/...-laguna-niguel-3 | Straight Flush Plumbing and Leak Detection | **live** | 2026-09-14 | Verify category + hours + photos |
| BBB | bbb.org | — | open | — | Only if joining as a business; verify accreditation claims |

## Tier 2 — Local authority

Orange County / South Orange County organizations that are legitimate places to
list a local plumbing business. **Verify each exists and accepts small businesses
before acting.**

- Local chambers of commerce (Laguna Niguel / Laguna Beach / Mission Viejo / Dana
  Point / San Clemente chambers)
- South Orange County business organizations / local business associations
- Local homeowner / HOA resource directories (only legitimate, well-trafficked ones)
- Local newspapers / community publications (e.g., OC Register local columns,
  local lifestyle mags) — for earned coverage, not paid links

## Tier 3 — Industry authority

- CSLB (Contractors State License Board) license lookup — add to site once verified
- Angi, HomeAdvisor, Thumbtack, Nextdoor Business, Houzz (home-service directories)
- Local plumbers' associations / PHCC (Plumbing-Heating-Cooling Contractors) if a member
- Insurance-preferred contractor directories (if the company is listed by insurers)

## Tier 4 — Social / entity profiles

- Facebook Page (**[VERIFY]** — link to official page)
- Instagram (**[VERIFY]**)
- LinkedIn company page (**[VERIFY]**)
- YouTube channel (**[VERIFY]**)
- Nextdoor Business Page (**[VERIFY]**)

> Only add to `sameAs` after the profile exists and is publicly reachable.

## Ongoing tracking (engine)

The SFGE engine's `site_data.SAMEAS_VERIFIED` / `SAMEAS_TODO` lists are the
machine-readable record. Update them as profiles get created. Add a
`citations` table in `sfge.db` when automated tracking is desired (out of scope
for this iteration).