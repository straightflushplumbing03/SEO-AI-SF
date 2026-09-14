#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold-compatible page composer.

Clones the EXACT head/nav/footer markup from the published site
(cities/laguna-niguel.html, academy/what-is-a-slab-leak.html) so generated
pages are byte-compatible with what Cloudflare serves. Use ONLY the patterns
below; they reflect the on-disk ground truth, not the (out-of-date) build.py.

Key conventions (from the live site):
- Canonical/og:url are extensionless paths, no trailing slash except hubs:
    /cities/laguna-niguel          /academy/          /services/ ...
- Assets referenced relative to the page's folder depth via `prefix` ("../").
- Schema emitted as separate <script type="application/ld+json"> blocks in head.
- Inline SVG icons emitted directly (site runs icon_defs.apply_icons at build).
"""
import html as html_module
import textwrap
import re

from . import site_data as S

TICK_ICON = ('<svg class="ico" viewBox="0 0 24 24" width="1em" height="1em" '
             'fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round" '
             'style="display:inline-block;vertical-align:-0.15em;" >'
             '<path d="M4 12.5l5 5L20 6"/></svg>')

MENU_ICON = ('<svg class="ico" viewBox="0 0 24 24" width="1em" height="1em" '
             'fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round" '
             'style="display:inline-block;vertical-align:-0.15em;" >'
             '<line x1="3.5" y1="7" x2="20.5" y2="7"/>'
             '<line x1="3.5" y1="12" x2="20.5" y2="12"/>'
             '<line x1="3.5" y1="17" x2="20.5" y2="17"/></svg>')


def esc(t):
    return html_module.escape(str(t), quote=True)


def head(title, description, canonical, prefix, schema_blocks=()):
    """schema_blocks: iterable of JSON-LD dicts. Titles/descriptions are escaped."""
    blocks = "\n".join(
        '<script type="application/ld+json">\n%s\n</script>' % textwrap.indent(
            _compact_json(sb), "  " if "\n" in _compact_json(sb) else ""
        )
        for sb in schema_blocks
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{S.DOMAIN}/{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{S.DOMAIN}/{canonical}">
<meta property="og:image" content="{S.OG_IMAGE}">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{S.OG_IMAGE}">
<link rel="icon" href="{prefix}assets/img/logo.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{prefix}assets/css/style.css">
{blocks}
</head>
<body>
"""


def _compact_json(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)


def nav(prefix):
    items = [
        ("services/index.html", "Services"),
        ("about.html", "About"),
        ("service-areas.html", "Service Areas"),
        ("academy/index.html", "Blog"),
        ("index.html#reviews", "Reviews"),
        ("contact.html", "Contact"),
    ]
    links = "\n".join(
        f'      <li><a href="{prefix}{href}">{label}</a></li>' for href, label in items
    )
    return f"""<header class="site-header">
  <nav class="nav">
    <a href="{prefix}index.html" class="nav-brand">
      <img src="{prefix}assets/img/logo.jpg" alt="Straight Flush Plumbing & Leak Detection logo" width="54" height="44">
      <span class="nav-brand-text">Straight Flush<span>Plumbing &amp; Leak Detection</span></span>
    </a>
    <ul class="nav-links">
{links}
    </ul>
    <div class="nav-cta">
      <a href="tel:{S.PHONE_TEL}" class="nav-phone">Call <strong>{S.PHONE_DISPLAY}</strong></a>
      <a href="{prefix}contact.html" class="btn btn-primary btn-sm">Schedule Detection</a>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false">{MENU_ICON}</button>
    </div>
  </nav>
</header>
"""


def footer(prefix):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid-5">
      <div>
        <img src="{prefix}assets/img/logo.jpg" alt="Straight Flush Plumbing & Leak Detection logo" width="69" height="56" style="height:56px; margin-bottom:16px;">
        <p style="color:var(--muted-on-ink); font-size:0.92rem; max-width:30ch;">Family-owned and operated since 2019. Providing honest, reliable plumbing services to Laguna Niguel and surrounding areas.</p>
        <div class="footer-ratings">
          <div class="row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span> 5/5 on Google</div>
          <div class="row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span> 4.8/5 on Yelp</div>
        </div>
      </div>
      <div>
        <h4>Our Services</h4>
        <ul>
          <li><a href="{prefix}services/leak-detection.html">Leak Detection</a></li>
          <li><a href="{prefix}services/slab-leak-detection.html">Slab Leak Detection</a></li>
          <li><a href="{prefix}services/pex-repiping.html">PEX Repiping</a></li>
          <li><a href="{prefix}services/water-heater-services.html">Water Heater</a></li>
          <li><a href="{prefix}services/drain-services.html">Drain Cleaning</a></li>
          <li><a href="{prefix}services/plumbing-repair.html">Plumbing Repair</a></li>
          <li><a href="{prefix}academy/index.html">Blog</a></li>
          <li><a href="{prefix}guides/leak-detection-cost.html">Cost Guides</a></li>
          <li><a href="{prefix}insurance/index.html">Insurance Resources</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact Us</h4>
        <ul>
          <li><a href="tel:{S.PHONE_TEL}">{S.PHONE_DISPLAY}</a></li>
          <li><a href="mailto:{S.EMAIL}">{S.EMAIL}</a></li>
          <li>{S.ADDRESS}</li>
          <li>Mon&ndash;Fri 8am&ndash;7pm &middot; Sat&ndash;Sun 9am&ndash;6pm<br>24/7 for emergencies</li>
        </ul>
      </div>
      <div>
        <h4>Cities We Serve</h4>
        <ul>
          <li><a href="{prefix}cities/laguna-niguel.html">Laguna Niguel</a></li>
          <li><a href="{prefix}cities/mission-viejo.html">Mission Viejo</a></li>
          <li><a href="{prefix}cities/irvine.html">Irvine</a></li>
          <li><a href="{prefix}cities/aliso-viejo.html">Aliso Viejo</a></li>
          <li><a href="{prefix}cities/dana-point.html">Dana Point</a></li>
          <li><a href="{prefix}cities/laguna-beach.html">Laguna Beach</a></li>
          <li><a href="{prefix}cities/newport-beach.html">Newport Beach</a></li>
          <li><a href="{prefix}cities/san-clemente.html">San Clemente</a></li>
          <li><a href="{prefix}service-areas.html"><strong>All Service Areas</strong></a></li>
        </ul>
      </div>
      <div>
        <h4>Save Our Card</h4>
        <p style="color:var(--muted-on-ink); font-size:0.85rem; margin-bottom:14px;">Scan to save our digital business card to your phone.</p>
        <div class="footer-qr"><img src="{prefix}assets/img/qr-code.png" alt="QR code to save Straight Flush Plumbing contact info" width="110" height="107" loading="lazy"></div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year></span> {S.BRAND}. {S.SLOGAN}.</span>
      <span><a href="{prefix}privacy-policy.html" style="color:var(--muted-on-ink);">Privacy Policy</a> &middot; <a href="{prefix}terms-of-service.html" style="color:var(--muted-on-ink);">Terms of Service</a></span>
    </div>
  </div>
</footer>
"""


def breadcrumbs(prefix, trail):
    """trail: list of (label, href_or_None)."""
    parts = []
    for label, href in trail:
        if href:
            parts.append(f'<a href="{prefix}{href}">{esc(label)}</a>')
        else:
            parts.append(f'<span>{esc(label)}</span>')
    return '<div class="breadcrumbs">' + ' &rsaquo; '.join(parts) + '</div>'


def page_hero(prefix, eyebrow, h1, sub, cta_label="Schedule Service", cta_href="contact.html", trail=None):
    trail = trail or [("Home", "index.html"), (None, None)]
    return f"""<section class="hero" style="padding-bottom:90px;">
  <div class="wrap">
    {breadcrumbs(prefix, trail)}
    <div class="hero-eyebrow"><span class="dot"></span> {esc(eyebrow)}</div>
    <h1 style="max-width:22ch;">{esc(h1)}</h1>
    <p class="hero-sub">{sub}</p>
    <div class="hero-ctas"><a href="{prefix}{cta_href}" class="btn btn-primary">{esc(cta_label)}</a></div>
  </div>
</section>
"""


def cta_band(prefix, heading, sub, cta_label="Schedule Now", cta_href="contact.html", dark=False):
    bg = ' style="background:var(--ink);"' if dark else ''
    return f"""<section>
  <div class="wrap">
    <div class="cta-band reveal"{bg}>
      <div>
        <h2>{esc(heading)}</h2>
        <p>{sub}</p>
      </div>
      <a href="{prefix}{cta_href}" class="btn btn-primary">{esc(cta_label)}</a>
    </div>
  </div>
</section>
"""


def faq_section(prefix, eyebrow, heading, items):
    """items: list of (question, answer_html). answer_html already escaped."""
    blocks = []
    for q, a in items:
        blocks.append(f"""      <div class="faq-item">
        <button class="faq-q" aria-expanded="false">{esc(q)}<span class="plus">+</span></button>
        <div class="faq-a"><p>{a}</p></div>
      </div>""")
    body = "\n".join(blocks)
    return f"""<section class="section-sand">
  <div class="wrap">
    <div class="faq reveal">
      <div class="section-head" style="margin-bottom:30px;">
        <div class="eyebrow">{esc(eyebrow)}</div>
        <h2>{esc(heading)}</h2>
      </div>
{body}
    </div>
  </div>
</section>
"""


def neighbor_chips(prefix, city_slug):
    """City-chip grid linking to nearest neighbors, matching the gold pattern."""
    chips = []
    for n in S.city_neighbors(city_slug):
        if S.is_valid_city(n):
            chips.append(
                f'<a class="city-chip" href="{n}.html">{S.CITY_LABEL[n]} <span>&rarr;</span></a>'
            )
        else:
            chips.append(
                f'<a class="city-chip" href="../service-areas.html">{S.CITY_LABEL.get(n, n).title()} <span>&rarr;</span></a>'
            )
    return f"""<section class="section-sand">
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">Nearby areas we also serve</div>
      <h2>Also serving communities near {esc(S.CITY_LABEL.get(city_slug, city_slug))}</h2>
    </div>
    <div class="city-grid reveal">
      {"\n".join(chips)}
    </div>
  </div>
</section>
"""


def tick_list(items):
    return "\n".join(
        f'<li><span class="tick">{TICK_ICON}</span> {item}</li>' for item in items
    )


def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s or "page"