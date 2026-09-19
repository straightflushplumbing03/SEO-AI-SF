#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
City page tests.

Two jobs:
  1. Guard the content model: only verified facts, no fabricated fields.
  2. Guard against near-duplicate city pages — the failure mode the brief
     explicitly forbids (11 copies of one article).
"""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.objects import city_data as C  # noqa: E402
from modules.objects import city_page as CP  # noqa: E402
from modules.objects import schema_jsonld as J  # noqa: E402

TARGET_CITIES = [
    "laguna-niguel", "san-clemente", "dana-point", "mission-viejo",
    "ladera-ranch", "laguna-hills", "aliso-viejo", "lake-forest",
    "dove-canyon", "coto-de-caza", "rancho-santa-margarita",
]

# Phrases that would signal an unverified or prohibited marketing claim.
FORBIDDEN = [
    "best plumber", "the best", "#1", "number one", "top rated", "award",
    "certified", "licensed", "insured", "guarantee", "years of experience",
    "5-star", "fastest", "cheapest", "we invented", "industry-leading",
]


class TestCityData(unittest.TestCase):
    def test_all_target_cities_present(self):
        for slug in TARGET_CITIES:
            self.assertIn(slug, C.CITY_FACTS, f"missing city data for {slug}")

    def test_every_city_has_core_facts(self):
        for slug in TARGET_CITIES:
            f = C.facts(slug)
            self.assertTrue(f["name"], slug)
            self.assertTrue(f["zips"], slug)
            self.assertTrue(f["era"], slug)
            self.assertTrue(f["notes"], slug)
            self.assertTrue(f["landmarks"], slug)
            self.assertTrue(f["focus"], slug)
            self.assertTrue(f["typical_call"], slug)

    def test_zips_look_like_ca_zips(self):
        for slug in TARGET_CITIES:
            for z in C.facts(slug)["zips"]:
                self.assertRegex(z, r"^92\d{3}$", f"{slug}: {z}")

    def test_focus_values_are_known_services(self):
        known = {"leak_detection", "slab_leak", "water_line", "repiping",
                 "plumbing_repair", "water_heater"}
        for slug in TARGET_CITIES:
            for foc in C.facts(slug)["focus"]:
                self.assertIn(foc, known, f"{slug}: {foc}")

    def test_unincorporated_cities_declared_as_none(self):
        for slug in ("ladera-ranch", "dove-canyon", "coto-de-caza"):
            self.assertIsNone(C.facts(slug)["incorporated"],
                              f"{slug} should be unincorporated/CDP")
            self.assertFalse(C.is_incorporated(slug))


class TestCityPageContent(unittest.TestCase):
    def _page(self, slug):
        return CP.build_city_page(slug)

    def test_page_has_single_h1(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"]
            self.assertEqual(len(re.findall(r"<h1[^>]*>", html)), 1, slug)

    def test_title_and_description_unique(self):
        titles = [self._page(s)["title"] for s in TARGET_CITIES]
        descs = [self._page(s)["description"] for s in TARGET_CITIES]
        self.assertEqual(len(set(titles)), len(TARGET_CITIES))
        self.assertEqual(len(set(descs)), len(TARGET_CITIES))

    def test_canonical_is_city_url(self):
        for slug in TARGET_CITIES:
            p = self._page(slug)
            self.assertEqual(p["canonical_path"], f"cities/{slug}")
            self.assertIn(f'canonical" href="{C.S.DOMAIN}/cities/{slug}"',
                          p["html"])

    def test_all_required_sections_present(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"]
            name = C.facts(slug)["name"]
            for heading in (
                f"Leak Detection in {name}",
                f"Slab Leak Detection in {name}",
                f"Whole-House Repiping in {name}",
                f"Plumbing Services in {name}",
                f"Where We Work in {name}",
                "Why Homeowners Call Straight Flush",
            ):
                self.assertIn(heading, html, f"{slug} missing: {heading}")

    def test_structured_data_types(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"]
            types = []
            for b in re.findall(r"application/ld\+json[^>]*>(.*?)</script>",
                                html, re.S):
                types.append(json.loads(b)["@type"])
            self.assertIn("Plumber", types, slug)
            self.assertIn("Service", types, slug)
            self.assertIn("FAQPage", types, slug)
            self.assertIn("BreadcrumbList", types, slug)

    def test_service_provider_references_canonical_business(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"]
            for b in re.findall(r"application/ld\+json[^>]*>(.*?)</script>",
                                html, re.S):
                d = json.loads(b)
                if d["@type"] == "Service":
                    self.assertEqual(d["provider"], {"@id": C.S.BUSINESS_ID},
                                     slug)

    def test_faq_answers_are_substantive(self):
        for slug in TARGET_CITIES:
            for q, a in CP._faqs(slug):
                self.assertGreater(len(q.split()), 4, slug)
                self.assertGreater(len(a.split()), 15,
                                   f"{slug}: answer too thin for {q!r}")

    def test_no_forbidden_claims(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"].lower()
            for phrase in FORBIDDEN:
                self.assertNotIn(
                    phrase, html,
                    f"{slug} contains unverified claim: {phrase!r}")

    def test_no_fabricated_projects_or_reviews(self):
        """No project/review claims may appear until real records exist."""
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"].lower()
            for phrase in ("recent project", "recently completed", "our customer",
                           "testimonial", "review from"):
                self.assertNotIn(phrase, html, f"{slug}: {phrase!r}")

    def test_does_not_claim_local_office(self):
        for slug in TARGET_CITIES:
            html = self._page(slug)["html"]
            self.assertNotIn("our office in", html.lower(), slug)
            # The landmark section must disclaim offices explicitly.
            self.assertIn("not office locations", html, slug)


class TestCityPageUniqueness(unittest.TestCase):
    """The brief forbids near-duplicate city pages. These tests enforce it."""

    def _maintext(self, slug):
        html = CP.build_city_page(slug)["html"]
        html = html.split("</header>", 1)[1].split("<footer", 1)[0]
        html = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S)
        html = re.sub(r"<[^>]+>", " ", html)
        for e, r in (("&amp;", "&"), ("&mdash;", " "), ("&ldquo;", ""),
                     ("&rdquo;", ""), ("&rsaquo;", " ")):
            html = html.replace(e, r)
        return re.sub(r"\s+", " ", html).strip()

    def test_each_city_faq_set_is_distinct(self):
        sets = {}
        for slug in TARGET_CITIES:
            qs = tuple(q for q, _ in CP._faqs(slug))
            sets.setdefault(qs, []).append(slug)
        dupes = {k: v for k, v in sets.items() if len(v) > 1}
        self.assertEqual(dupes, {}, f"identical FAQ sets across cities: {dupes}")

    def test_local_context_sentences_are_not_shared(self):
        """Every city's opening local-context paragraph must be its own."""
        seen = {}
        for slug in TARGET_CITIES:
            note = C.facts(slug)["notes"]
            self.assertNotIn(note, seen, f"{slug} duplicates {seen.get(note)}")
            seen[note] = slug

    def test_pages_are_substantial(self):
        for slug in TARGET_CITIES:
            words = len(self._maintext(slug).split())
            self.assertGreater(words, 700,
                               f"{slug} main content only {words} words")


if __name__ == "__main__":
    unittest.main()