# Business Entity — Canonical Record

> Source of truth for the identity fields used by every generator, schema block,
> citation, and external profile. **Nothing here is invented.** Values marked
> `[VERIFY]` must be confirmed against a real, current source before being
> promoted to a verified value.

## Canonical NAP

| Field | Value | Source | Status |
|---|---|---|---|
| Business Name | Straight Flush Plumbing & Leak Detection | Site-wide, all pages | Verified |
| Website | https://straightflushplumbingoc.com/ | CNAME + live site | Verified |
| Primary Category | Plumber | Schema on home page (`@type: Plumber`) | Verified |
| Phone (display) | (949) 374-6524 | Site-wide nav/footer/CTA | Verified |
| Phone (tel:) | +19493746524 | Site-wide | Verified |
| Email | straightflushplumbing03@gmail.com | Site footer + contact page | Verified |
| Address | 78 Cameray Heights, Laguna Niguel, CA 92677 | Site footer + contact page + schema | Verified |
| Opening Hours | Mon–Fri 8am–7pm · Sat–Sun 9am–6pm | Site footer + schema | Verified |
| Emergency | 24/7 emergency response | Site copy (service feature) | Verified |
| Founding Year | 2019 | Site footer "since 2019", schema `foundingDate` | Verified |
| Slogan | Always A Safe Bet | Site footer | Verified |

> **Address conflict flag:** invoices log the address as **"78 Camery Hts"**
> (abbreviated) while the live site/contact/footer/schema all use
> **"78 Cameray Heights"**. These are almost certainly the same location, but
> the canonical spelling has been chosen as **78 Cameray Heights** because it is
> the form published consistently across the live site. Confirm the official
> postal form with Google Business Profile / the city before using it on any
> citation — **do not mix the two spellings.**

## Services (canonical offer list)

From the site footer + home `makesOffer`:

1. Leak Detection
2. Slab Leak Detection
3. PEX Repiping
4. Water Heater Services
5. Drain Services
6. Plumbing Repair

Emergency plumbing is offered as a 24/7 response service, not a separate line
in the offers list.

## Service Area (South Orange County)

21 city pages exist on the site (see `site_data.CITIES`): Aliso Viejo, Costa
Mesa, Coto de Caza, Dana Point, Dove Canyon, Foothill Ranch, Huntington Beach,
Irvine, Ladera Ranch, Laguna Beach, Laguna Hills, Laguna Niguel, Laguna Woods,
Lake Forest, Mission Viejo, Newport Beach, Orange, Rancho Santa Margarita,
San Clemente, San Juan Capistrano, Tustin.

Primary base city: **Laguna Niguel, CA.**

## sameAs (entity profiles)

### Verified (already referenced on the live site schema)
- **Yelp:** https://www.yelp.com/biz/straight-flush-plumbing-and-leak-detection-laguna-niguel-3
- **Google Business Profile (share link):** https://share.google/WcJBYE3uu5FsppBTR

### Not yet verified / created (`[VERIFY]` before adding)
| Platform | URL | Status |
|---|---|---|
| Google Business Profile (full) | https://business.google.com/ | open |
| Bing Places | https://www.bingplaces.com/ | open |
| Apple Business Connect | https://businessconnect.apple.com/ | open |
| BBB | — | open |
| Facebook | — | open |
| Instagram | — | open |
| LinkedIn | — | open |
| YouTube | — | open |
| Nextdoor | — | open |
| Angi / HomeAdvisor | — | open |

> **Rule:** never add a URL to `sameAs` (or any citation) unless it has been
> verified to belong to Straight Flush Plumbing & Leak Detection. A URL that
> points to a different business, or that we guess, is worse than no URL.

## Licensing / Certifications / Associations

- California contractor license: **[VERIFY]** — confirm number/category with
  the owner and CSLB before publishing.
- Insurance: **[VERIFY]** — confirm current policy carrier/coverage.
- Certifications (e.g., manufacturer training, water heater certification): **[VERIFY]**
- Trade associations / chamber memberships: **[VERIFY]**

## Owner / Team

- **Lance** — Owner & Lead Technician (from the site's About page).
- No other team member names are published; do not invent any.