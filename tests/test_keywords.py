#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 3 (Modules A + B) tests."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from db import get_db  # noqa: E402
from modules.objects import keywords as K  # noqa: E402
from modules.objects import blog_gen as BG  # noqa: E402
from modules.objects import case_study as CS  # noqa: E402


class TestKeywords(unittest.TestCase):
    def test_cluster_size(self):
        kws = K.cluster_keywords("Laguna Niguel")
        # 4 services x (7 commercial + 8 informational + 5 emergency) = 80
        self.assertEqual(len(kws), 80)
        self.assertTrue(all(k["city"] == "Laguna Niguel" for k in kws))
        intents = {k["intent_type"] for k in kws}
        self.assertEqual(intents, {"commercial", "informational", "emergency"})

    def test_volume_difficulty_range(self):
        kws = K.cluster_keywords("Irvine")
        self.assertTrue(all(k["search_volume"] > 0 for k in kws))
        self.assertTrue(all(0 <= k["difficulty"] <= 1 for k in kws))

    def test_all_cities_generate(self):
        all_kws = K.generate_all()
        self.assertEqual(len(set(k["city"] for k in all_kws)), len(K.S.CITY_LABEL))
        # no duplicate keyword/city/service combos
        seen = set()
        for k in all_kws:
            key = (k["keyword"], k["city"], k["service_type"])
            self.assertNotIn(key, seen)
            seen.add(key)

    def test_paa_questions(self):
        qs = K.paa_questions("Slab Leak Detection", "Mission Viejo")
        self.assertTrue(any("Mission Viejo" in q for q in qs))


class TestOpportunityBuild(unittest.TestCase):
    def test_opportunity_priority_and_content_gate(self):
        import build_opportunities as BO
        db = get_db(os.path.join(tempfile.mkdtemp(), "t.db"))
        db.init_schema()
        # existing content for Laguna Niguel / Slab Leak Detection -> that
        # combo must be skipped when seeding opportunities.
        db.execute("""INSERT INTO content (type, tier, city, service_type, site_path,
                                           canonical_url, title, schema_types, publish_status)
                      VALUES ('city_page','tier1','Laguna Niguel','Slab Leak Detection',
                              'cities/laguna-niguel.html','https://x','t','[]','live')""")
        # module-level funcs use the module's db path; monkeypatch the module's
        # global get_db to return ours so we can inspect results.
        orig = BO.get_db
        BO.get_db = lambda *a, **k: db
        try:
            inserted = BO.seed_opportunities(db)
            # at least one keyword seeded
            self.assertGreater(inserted, 0)
            # no row for the existing-combo city/service
            n = db.scalar(
                "SELECT COUNT(*) FROM opportunities WHERE city=? AND service_type=?",
                ("Laguna Niguel", "Slab Leak Detection"),
            )
            self.assertEqual(n, 0)
            # priority scores are non-negative & sortable
            top = db.rows("SELECT * FROM opportunities ORDER BY priority_score DESC")
            self.assertTrue(all(float(r["priority_score"]) >= 0 for r in top))
        finally:
            BO.get_db = orig
            db.close()


class TestBlogGeneration(unittest.TestCase):
    def test_comparison_page_build(self):
        r = BG.build_comparison_page("slab-vs-general-leak", [], [])
        self.assertEqual(r["type"], "blog")
        self.assertIn("Slab Leak vs. General Leak", r["title"])
        self.assertIn("FAQPage", r["schema_types"])
        self.assertIn("application/ld+json", r["html"])
        self.assertIn("academy", r["canonical_path"])
        self.assertIn("slab-leak-vs-general-leak", r["slug"])

    def test_tier1_uses_real_proof(self):
        jobs = [{"city": "Mission Viejo", "service_type": "PEX Repiping",
                 "neighborhood": "Alicia", "date": "2026-08-09",
                 "issue_description": "Old copper lines pinhole leaks; whole-house repipe to PEX"}]
        reviews = [{"approved_for_publish": 1, "text": "PEX repipe looks great, thank you!",
                    "extracted_city": "Mission Viejo", "extracted_service": "Pex Repiping"}]
        opp = {"city": "Mission Viejo", "service_type": "PEX Repiping",
               "keyword": "pex repiping mission viejo", "intent_type": "commercial"}
        r = BG.build_service_explainer(opp, jobs, reviews)
        self.assertEqual(r["tier"], "tier1")
        self.assertIn("From real local work", r["html"])
        self.assertIn("Old copper lines pinhole leaks", r["html"])
        self.assertIn("FAQPage", r["schema_types"])

    def test_tier2_is_honest_scoped(self):
        opp = {"city": "Aliso Viejo", "service_type": "Water Heater Services",
               "keyword": "water heater replacement aliso viejo", "intent_type": "commercial"}
        r = BG.build_service_explainer(opp, [], [])
        self.assertEqual(r["tier"], "tier2")
        self.assertNotIn("recently completed", r["html"].lower())
        # no fabricated job language
        for bad in ["we completed", "we finished", "our team did", "slab leak detected and repaired"]:
            self.assertNotIn(bad, r["html"].lower())

    def test_service_explainer_schema_and_links(self):
        opp = {"city": "Irvine", "service_type": "Slab Leak Detection",
               "keyword": "slab leak detection cost irvine", "intent_type": "informational"}
        jobs = [{"city": "Irvine", "service_type": "Slab Leak Detection",
                 "neighborhood": "Woodbridge", "date": "2026-07-20",
                 "issue_description": "Slab leak under family room; rerouted"}]
        reviews = []
        r = BG.build_service_explainer(opp, jobs, reviews)
        self.assertIn("cities/irvine.html", r["html"])
        self.assertIn("services/slab-leak-detection.html", r["html"])
        self.assertIn("schema_types", r)
        self.assertIn("Plumber", r["schema_types"])


if __name__ == "__main__":
    unittest.main()