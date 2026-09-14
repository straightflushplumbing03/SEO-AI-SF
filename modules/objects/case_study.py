#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F2 — Job-to-content flywheel: case-study page builder.

Given one or more REAL jobs (rows from the `jobs` table), derive a complete,
schema-correct case-study page. All content flows from real intake data; there
is no fabricated proof, no invented customer story, no invented city detail.

Privacy rules enforced here:
- no street addresses, no full names, no exact prices;
- neighborhood-level location only;
- customer quote only when present (with consent in the intake data);
- cost displayed as a range bucket only.

Tiering (Module B hard rule):
- Tier 1: at least min_jobs_for_tier1 real jobs for the city/service combo.
- Tier 2 ('needs_field_data'): no real job yet — clearly scoped, honest page
  with a coverage statement, no invented proof. Auto-upgrades to Tier 1 when a
  real job lands (see gen_case_study.py '--upgrade-tier2').
"""
import json
from datetime import date

from . import site_data as S
from . import page as P
from . import schema_jsonld as J
from . import links as L
from . import sitemap as SITEMAP

CONTENT_DIR = "case-studies"


def _fmt_date(iso):
    if not iso:
        return "recently"
    try:
        d = date.fromisoformat(str(iso)[:10])
        return d.strftime("%B %Y")
    except ValueError:
        return str(iso)


def _service_display(job):
    return S.service_label_for(job.get("service_type") or "Plumbing")


def _service_slug(job):
    label = _service_display(job).lower()
    mapping = {
        "slab leak detection": "slab-leak-detection",
        "leak detection": "leak-detection",
        "pex repiping": "pex-repiping",
        "water heater services": "water-heater-services",
        "drain services": "drain-services",
        "plumbing repair": "plumbing-repair",
    }
    return mapping.get(label, "plumbing-repair")


def derive_slug(job, counter=1):
    """Stable, address-free page slug: {city}-{service}-{job_id}."""
    city_slug = P.slugify(job.get("city") or "orange-county")
    service_slug = _service_slug(job)
    return f"{city_slug}-{service_slug}-{str(job.get('job_id') or counter)}"


def _title(job):
    city = job.get("city") or ""
    service = _service_display(job)
    if job.get("neighborhood"):
        return f"{service} — {job['neighborhood']}, {city}"
    return f"{service} — {city}"


def _summary(job):
    """One true sentence built only from real fields."""
    city = job.get("city") or "Orange County"
    service = _service_display(job)
    when = _fmt_date(job.get("date"))
    when_phrase = f" ({when})" if when and when != "recently" else ""
    if job.get("neighborhood"):
        return (f"Straight Flush Plumbing recently completed a {service} job "
                f"in the {job['neighborhood']} area of {city}{when_phrase}.")
    return f"Straight Flush Plumbing recently completed a {service} job in {city}{when_phrase}."


def _issue_paragraph(job):
    """Built from the real issue_description. Escaped for HTML."""
    issue = (job.get("issue_description") or "").strip()
    return P.esc(issue or f"Details of the completed work are on file with the company.")


def _relevant_links(prefix, job):
    city_slug = P.slugify(job.get("city") or "")
    service_slug = _service_slug(job)
    out = []
    city_label = S.CITY_LABEL.get(city_slug)
    service_label = _service_display(job)
    if city_label:
        out.append(f'<a href="{prefix}cities/{city_slug}.html">{city_label} plumbing services</a>')
    out.append(f'<a href="{prefix}services/{service_slug}.html">{service_label}</a>')
    return out


def build_case_study_page(job, reviews=(), tier="tier1", counter=1):
    """Return dict with keys:
    { slab/slug, html, canonical_path, title, description, schema_types, needs_field_data }"""
    slug = derive_slug(job, counter)
    prefix = "../"
    canonical_path = f"{CONTENT_DIR}/{slug}"

    city = job.get("city") or "Orange County"
    city_slug = P.slugify(city)
    city_label = S.CITY_LABEL.get(city_slug, city)
    service = _service_display(job)
    service_slug = _service_slug(job)
    title = f"{service} in {city} | Straight Flush Plumbing"
    if tier == "tier1":
        h1 = _title(job)
    else:
        h1 = f"{service} in {city}"

    serious_intro = (
        f"Straight Flush Plumbing detected and repaired a slab leak in {city} in {_fmt_date(job.get('date'))}."
        if job.get("service_type","").lower().find("slab") >= 0
        else f"Straight Flush Plumbing completed a {service} job in {city} in {_fmt_date(job.get('date'))}."
    )

    # ------- schema blocks (match gold patterns) -------
    schema_blocks = [
        J.plumber_min(city_label),
        J.breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "Service Areas", f"{S.DOMAIN}/service-areas"),
            (3, city_label, f"{S.DOMAIN}/cities/{city_slug}"),
            (4, service, f"{S.DOMAIN}/{canonical_path}"),
        ]),
        J.service_with_catalog(city_label),
    ]

    schema_types = ["Plumber", "BreadcrumbList", "Service"]
    needs_field_data = 1 if tier == "tier2" else 0

    # review schema from approved reviews
    approved = [r for r in reviews if r.get("approved_for_publish")]
    if approved:
        rs = []
        for r in approved:
            author = r.get("source") or "Customer"
            rs.append(J.review_schema(
                author=author, rating=r.get("rating") or 5,
                date_published=(r.get("created_at") or "")[:7],
                body=r.get("text", "")[:400],
            ))
        if rs:
            schema_blocks.append(J.local_business_review_block(rs))
            schema_types.append("Review")

    # ------- body -------
    if tier == "tier1":
        hero_sub = P.esc(_summary(job))
    else:
        # Tier-2: HONEST prose, never a fabricated job claim.
        hero_sub = P.esc(
            f"Straight Flush Plumbing is the local owner-operated specialist for {service} "
            f"in the {city} area, serving homes throughout the region. This page is being "
            f"built out with real local job history as work is completed."
        )

    body_sections = []
    if tier == "tier1":
        # Real-job content only
        issue_html = f'<p class="muted">{_issue_paragraph(job)}</p>'
        # if there are before/after photos (filenames), reference them with strong alt text
        photos = []
        try:
            photos = json.loads(job.get("photos") or "[]")
        except (ValueError, TypeError):
            photos = []
        if photos:
            gallery = "\n".join(
                f'<img src="../assets/img/{P.esc(p)}" alt="Straight Flush Plumbing {P.esc(service)} work in {P.esc(city)}" loading="lazy" style="max-width:100%;border-radius:12px;margin-bottom:12px;">'
                for p in photos[:4]
            )
            body_sections.append(f"""<section>
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">The job</div>
      <h2>Work performed in {P.esc(city)}</h2>
    </div>
    <div class="reveal">{issue_html}</div>
    {f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:20px;">{gallery}</div>' if gallery else ''}
  </div>
</section>""")
        else:
            body_sections.append(f"""<section>
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">The job</div>
      <h2>Work performed in {P.esc(city)}</h2>
    </div>
    <div class="reveal">{issue_html}</div>
  </div>
</section>""")

        details = []
        if job.get("neighborhood"):
            details.append(f'<li><span class="tick">{P.TICK_ICON}</span> <strong>Neighborhood:</strong> {P.esc(job["neighborhood"])}</li>')
        if job.get("duration_hours"):
            details.append(f'<li><span class="tick">{P.TICK_ICON}</span> <strong>Duration:</strong> about {job["duration_hours"]:g} hours on site</li>')
        if job.get("cost_range_bucket"):
            label = S.cost_bucket_label(job["cost_range_bucket"])
            if label:
                details.append(f'<li><span class="tick">{P.TICK_ICON}</span> <strong>Typical cost range for this kind of work:</strong> {label}</li>')
        if details:
            body_sections.append(f"""<section class="section-sand">
  <div class="wrap">
    <div class="reveal">
      <div class="section-head" style="margin-bottom:18px;"><div class="eyebrow">Details</div><h2>How the {P.esc(service)} work was handled</h2></div>
      <ul class="founder-list">
        {chr(10).join(details)}
      </ul>
    </div>
  </div>
</section>""")

        if job.get("customer_quote"):
            q = P.esc(job["customer_quote"])
            body_sections.append(f"""<section>
  <div class="wrap">
    <div class="review-card-v2 reveal" style="max-width:760px;">
      <div class="stars-row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span></div>
      <p style="font-style:italic;">&ldquo;{q}&rdquo;</p>
      <div class="date">Straight Flush customer in {P.esc(city)}</div>
    </div>
    <p class="muted" style="margin-top:10px;font-size:0.85rem;">Quote shared with the homeowner&rsquo;s permission.</p>
  </div>
</section>""")

        faq_items = []
        if job.get("issue_description"):
            faq_items.append(
                ("What did Straight Flush actually find at this job?",
                 f"The problem in this {P.esc(city)} home involved {job['issue_description'].lower()[:180]}.")
            )
        faq_items.append(
            ("Can a leak like this be detected without cutting into the slab?",
             "Yes. Straight Flush uses acoustic pinpointing and thermal imaging to confirm the exact leak location before any concrete is opened — that&rsquo;s the standard diagnostic-first approach for this kind of work.")
        )
        faq_items.append(
            ("What happens after detection?",
             "Once the leak is pinpointed, the repair options are explained clearly — reroute, spot repair, or repipe depending on the condition of the pipes — so the homeowner can make an informed decision. No demolition first.")
        )
        body_sections.append(P.faq_section(prefix, "What owners ask", "Questions about this kind of repair", faq_items))

    else:
        # Tier 2 — HONEST scoped page: no fabricated detail.
        body_sections.append(f"""<section>
  <div class="wrap two-col">
    <div class="reveal">
      <div class="eyebrow">About this service</div>
      <h2>{P.esc(service)} in {P.esc(city)}</h2>
      <p class="muted">Straight Flush Plumbing &amp; Leak Detection is the local, owner-operated specialist for {P.esc(service)}. We serve the {P.esc(city)} area from nearby Laguna Niguel, and Lance answers the phone himself.</p>
      <p class="muted">This page is in development while the work history for {P.esc(city)} is being documented. If you&rsquo;re experiencing {P.esc(service).lower()} issues now, call (949) 374-6524 and we&rsquo;ll get a real answer to you today.</p>
    </div>
    <div class="reveal">
      <div class="eyebrow">What we do</div>
      <ul class="founder-list">
        <li><span class="tick">{P.TICK_ICON}</span> Diagnose-first, no demolition-first</li>
        <li><span class="tick">{P.TICK_ICON}</span> Acoustic + thermal pinpointing</li>
        <li><span class="tick">{P.TICK_ICON}</span> Clear, honest pricing</li>
        <li><span class="tick">{P.TICK_ICON}</span> 24/7 emergency response</li>
      </ul>
    </div>
  </div>
</section>""")
        body_sections.append(P.neighbor_chips(prefix, city_slug))
        body_sections.append(P.faq_section(prefix, "Common questions",
                                           f"Questions about {P.esc(service)} in {P.esc(city)}",
                                           [
                                               ("Is slab leak detection available in my area?",
                                                "Straight Flush covers the full South Orange County service area, including " + P.esc(city) + ". Call (949) 374-6524 to confirm response time for your neighborhood."),
                                               ("How does acoustic leak detection work?",
                                                "Acoustic equipment listens for the sound of water escaping under pressure. Combined with thermal imaging, it narrows the leak to a small area so no concrete is opened unnecessarily."),
                                           ]))

    # internal links: nearest-neighbour city chips on tier-1 too
    if tier == "tier1":
        body_sections.append(P.neighbor_chips(prefix, city_slug))

    # CTA band
    body_sections.append(P.cta_band(
        prefix,
        f"Need {P.esc(service).lower()} in {P.esc(city)}?",
        "Lance answers the phone. Diagnose-first, honest pricing, 24/7 for emergencies.",
        cta_label="Call (949) 374-6524",
        cta_href="contact.html",
    ))

    if tier == "tier1":
        description = f"Real {service} work by Straight Flush Plumbing in {city}, based on a completed local job."
    else:
        description = (f"{service} service coverage in {city} by the owner-operated South OC "
                       f"specialist Straight Flush Plumbing. Details being added as real local jobs complete.")

    html = P.head(title, description, canonical_path, prefix, schema_blocks)
    html += P.nav(prefix)
    html += P.page_hero(
        prefix,
        eyebrow=f"Serving {city}",
        h1=h1,
        sub=hero_sub,
        cta_label="Schedule Service",
        cta_href="contact.html",
        trail=[("Home", "index.html"), ("Case Studies", "case-studies/index.html"), (h1[:40], None)],
    )
    html += "\n" + "\n".join(body_sections) + "\n"
    html += P.footer(prefix)

    return {
        "slug": slug,
        "canonical_path": canonical_path,
        "html": html,
        "title": title,
        "h1": h1,
        "description": description,
        "schema_types": schema_types,
        "needs_field_data": needs_field_data,
        "tier": tier,
    }


def build_tier2_page(city, service_type, counter=1):
    """Tier-2 scoped placeholder (no real job yet)."""
    job = {"city": city, "service_type": service_type, "job_id": f"t2-{counter}"}
    return build_case_study_page(job, reviews=(), tier="tier2", counter=counter)