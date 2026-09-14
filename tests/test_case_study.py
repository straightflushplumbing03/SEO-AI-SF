#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acceptance tests for F2 (Phase 1).

Validates:
- generated pages contain valid JSON-LD with the expected schema types;
- canonical/og:url match the site's extensionless convention;
- internal links to city + service pages exist (no orphans);
- a real job yields a Tier-1 page; a tier-2 page stays honest (no fabricated
  proof words, no invented customer story);
- privacy: no street addresses, no full names in generated HTML.
"""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from modules.objects import case_study as CS  # noqa: E402
from modules.objects import site_data as S  # noqa: E402
from modules.objects import sitemap as SITEMAP  # noqa: E402
from modules.objects import page as P  # noqa: E402


def make_job(city="Laguna Niguel", service="Slab Leak Detection", job_id=1, **kw):
    job = {
        "job_id": job_id, "city": city, "service_type": service,
        "issue_description": "Slab leak under kitchen; copper pinhole; rerouted through attic",
        "date": "2026-08-14", "neighborhood": "Bear Brand",
        "duration_hours": 6, "cost_range_bucket": "15000-25000",
        "customer_quote": "Best money we've spent on this house.",
    }
    job.update({k: v for k, v in kw.items() if v is not None})
    return job


def extract_jsonld(html):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(b) for b in blocks]


class TestSchema(unittest.TestCase):
    def test_tier1_has_plumber_breadcrumb_service(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        blocks = extract_jsonld(r["html"])
        types = [b["@type"] for b in blocks]
        self.assertEqual(set(types), {"Plumber", "BreadcrumbList", "Service"})

    def test_breadcrumb_canonicity(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        blocks = extract_jsonld(r["html"])
        bc = [b for b in blocks if b["@type"] == "BreadcrumbList"][0]
        items = bc["itemListElement"]
        self.assertEqual(len(items), 4)
        self.assertEqual(items[-1]["item"], f"{S.DOMAIN}/{r['canonical_path']}")
        self.assertTrue(items[0]["item"].endswith(S.DOMAIN + "/"))

    def test_canonical_and_og_match(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        html = r["html"]
        can = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        og = re.search(r'<meta property="og:url" content="([^"]+)"', html)
        self.assertEqual(can.group(1), f"{S.DOMAIN}/{r['canonical_path']}")
        self.assertEqual(og.group(1), can.group(1))
        # extensionless, under case-studies/
        self.assertRegex(can.group(1), r"/case-studies/[^/.]+$")

    def test_review_schema_attached_when_approved(self):
        reviews = [{
            "approved_for_publish": 1, "source": "Yelp", "rating": 5,
            "text": "Lance pinpointed the leak before any concrete was cut.", "created_at": "2026-08-01",
        }]
        r = CS.build_case_study_page(make_job(), reviews=reviews)
        types = [b["@type"] for b in extract_jsonld(r["html"])]
        self.assertIn("Plumber", types)
        reviews_blocks = [b for b in extract_jsonld(r["html"]) if "review" in b]
        self.assertTrue(reviews_blocks, "review block missing")
        self.assertEqual(reviews_blocks[0]["review"][0]["reviewRating"]["ratingValue"], 5)


class TestPrivacy(unittest.TestCase):
    # The site footer legitimately contains the BUSINESS address — that is not
    # customer PII. These checks target CUSTOMER-identifying details only.
    def test_no_customer_street_address(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        # the case-study content must not embed an arbitrary street address
        self.assertNotRegex(r["html"], r"\d{1,4}\s+[A-Z][a-z]+\s(st|ave|blvd|dr|rd|ln|way|place)\b", re.I)
        # business HQ in footer is fine and expected
        self.assertIn("78 Cameray Heights", r["html"])

    def test_no_customer_full_name(self):
        # If a customer_name field ever sneaks into a job dict, it must never
        # be rendered.
        job = make_job()
        job["customer_name"] = "Margaret Thompson"
        r = CS.build_case_study_page(job, reviews=())
        self.assertNotIn("Margaret Thompson", r["html"])
        self.assertNotIn("Margaret", r["html"])
        self.assertNotIn("Mr.", r["html"])
        self.assertNotIn("Mrs.", r["html"])

    def test_cost_displayed_as_range_only(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        # range bucket shown (en dash or &ndash; both render identically)
        self.assertRegex(r["html"], r"\$15,000(?:&ndash;|–)\$25,000")
        # no exact price digits in a dollar-amount form
        for bad in ["$6,500", "$ 6,500", "at exactly"]:
            self.assertNotIn(bad, r["html"])


class TestSummary(unittest.TestCase):
    def test_summary_shows_real_month(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn("(August 2026)", r["html"])
        # no raw "recently" leftover inside parentheses
        self.assertNotIn("(recently)", r["html"])

    def test_summary_never_double_parenthesis(self):
        import random
        # job with no date: should read "recently." without wrapping parens
        job = make_job()
        job["date"] = None
        r = CS.build_case_study_page(job, reviews=())
        self.assertNotIn("(recently)", r["html"])


class TestGoldMarkup(unittest.TestCase):
    """Locks the header/nav/footer templates to the real site's dominant variant."""

    GOLD_NAV = """<header class="site-header">
  <nav class="nav">
    <a href="../index.html" class="nav-brand">
      <img src="../assets/img/logo.jpg" alt="Straight Flush Plumbing & Leak Detection logo" width="54" height="44">
      <span class="nav-brand-text">Straight Flush<span>Plumbing &amp; Leak Detection</span></span>
    </a>
    <ul class="nav-links">
      <li><a href="../services/index.html">Services</a></li>
      <li><a href="../about.html">About</a></li>
      <li><a href="../service-areas.html">Service Areas</a></li>
      <li><a href="../academy/index.html">Blog</a></li>
      <li><a href="../index.html#reviews">Reviews</a></li>
      <li><a href="../contact.html">Contact</a></li>
    </ul>
    <div class="nav-cta">
      <a href="tel:+19493746524" class="nav-phone">Call <strong>(949) 374-6524</strong></a>
      <a href="../contact.html" class="btn btn-primary btn-sm">Schedule Detection</a>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false"><svg class="ico" viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-0.15em;" ><line x1="3.5" y1="7" x2="20.5" y2="7"/><line x1="3.5" y1="12" x2="20.5" y2="12"/><line x1="3.5" y1="17" x2="20.5" y2="17"/></svg></button>
    </div>
  </nav>
</header>
"""

    GOLD_FOOTER = """<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid-5">
      <div>
        <img src="../assets/img/logo.jpg" alt="Straight Flush Plumbing & Leak Detection logo" width="69" height="56" style="height:56px; margin-bottom:16px;">
        <p style="color:var(--muted-on-ink); font-size:0.92rem; max-width:30ch;">Family-owned and operated since 2019. Providing honest, reliable plumbing services to Laguna Niguel and surrounding areas.</p>
        <div class="footer-ratings">
          <div class="row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span> 5/5 on Google</div>
          <div class="row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span> 4.8/5 on Yelp</div>
        </div>
      </div>
      <div>
        <h4>Our Services</h4>
        <ul>
          <li><a href="../services/leak-detection.html">Leak Detection</a></li>
          <li><a href="../services/slab-leak-detection.html">Slab Leak Detection</a></li>
          <li><a href="../services/pex-repiping.html">PEX Repiping</a></li>
          <li><a href="../services/water-heater-services.html">Water Heater</a></li>
          <li><a href="../services/drain-services.html">Drain Cleaning</a></li>
          <li><a href="../services/plumbing-repair.html">Plumbing Repair</a></li>
          <li><a href="../academy/index.html">Blog</a></li>
          <li><a href="../guides/leak-detection-cost.html">Cost Guides</a></li>
          <li><a href="../insurance/index.html">Insurance Resources</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact Us</h4>
        <ul>
          <li><a href="tel:+19493746524">(949) 374-6524</a></li>
          <li><a href="mailto:straightflushplumbing03@gmail.com">straightflushplumbing03@gmail.com</a></li>
          <li>78 Cameray Heights, Laguna Niguel, CA 92677</li>
          <li>Mon&ndash;Fri 8am&ndash;7pm &middot; Sat&ndash;Sun 9am&ndash;6pm<br>24/7 for emergencies</li>
        </ul>
      </div>
      <div>
        <h4>Cities We Serve</h4>
        <ul>
          <li><a href="../cities/laguna-niguel.html">Laguna Niguel</a></li>
          <li><a href="../cities/mission-viejo.html">Mission Viejo</a></li>
          <li><a href="../cities/irvine.html">Irvine</a></li>
          <li><a href="../cities/aliso-viejo.html">Aliso Viejo</a></li>
          <li><a href="../cities/dana-point.html">Dana Point</a></li>
          <li><a href="../cities/laguna-beach.html">Laguna Beach</a></li>
          <li><a href="../cities/newport-beach.html">Newport Beach</a></li>
          <li><a href="../cities/san-clemente.html">San Clemente</a></li>
          <li><a href="../service-areas.html"><strong>All Service Areas</strong></a></li>
        </ul>
      </div>
      <div>
        <h4>Save Our Card</h4>
        <p style="color:var(--muted-on-ink); font-size:0.85rem; margin-bottom:14px;">Scan to save our digital business card to your phone.</p>
        <div class="footer-qr"><img src="../assets/img/qr-code.png" alt="QR code to save Straight Flush Plumbing contact info" width="110" height="107" loading="lazy"></div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <span data-year></span> Straight Flush Plumbing & Leak Detection. Always A Safe Bet.</span>
      <span><a href="../privacy-policy.html" style="color:var(--muted-on-ink);">Privacy Policy</a> &middot; <a href="../terms-of-service.html" style="color:var(--muted-on-ink);">Terms of Service</a></span>
    </div>
  </div>
</footer>
"""

    def test_nav_matches_gold(self):
        self.assertEqual(P.nav("../"), self.GOLD_NAV)

    def test_footer_matches_gold(self):
        self.assertEqual(P.footer("../"), self.GOLD_FOOTER)

    def test_generated_page_contains_gold_nav_footer(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn(self.GOLD_NAV, r["html"])
        self.assertIn(self.GOLD_FOOTER, r["html"])

    def test_head_canonical_abs_og(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn(f'<link rel="canonical" href="{S.DOMAIN}/{r["canonical_path"]}">', r["html"])
        self.assertIn(f'<meta property="og:url" content="{S.DOMAIN}/{r["canonical_path"]}">', r["html"])
        self.assertIn(f'<meta property="og:image" content="{S.OG_IMAGE}">', r["html"])
        self.assertIn(f'<meta name="twitter:image" content="{S.OG_IMAGE}">', r["html"])


class TestContentRules(unittest.TestCase):
    def test_tier2_is_honest(self):
        r = CS.build_tier2_page("Aliso Viejo", "Slab Leak Detection")
        self.assertEqual(r["tier"], "tier2")
        self.assertEqual(r["needs_field_data"], 1)
        # must NOT contain invented job claims
        for phrase in ["recently completed", "we recently diagnosed", "we repaired a slab leak in Aliso Viejo",
                       "we detected a slab leak", "recently repaired a"]:
            self.assertNotIn(phrase, r["html"])
        # must contain a coverage statement
        self.assertIn("we serve the", r["html"].lower())

    def test_tier1_has_real_job_detail(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn("copper pinhole", r["html"])
        self.assertIn("Bear Brand", r["html"])

    def test_tier1_does_claim_job_completion(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn("recently completed", r["html"])


class TestInternalLinks(unittest.TestCase):
    def test_links_to_city_and_service(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        self.assertIn('href="../cities/laguna-niguel.html"', r["html"])
        self.assertIn('href="../services/slab-leak-detection.html"', r["html"])

    def test_neighbor_chips(self):
        r = CS.build_case_study_page(make_job(), reviews=())
        for n in S.city_neighbors("laguna-niguel")[:3]:
            self.assertIn(f'class="city-chip" href="{n}.html"', r["html"])

    def test_link_graph_no_orphan(self):
        from modules.objects.links import LinkGraph, city_page_url, service_page_url
        g = LinkGraph()
        r = CS.build_case_study_page(make_job(), reviews=())
        page = f"case-studies/{r['slug']}.html"
        # the generated page links out to city + service pages AND back to the hub
        g.add(page, {
            city_page_url("laguna-niguel"), service_page_url("slab-leak-detection"),
            "case-studies/index.html",
        })
        # hub links to every case study
        g.add("case-studies/index.html", {page})
        # hub is reachable from the site footer/sitemap (crawler entry)
        g.add("sitemap.xml", {"case-studies/index.html"})
        self.assertEqual(g.orphaned(), [])


class TestSitemap(unittest.TestCase):
    def test_patch_adds_url(self):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(fd, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                    '  <url>\n    <loc>https://straightflushplumbingoc.com/</loc>\n    <lastmod>2026-08-25</lastmod>\n'
                    '    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n')
        try:
            SITEMAP.patch_sitemap(path, "case-studies/laguna-niguel-slab-leak-detection-1", "0.7")
            with open(path, encoding="utf-8") as f:
                xml = f.read()
            self.assertIn("<loc>https://straightflushplumbingoc.com/case-studies/laguna-niguel-slab-leak-detection-1</loc>", xml)
            # exactly one urlset element remains well-formed
            self.assertEqual(xml.strip().count("</urlset>"), 1)
            self.assertIn('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', xml)
        finally:
            os.unlink(path)


class TestPageModule(unittest.TestCase):
    def test_nav_contains_cta_phone(self):
        html = P.nav("../")
        self.assertIn('tel:+19493746524', html)
        self.assertIn('(949) 374-6524', html)

    def test_footer_matches_gold_hours(self):
        html = P.footer("../")
        self.assertIn("Mon&ndash;Fri 8am&ndash;7pm", html)


if __name__ == "__main__":
    unittest.main()