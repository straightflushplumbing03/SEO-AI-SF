#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the AI-Authority module (master authority page + entity schema)."""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from modules.objects import site_data as S  # noqa: E402
from modules.objects import schema_jsonld as J  # noqa: E402
from modules.objects import authority_page as A  # noqa: E402


class TestSiteDataEntity(unittest.TestCase):
    def test_canonical_identity(self):
        self.assertEqual(S.BRAND, "Straight Flush Plumbing & Leak Detection")
        self.assertEqual(S.PHONE_DISPLAY, "(949) 374-6524")
        self.assertEqual(S.PHONE_TEL, "+19493746524")
        self.assertIn("Laguna Niguel, CA 92677", S.ADDRESS)
        self.assertEqual(S.FOUNDING_YEAR, "2019")
        self.assertEqual(S.PRIMARY_CATEGORY, "Plumber")

    def test_area_served_is_21_cities(self):
        # 21 + Orange = the site's published coverage list
        self.assertEqual(len(S.AREA_SERVED), 21)
        self.assertIn("Laguna Niguel", S.AREA_SERVED)
        self.assertIn("San Clemente", S.AREA_SERVED)

    def test_sameas_only_verified(self):
        # Must not contain placeholder URL values
        for url in S.SAMEAS_VERIFIED:
            self.assertTrue(url.startswith("https://"))
            self.assertNotIn("VERIFY", url)


class TestMasterSchema(unittest.TestCase):
    def _blocks(self):
        return J.master_authority_schema()

    def test_contains_all_types(self):
        types = [b["@type"] for b in self._blocks()]
        for expected in ("Organization", "Plumber", "WebSite", "BreadcrumbList"):
            self.assertIn(expected, types)

    def test_organization_sameas_verified_only(self):
        org = next(b for b in self._blocks() if b["@type"] == "Organization")
        self.assertEqual(set(org["sameAs"]), set(S.SAMEAS_VERIFIED))

    def test_plumber_nap_hours_and_offers(self):
        plumber = next(b for b in self._blocks() if b["@type"] == "Plumber")
        self.assertEqual(plumber["name"], "Straight Flush Plumbing & Leak Detection")
        self.assertEqual(plumber["address"]["postalCode"], "92677")
        self.assertEqual(plumber["foundingDate"], "2019")
        self.assertEqual(plumber["telephone"], "+19493746524")
        self.assertTrue(plumber["openingHoursSpecification"])
        self.assertTrue(plumber["makesOffer"])
        self.assertTrue(plumber["knowsAbout"])
        # areaServed is a list of City objects
        self.assertTrue(all(c["@type"] == "City" for c in plumber["areaServed"]))

    def test_website_refs_organization(self):
        ws = next(b for b in self._blocks() if b["@type"] == "WebSite")
        self.assertEqual(ws["publisher"]["@id"], f"{S.DOMAIN}/#organization")

    def test_all_blocks_serialize(self):
        for b in self._blocks():
            json.dumps(b)


class TestAuthorityPage(unittest.TestCase):
    def setUp(self):
        self.result = A.build_authority_page()

    def test_page_shape(self):
        r = self.result
        self.assertEqual(r["slug"], "straight-flush-plumbing-orange-county")
        self.assertEqual(r["canonical_path"], "about/straight-flush-plumbing-orange-county")
        self.assertIn("Orange County Plumbing & Leak Detection", r["title"])
        for expected_type in ("Organization", "Plumber", "WebSite", "BreadcrumbList"):
            self.assertIn(expected_type, r["schema_types"])

    def test_canonical_and_nap_present(self):
        html = self.result["html"]
        self.assertIn(
            'canonical" href="https://straightflushplumbingoc.com/about/'
            'straight-flush-plumbing-orange-county"', html)
        self.assertIn("78 Cameray Heights", html)
        self.assertIn("(949) 374-6524", html)

    def test_jsonld_blocks_valid_and_unique(self):
        html = self.result["html"]
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            html, flags=re.S)
        self.assertEqual(len(blocks), 4)
        types = set()
        for b in blocks:
            d = json.loads(b)
            types.add(d["@type"])
            json.dumps(d)  # serializable
        self.assertEqual(types, {"Organization", "Plumber", "WebSite", "BreadcrumbList"})

    def test_internal_links_resolve_to_real_files(self):
        """Every local href target must exist in the site repo checkout."""
        site_dir = os.environ.get("SFGE_SITE_DIR", "")
        if not site_dir:
            self.skipTest("SFGE_SITE_DIR not set (site checkout not available)")
        html = self.result["html"]
        hrefs = set(re.findall(r'href="\.\./([^"#]+)"', html))
        for h in hrefs:
            self.assertTrue(
                os.path.exists(os.path.join(site_dir, h)),
                f"broken link target: {h}",
            )

    def test_brand_not_shortened_in_body(self):
        html = self.result["html"]
        # canonical long name used in the page body
        self.assertIn("Straight Flush Plumbing &amp; Leak Detection", html)


if __name__ == "__main__":
    unittest.main()