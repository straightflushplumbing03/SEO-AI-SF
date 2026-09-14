#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module B — Supporting content generation engine.

Generates two content types beyond case studies:

1. **Comparison content** ("slab leak vs. general leak", "repipe vs.
   re-route — which do you need") — evergreen, education-first, naturally
   link to the relevant service + city pages.

2. **Service explainer** supporting the opportunity keyword (e.g. "signs
   of a slab leak in Mission Viejo") — written from the real job dataset
   when available (Tier 1), honest scoped otherwise (Tier 2).

Hard rule (guardrail 2): any page that names a *city* must ground its
proof in real detail from Module F (real job, real review quote, real
cost-range data, or a real neighborhood/landmark). Never fabricate a job.

The generator consumes:
- `opportunity` row (keyword, city, service_type, intent_type)
- `jobs` + `reviews` for that city/service (real proof)
- PAA questions (for FAQ schema)
"""

from datetime import date

from . import site_data as S
from . import page as P
from . import schema_jsonld as J
from . import links as L
from . import keywords as K

BLOG_DIR = "academy"   # matches the site's academy/ hub


def _city_slug(city):
    return P.slugify(city)


def _service_slug(service):
    return {
        "Slab Leak Detection": "slab-leak-detection",
        "Leak Detection": "leak-detection",
        "PEX Repiping": "pex-repiping",
        "Water Heater Services": "water-heater-services",
        "Drain Services": "drain-services",
        "Plumbing Repair": "plumbing-repair",
    }.get(service, "plumbing-repair")


def _proof_note(jobs, reviews):
    """Build a grounded 'proof' paragraph from real Module F data, or None."""
    approved = [r for r in reviews if r.get("approved_for_publish")]
    if jobs:
        job = jobs[0]
        city = job["city"]
        when = (job.get("date") or "")[:7].replace("-", "/")
        base = (
            f"Across real {job.get('service_type')} work in {city}"
            + (f" (including a {when} job in the {job['neighborhood']} area)" if job.get("neighborhood") and when else "")
            + ", the most common cause we see is "
        )
        issue = (job.get("issue_description") or "").strip()
        return f"<p>{P.esc(base)}{P.esc(issue[:160].lower())}.</p>"
    if approved:
        r = approved[0]
        city = r.get("extracted_city") or "Orange County"
        return (
            f"<p>One recent customer in {P.esc(city)} told us: "
            f"&ldquo;{P.esc((r.get('text') or '')[:200])}&rdquo;</p>"
        )
    return None


def _tier(city, service, jobs, reviews):
    if jobs:
        return "tier1"
    return "tier2"


def build_comparison_page(topic_key, jobs, reviews):
    """Comparison/explainer page generator.

    topic_key in: 'slab-vs-general-leak', 'repipe-vs-reroute',
                  'tank-vs-tankless', 'cu-vs-pex'
    """
    topic = _COMPARISON[topic_key]
    slug = topic["slug_key"]
    canonical_path = f"{BLOG_DIR}/{slug}"
    today = date.today().isoformat()

    schema_blocks = [
        J.plumber_min("Orange County, CA"),
        J.breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "Blog", f"{S.DOMAIN}/academy"),
            (3, topic["h1"], f"{S.DOMAIN}/{canonical_path}"),
        ]),
        J.article(topic["h1"], today, f"{S.DOMAIN}/{canonical_path}"),
        J.faq(topic["faq"]),
    ]
    schema_types = ["Plumber", "BreadcrumbList", "Article", "FAQPage"]

    sections = []
    sections.append(f"""<section>
  <div class="wrap two-col">
    <div class="reveal">
      <div class="eyebrow">Straight Flush explains</div>
      <h2>A quick way to think about it</h2>
      <p class="muted">{topic['blurb']}</p>
      <ul class="founder-list">
        {P.tick_list(topic['bullets'])}
      </ul>
      <div class="cta-band reveal" style="margin-top:24px;">
        <div><p>{topic['cta_line']}</p></div>
        <a href="../contact.html" class="btn btn-primary">Talk to Lance</a>
      </div>
    </div>
    <div class="reveal">
      <div style="border:1px solid var(--line);border-radius:14px;padding:22px;background:var(--sand);">
        <div class="eyebrow">How we handle this</div>
        <p class="muted">Every case is diagnosed first — acoustic and thermal pinpointing before any demo, then a clear recommendation. No demolition-first guessing, no finger-in-the-plug estimates.</p>
        <div class="stars-row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span></div>
        <p class="muted" style="font-size:0.9rem;">Family-owned &amp; operated since 2019. <strong>Always A Safe Bet.</strong></p>
      </div>
    </div>
  </div>
</section>""")

    proof = _proof_note(jobs, reviews)
    if proof:
        sections.append(f"""<section class="section-sand">
  <div class="wrap">
    <div class="reveal">
      <div class="eyebrow">From real local work</div>
      <h2>What homeowners in this area actually run into</h2>
      {proof}
    </div>
  </div>
</section>""")

    sections.append(P.faq_section(
        "../",
        "Questions homeowners ask",
        topic["h1"] + " — FAQ",
        topic["faq"],
    ))
    sections.append(P.cta_band(
        "../", topic["cta_line"], "Call (949) 374-6524 for a straight answer.",
        cta_label="Call Now", cta_href="tel:+19493746524",
    ))

    html = P.head(topic["h1"] + " | Straight Flush Plumbing", topic["meta_desc"],
                  canonical_path, "../", schema_blocks)
    html += P.nav("../")
    html += P.page_hero(
        "../",
        eyebrow="From the blog",
        h1=topic["h1"],
        sub=topic["hero_sub"],
        cta_label="Schedule Service",
        cta_href="../contact.html",
        trail=[("Home", "index.html"), ("Blog", "academy/index.html"), (topic["h1"][:40], None)],
    )
    html += "\n" + "\n".join(sections) + "\n"
    html += P.footer("../")

    return {
        "slug": slug,
        "canonical_path": canonical_path,
        "html": html,
        "title": topic["h1"] + " | Straight Flush Plumbing",
        "description": topic["meta_desc"],
        "schema_types": schema_types,
        "type": "blog",
    }


_COMPARISON = {
    "slab-vs-general-leak": {
        "slug_key": "slab-leak-vs-general-leak",
        "h1": "Slab Leak vs. General Leak — How to Tell the Difference",
        "meta_desc": "A slab leak hides under your foundation. Learn to tell a slab leak from a general plumbing leak, when it's an emergency, and how Straight Flush pinpoints it without tearing up your slab.",
        "blurb": "A general leak (under a sink, behind a wall, along visible piping) is annoying but usually easy to locate. A slab leak is different: water escapes from copper piping buried in the concrete foundation, and the first sign is often a mystery water bill or a warm spot on the floor.",
        "hero_sub": "The two leaks feel different, cost different amounts, and need very different responses. Here's the plain-English breakdown.",
        "cta_line": "Not sure which kind of leak you have?",
        "bullets": [
            "General leak: visible, localized, usually fixable fast",
            "Slab leak: hidden under the foundation — higher stakes",
            "Spiking water bill, warm floor, or the sound of running water with everything off = likely slab leak",
            "Straight Flush pinpoints slab leaks acoustically before opening any concrete",
        ],
        "faq": [
            ("How do I know if it's a slab leak or a regular leak?",
             "If you see water, drips, or a wet spot on a wall, it's usually a general leak. If your water bill spikes with no visible leak, floors feel warm, or you hear water running when everything is off, it's likely a slab leak under the foundation."),
            ("Can a slab leak fix itself?",
             "No. Slab leaks get worse and cause foundation and mold damage. The only question is how soon the leak gets pinpointed and repaired."),
            ("Will you break through the slab to find it?",
             "Only after pinpointing. Straight Flush uses acoustic and thermal methods first so concrete is opened in exactly the right spot — not for exploratory demolition."),
        ],
    },
    "repipe-vs-reroute": {
        "slug_key": "repipe-vs-reroute",
        "h1": "Repipe vs. Re-route — Which Do You Actually Need?",
        "meta_desc": "Repipe or re-route? Straight Flush explains when a slab leak can be re-routed around the slab and when a full repipe to PEX is the honest recommendation.",
        "blurb": "When copper pipes under a slab develop pinhole leaks, there are two honest answers. A re-route abandons the failing pipe and runs new line around the problem — faster, cheaper, less invasive. A repipe replaces the whole system, usually with PEX, and is the right call when the old copper is failing everywhere.",
        "hero_sub": "The right answer depends on how many pipes are failing and how old the system is. Here's how to think about it.",
        "cta_line": "Get a straight answer on your repipe options",
        "bullets": [
            "One isolated pinhole in good-aged pipe → re-route or spot repair",
            "Multiple failures, 1980s copper, recurring leaks → whole-house repipe to PEX",
            "PEX doesn't corrode the way copper does — no more pinhole roulette",
            "Either way: diagnose first, decide with clear numbers",
        ],
        "faq": [
            ("How do I know if I need a repipe instead of a re-route?",
             "If it's a single leak in an otherwise healthy system, a re-route usually carries you. If you're on your third leak in different pipes, or the copper is visibly thinning and corroded, a whole-house repipe is usually the more honest, cost-effective answer."),
            ("How long does a repipe take?",
             "A whole-house repipe in an occupied home typically takes 2-4 days depending on size and access. A re-route of a single slab leak can often be done in a day."),
            ("Does insurance cover repipes?",
             "Coverage varies. Leak damage is often covered; the pipe replacement itself often isn't. We document everything clearly so your adjuster and you have the full picture."),
        ],
    },
    "tank-vs-tankless": {
        "slug_key": "tank-vs-tankless-water-heater",
        "h1": "Tank vs. Tankless Water Heater — The Honest Comparison",
        "meta_desc": "Tank or tankless? Straight Flush compares up-front cost, lifespan, and ongoing cost for South Orange County homes so you can pick the right water heater.",
        "blurb": "Tank heaters are cheaper to install and simpler to maintain. Tankless units are more expensive up front but last longer and heat water on demand. For most OC homes, the deciding factors are space, gas supply, and how long you plan to stay in the house.",
        "hero_sub": "No pushy upsells here — just the math, sized to your home.",
        "cta_line": "Want a recommendation sized to your home?",
        "bullets": [
            "Tank: lower install cost, 8-12 year lifespan, needs a tank space",
            "Tankless: 2-3x the up-front cost, 20+ year lifespan, endless hot water",
            "Gas vs. electric matters more in OC than you'd think",
            "Straight Flush installs both — we'll give you the real math either way",
        ],
        "faq": [
            ("How much more does tankless cost to install?",
             "Typically 2-3x the tank install, mostly because of venting and gas line work. Over 15+ years the energy savings can offset it — but only if your home's setup suits a tankless unit."),
            ("How long do water heaters last?",
             "Tank units average 8-12 years; tankless units commonly last 20+. Hard water (common in parts of South OC) shortens both unless they're maintained."),
            ("Should I replace my water heater before it leaks?",
             "If it's past 10 years, showing rust, or making noise, it's smart to plan replacement before a catastrophic leak. A leaking heater can flood a garage or attic in minutes."),
        ],
    },
    "cu-vs-pex": {
        "slug_key": "copper-vs-pex-repiping",
        "h1": "Copper vs. PEX — Why We Recommend PEX for Most Repipes",
        "meta_desc": "Copper vs PEX for repiping: Straight Flush explains why PEX wins for most South OC repipes — no pinhole leaks, easier in walls, better freeze tolerance — and when copper still makes sense.",
        "blurb": "Copper was the standard for decades, and it still has its uses. But copper develops pinhole leaks over time (especially in 1970s-80s homes), while modern PEX doesn't corrode. For whole-house repipes, PEX is usually the better, cheaper, longer-lasting choice.",
        "hero_sub": "Here's the straight-talking version of the copper vs. PEX debate.",
        "cta_line": "Wondering if your old copper is on borrowed time?",
        "bullets": [
            "PEX: flexible, doesn't corrode, fewer fittings, cheaper material",
            "Copper: rigid, traditional, still great for exposed and short runs",
            "80s copper pinhole leaks are the #1 repipe trigger in South OC",
            "We repipe with PEX and re-route slab leaks through the attic",
        ],
        "faq": [
            ("Is PEX safe for drinking water?",
             "Yes. PEX is certified for potable water and is the most common new residential plumbing in the US. It does not corrode, which is exactly why it stops the pinhole-leak cycle."),
            ("Can you reuse my copper for anything?",
             "Often yes — exposed vertical runs and appliance hookups can stay copper. A repipe doesn't have to mean replacing every inch of pipe, only the failing parts."),
            ("How much cheaper is PEX than copper for a repipe?",
             "Material runs meaningfully less, and because PEX is faster to install, total labor drops too. Exact numbers depend on home size and layout — call for a real estimate."),
        ],
    },
}


def build_service_explainer(opportunity, jobs, reviews):
    """Supporting article for an opportunity keyword (Module B).

    Grounded in real data when available (Tier 1); honest scoped (Tier 2)
    otherwise. Always links back to the city + service pages.
    """
    city = opportunity["city"]
    service = opportunity["service_type"]
    city_slug = _city_slug(city)
    svc_slug = _service_slug(service)
    tier = _tier(city, service, jobs, reviews)
    slug_key = P.slugify(f"{city}-{service}-guide")
    if tier == "tier1":
        slug_key = P.slugify(f"{city}-{service}-what-to-know")
    canonical_path = f"{BLOG_DIR}/{slug_key}"
    today = date.today().isoformat()

    title = f"{service} in {city}: What to Know"
    desc = (f"Our guide to {service.lower()} in {city} — including real experience "
            f"from completed work by Straight Flush Plumbing." if tier == "tier1"
            else f"An honest overview of {service.lower()} in {city} from the "
                 f"owner-operated South OC specialist.")

    schema_blocks = [
        J.plumber_min(city),
        J.breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "Blog", f"{S.DOMAIN}/academy"),
            (3, title, f"{S.DOMAIN}/{canonical_path}"),
        ]),
        J.article(title, today, f"{S.DOMAIN}/{canonical_path}"),
        J.service_with_catalog(city, S.OFFERED_SERVICES, f"{service} in {city}"),
    ]
    schema_faqs = [(q, P.esc(_answer_for(q, city, service, jobs))) for q in K.paa_questions(service, city)]
    schema_blocks.append(J.faq(schema_faqs))
    schema_types = ["Plumber", "BreadcrumbList", "Article", "Service", "FAQPage"]

    sections = []
    sections.append(f"""<section>
  <div class="wrap two-col">
    <div class="reveal">
      <div class="eyebrow">Guide</div>
      <h2>{P.esc(service)} in {P.esc(city)} — the short version</h2>
      <p class="muted">{P.esc(opportunity['keyword'])} is one of the questions we answer every week.</p>
      <ul class="founder-list">
        {P.tick_list([
            f"Specialists in {P.esc(service.lower())} across the {P.esc(city)} area",
            "Diagnose-first: acoustic + thermal pinpointing",
            "Real, honest pricing — no demo-first surprises",
            "Owner-operated: Lance answers the phone",
        ])}
      </ul>
    </div>
    <div class="reveal">
      <div class="eyebrow">Related services</div>
      <div class="city-grid reveal">
        <a class="city-chip" href="../cities/{city_slug}.html">{P.esc(city)} Plumbing <span>&rarr;</span></a>
        <a class="city-chip" href="../services/{svc_slug}.html">{P.esc(service)} <span>&rarr;</span></a>
      </div>
    </div>
  </div>
</section>""")

    if tier == "tier1":
        sections.append(_tier1_proof_section(service, city, jobs, reviews))
    else:
        sections.append(f"""<section class="section-sand">
  <div class="wrap">
    <div class="reveal">
      <div class="eyebrow">Straight Flush in {P.esc(city)}</div>
      <h2>Honest coverage, real local service</h2>
      <p class="muted">Straight Flush Plumbing &amp; Leak Detection is the owner-operated specialist serving the {P.esc(city)} area out of Laguna Niguel. We respond fast and diagnose before we demo. Call (949) 374-6524 for a real answer about {P.esc(service.lower())} in {P.esc(city)}.</p>
    </div>
  </div>
</section>""")

    sections.append(P.faq_section(
        "../",
        "Questions homeowners ask",
        f"Questions about {P.esc(service)} in {P.esc(city)}",
        schema_faqs,
    ))

    # internal links: nearest neighbors
    sections.append(P.neighbor_chips("../", city_slug))

    sections.append(P.cta_band(
        "../", f"Need {P.esc(service.lower())} in {P.esc(city)}?",
        "Call (949) 374-6524 — diagnosed first, honest pricing.",
        cta_label="Call Now", cta_href="tel:+19493746524",
    ))

    html = P.head(title, desc, canonical_path, "../", schema_blocks)
    html += P.nav("../")
    html += P.page_hero(
        "../",
        eyebrow="Guide",
        h1=title,
        sub=P.esc(opportunity["keyword"]),
        cta_label="Schedule Service",
        cta_href="../contact.html",
        trail=[("Home", "index.html"), ("Blog", "academy/index.html"), (title[:40], None)],
    )
    html += "\n" + "\n".join(sections) + "\n"
    html += P.footer("../")

    return {
        "slug": slug_key,
        "canonical_path": canonical_path,
        "html": html,
        "title": title,
        "description": desc,
        "schema_types": schema_types,
        "type": "blog",
        "tier": tier,
    }


def _answer_for(question, city, service, jobs):
    """Plain-English FAQ answer. Grounded in real job data when we have it."""
    q = question.lower()
    svc = service.lower()
    if "cost" in q:
        bucket = None
        if jobs:
            b = [j["cost_range_bucket"] for j in jobs if j.get("cost_range_bucket")]
            if b:
                bucket = S.cost_bucket_label(b[0])
        base = (f"Real {svc} work in {city} typically runs "
                f"({bucket} in our recent completed jobs)." if bucket else
                f"{svc.capitalize()} cost varies with home size, pipe condition, and access. "
                f"Call (949) 374-6524 for a real number for your {city} home.")
        return base
    if "repair" in q or "re-route" in q or "reroute" in q:
        return (f"In most cases a pin-pointed leak can be repaired by spot repair or re-routing "
                f"around the failing section — no whole-slab demolition. That's our "
                f"diagnose-first approach in {city}.")
    if "detected" in q or "find" in q or "know" in q:
        return (f"Acoustic listening + thermal imaging pinpoint the leak location, then we "
                f"confirm before opening anything. If you're in {city} with a spiking water "
                f"bill or warm floor, that's usually a slab leak — call (949) 374-6524.")
    if "insurance" in q or "covered" in q:
        return (f"Coverage varies. In {city}, leak damage is often covered while pipe "
                f"replacement itself often isn't. We document everything so your adjuster has "
                f"the full picture.")
    if "long" in q or "how long" in q:
        return (f"Depending on access, a re-route or spot repair can often be done the same "
                f"day; a whole-house repipe runs 2-4 days. For a {city} home call "
                f"(949) 374-6524 and we'll give you a realistic timeline.")
    return (f"For a {city} home, the honest answer depends on the specifics. Call "
            f"(949) 374-6524 — Lance answers, and you'll get a straight assessment.")


def _tier1_proof_section(service, city, jobs, reviews):
    approved = [r for r in reviews if r.get("approved_for_publish")]
    job = jobs[0] if jobs else None
    when = ""
    if job and job.get("date"):
        when = (job["date"])[:7].replace("-", "/")
    blocks = []
    if job:
        blocks.append(
            f"<p>A completed {P.esc(service)} job in {P.esc(city)}"
            + (f" ({when}, {P.esc(job.get('neighborhood') or 'the area')})" if when else "")
            + f": main issue reported was {P.esc((job.get('issue_description') or '').strip()[:200])}.</p>"
        )
    for r in approved[:2]:
        blocks.append(
            f"<p>&ldquo;{P.esc((r.get('text') or '')[:200])}&rdquo; — a customer in {P.esc(r.get('extracted_city') or city)}.</p>"
        )
    return f"""<section class="section-sand">
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">From real local work</div>
      <h2>What {P.esc(service)} looks like in {P.esc(city)}</h2>
    </div>
    <div class="reveal">
      {''.join(blocks)}
    </div>
  </div>
</section>"""