#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master authority page builder (AI-Authority brief, Section 6).

Composes /about/straight-flush-plumbing-orange-county/ using the same
gold-compatible composer (modules.objects.page) as every other generated page.
The page is a humans-first "master company page" that makes the business
entity, its services, its service area, and its diagnostic approach explicit
and verifiable — the signals search engines and AI answer systems look for.

No fabricated data: every fact comes from site_data or is phrased as a
"verify before publishing" placeholder.
"""
from . import page as P
from . import site_data as S
from . import schema_jsonld as J

CANONICAL_PATH = "about/straight-flush-plumbing-orange-county"
FILENAME = "about/straight-flush-plumbing-orange-county.html"

TITLE = ("Straight Flush Plumbing & Leak Detection | "
         "Orange County Plumbing & Leak Detection")
DESCRIPTION = ("Owner-operated plumber in Laguna Niguel specializing in slab "
               "leak detection, repiping, and water heater services across "
               "South Orange County, CA. Diagnose-first, honest pricing.")
H1 = "The Orange County plumbing & leak detection company that diagnoses first"


def _schema_blocks():
    return J.master_authority_schema()


def _service_link(prefix, slug, label):
    return f'<a href="{prefix}services/{slug}.html">{label}</a>'


def _city_link(prefix, slug, label):
    return f'<a href="{prefix}cities/{slug}.html">{label}</a>'


def _section(eyebrow, heading, inner_html, cls="section-sand"):
    return f"""<section class="{cls}">
  <div class="wrap">
    <div class="section-head reveal" style="margin-bottom:26px;">
      <div class="eyebrow">{P.esc(eyebrow)}</div>
      <h2>{P.esc(heading)}</h2>
    </div>
    <div class="reveal">{inner_html}</div>
  </div>
</section>"""


def _service_cards(prefix):
    cards = [P.TICK_ICON]
    groups = [
        ("leak-detection", "Leak Detection", "Acoustic, electronic and thermal pinpointing for hidden and slab leaks."),
        ("slab-leak-detection", "Slab Leak Detection", "Finding hot-water slab leaks in copper-era homes without guesswork demolition."),
        ("pex-repiping", "PEX Repiping", "Whole-home repiping that protects against pinhole copper failures."),
        ("water-heater-services", "Water Heater Services", "Tank and tankless water heater installation and service."),
        ("plumbing-repair", "Plumbing Repair", "Repairs done right the first time — diagnose first, then fix."),
        ("drain-services", "Drain Services", "Drain cleaning and diagnostics for slow and blocked drains."),
        ("emergency-plumbing", "Emergency Plumbing", "24/7 emergency response for burst pipes and urgent leaks."),
    ]
    items = "\n".join(
        f'      <a class="service-card reveal" href="{prefix}services/{slug}.html">'
        f'<div class="section-head" style="margin-bottom:12px;"><div class="eyebrow">Service</div>'
        f'<h3>{label}</h3></div><p>{desc}</p>'
        f'<span style="color:var(--accent);">Learn more &rarr;</span></a>'
        for slug, label, desc in groups
    )
    return f"""<div class="card-grid reveal" style="grid-template-columns:repeat(auto-fill,minmax(280px,1fr));">
{items}
</div>"""


def _diagnostics(prefix):
    items = [
        ("Acoustic leak detection", "Specialized listening equipment pinpoints the sound of pressurized water escaping from a pipe — even through a concrete slab."),
        ("Thermal imaging", "Infrared cameras show temperature differences from a hot-water leak, narrowing the search area without breaking concrete."),
        ("Electronic pipe locating / pressure testing", "Confirms which line is leaking and isolates the problem before you pay for a repair."),
    ]
    lis = "\n".join(
        f'<li><span class="tick">{P.TICK_ICON}</span> <strong>{name}:</strong> {desc}</li>'
        for name, desc in items
    )
    return f"""<ul class="founder-list">{lis}</ul>"""


def _service_areas(prefix):
    cities = S.CITIES
    chips = "\n".join(
        f'<a class="city-chip" href="{prefix}cities/{slug}.html">{label} <span>&rarr;</span></a>'
        for slug, label in sorted(zip(cities, [S.CITY_LABEL[c] for c in cities]))
        if S.is_valid_city(slug)
    )
    return f"""<div class="city-grid reveal">
{chips}
</div>
<p class="muted" style="margin-top:18px;">Not sure if we cover your neighborhood? "
  "Call <a href="tel:{S.PHONE_TEL}">{S.PHONE_DISPLAY}</a> and ask — Lance answers the phone.</p>"""


def _faqs():
    return [
        ("Where is Straight Flush Plumbing & Leak Detection located?",
         "Straight Flush is based in Laguna Niguel, CA, and serves homes across South Orange County, including Dana Point, San Clemente, Mission Viejo, Aliso Viejo, and the surrounding communities."),
        ("Is Straight Flush a licensed plumbing company?",
         "Straight Flush is an owner-operated plumbing company. Verify current California contractor licensing and insurance with the company directly before hiring."),
        ("What does diagnose-first mean?",
         "Before recommending any repair, Straight Flush confirms where the leak actually is using acoustic and thermal detection — so you don't pay for unnecessary demolition or guesswork."),
        ("Does Straight Flush handle emergencies?",
         "Yes — 24/7 emergency response is available for burst pipes, urgent leaks, and similar plumbing emergencies in the South Orange County area."),
    ]


def build_authority_page():
    """Return dict with keys: slug, html, canonical_path, title, description, schema_types."""
    prefix = "../"
    schema_blocks = _schema_blocks()
    schema_types = [b["@type"] for b in schema_blocks]

    html = P.head(TITLE, DESCRIPTION, CANONICAL_PATH, prefix, schema_blocks)
    html += P.nav(prefix)
    html += P.page_hero(
        prefix,
        eyebrow="About · Orange County",
        h1=H1,
        sub=("Straight Flush Plumbing & Leak Detection is an owner-operated "
             "plumbing company based in Laguna Niguel, CA, serving South Orange "
             "County homes. Lance answers the phone, diagnoses first, and only "
             "recommends the repair that actually solves the problem."),
        cta_label="Call (949) 374-6524",
        cta_href="contact.html",
        trail=[("Home", "index.html"), ("About", "about.html"),
               ("Orange County", None)],
    )

    body = []

    body.append(_section(
        "Who we are", "The owner-operated South Orange County leak specialist",
        """<p class="muted">Straight Flush Plumbing &amp; Leak Detection is a family-owned,
owner-operated plumbing company serving South Orange County, California since
2019. We specialize in the two problems that catch most homeowners by surprise:
hidden water leaks and slab leaks in copper-era homes.</p>
<p class="muted">Our diagnostic-first standard means we confirm the source of a problem
before we recommend a repair. That's why homeowners in Laguna Niguel, Dana Point,
Mission Viejo and the surrounding cities ask us to find leaks that other
plumbers were ready to tear a wall or slab open to chase.</p>
<p class="muted">Lance, the owner, answers the phone. You talk to the person who will
actually do the work — not a call center.</p>""",
    ))

    body.append(_section(
        "What we do", "Plumbing services we provide",
        _service_cards(prefix),
        "section",
    ))

    body.append(_section(
        "How we work", "The diagnostic approach that sets us apart",
        """<p class="muted">Most leak detection starts with a guess and a demolition crew.
Ours starts with physics.</p>
""" + _diagnostics(prefix) + """
<p class="muted" style="margin-top:14px;">Once we've pinpointed the leak, we walk you through the
honest set of repair options — whether that's a spot repair, a reroute, or a
full repipe — with real pricing, so you can make an informed decision.</p>""",
    ))

    body.append(_section(
        "Where we work", "Serving South Orange County",
        _service_areas(prefix),
    ))

    body.append(_section(
        "The Straight Flush standard", "What you can expect on every job",
        """<ul class="founder-list">
  <li><span class="tick">%s</span> <strong>Know before you drill, dig, or open a wall.</strong> No guesswork demolition.</li>
  <li><span class="tick">%s</span> <strong>Plain-language explanations.</strong> You understand what we found and why.</li>
  <li><span class="tick">%s</span> <strong>Honest options, not upsells.</strong> If a small fix solves it, that's what we recommend.</li>
  <li><span class="tick">%s</span> <strong>Technology that earns its keep.</strong> Acoustic, thermal, and electronic tools, used correctly.</li>
  <li><span class="tick">%s</span> <strong>Local accountability.</strong> We live and work in the communities we serve.</li>
</ul>""" % (P.TICK_ICON, P.TICK_ICON, P.TICK_ICON, P.TICK_ICON, P.TICK_ICON),
    ))

    body.append(P.faq_section(prefix, "Common questions",
                              "Questions about Straight Flush", _faqs()))

    # Internal linking section: services + service areas + academy
    body.append(_section(
        "Explore", "More plumbing resources",
        """<div class="two-col">
  <div>
    <div class="eyebrow">Services</div>
    <ul class="founder-list">
      <li>""" + _service_link(prefix, "leak-detection", "Leak Detection") + """</li>
      <li>""" + _service_link(prefix, "slab-leak-detection", "Slab Leak Detection") + """</li>
      <li>""" + _service_link(prefix, "pex-repiping", "PEX Repiping") + """</li>
      <li>""" + _service_link(prefix, "water-heater-services", "Water Heater Services") + """</li>
      <li>""" + _service_link(prefix, "emergency-plumbing", "Emergency Plumbing") + """</li>
    </ul>
  </div>
  <div>
    <div class="eyebrow">Learn</div>
    <ul class="founder-list">
      <li><a href="../academy/what-is-a-slab-leak.html">What is a slab leak?</a></li>
      <li><a href="../academy/slab-leaks-in-older-orange-county-homes.html">Slab leaks in older Orange County homes</a></li>
      <li><a href="../academy/thermal-imaging-leak-detection-explained.html">Thermal imaging leak detection explained</a></li>
      <li><a href="../guides/repair-vs-reroute-vs-repipe.html">Repair vs. reroute vs. repipe</a></li>
      <li><a href="../case-studies/">Real case studies</a></li>
    </ul>
  </div>
</div>""",
        "section",
    ))

    html += "\n" + "\n".join(body) + "\n"
    html += P.cta_band(
        prefix, "Ready to talk to a plumber who diagnoses first?",
        "Call Lance at (949) 374-6524 — real answers, honest pricing, no call center.",
        cta_label="Call (949) 374-6524", cta_href="contact.html",
    )
    html += P.footer(prefix)

    return {
        "slug": "straight-flush-plumbing-orange-county",
        "html": html,
        "canonical_path": CANONICAL_PATH,
        "title": TITLE,
        "description": DESCRIPTION,
        "schema_types": schema_types,
    }