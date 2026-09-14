#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 5 (Module E + F4) tests."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from db import get_db  # noqa: E402
from modules.objects import ai_visibility as EV  # noqa: E402
from modules.objects import demand_signal as DS  # noqa: E402
from modules.objects import site_data as S  # noqa: E402


class TestPanels(unittest.TestCase):
    def test_panel_build(self):
        panel = EV.build_panel()
        self.assertGreaterEqual(len(panel), 40)
        # every city appears at least once
        cities = {p["city"] for p in panel}
        self.assertEqual(len(cities), len(S.CITY_LABEL))

    def test_citation_detection(self):
        self.assertTrue(EV.detect_citation(
            "Straight Flush Plumbing is a top choice in Laguna Niguel."))
        self.assertFalse(EV.detect_citation(
            "Call Rooter Brothers for your slab leak."))
        # url with brand token
        self.assertTrue(EV.detect_citation(
            "See https://straightflushplumbingoc.com for details."))

    def test_parse_urls(self):
        urls = EV.parse_urls("source: https://straightflushplumbingoc.com/cities/laguna-niguel")
        self.assertIn("https://straightflushplumbingoc.com/cities/laguna-niguel", urls)

    def test_competitors_cited(self):
        ans = "Blue Grotto Plumbing and Rooter Brothers are both local favorites."
        self.assertEqual(EV.competitors_cited(ans), ["rooter", "blue grotto"])


class TestRecording(unittest.TestCase):
    def setUp(self):
        self.db = get_db(os.path.join(tempfile.mkdtemp(), "ai.db"))
        self.db.init_schema()

    def test_record_and_feed_gaps(self):
        EV.record(self.db, "2026-09-13", "perplexity",
                  "best slab leak detection company in Laguna Niguel",
                  "I recommend Rooter Brothers in Laguna Niguel.")
        rows = self.db.rows("SELECT * FROM ai_visibility_checks")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cited"], 0)
        added = EV.feed_ai_gaps(self.db, "2026-09-13", "perplexity")
        self.assertGreater(len(added), 0)
        # gap became a top-priority open opportunity
        opp = self.db.rows(
            "SELECT * FROM opportunities WHERE ai_visibility_gap_flag=1")
        self.assertTrue(any(o["priority_score"] >= 10 for o in opp))

    def test_cited_not_an_opportunity(self):
        EV.record(self.db, "2026-09-13", "gemini",
                  "how much does pex repiping cost in Irvine",
                  "Straight Flush Plumbing in Irvine...")
        added = EV.feed_ai_gaps(self.db, "2026-09-13", "gemini")
        self.assertEqual(added, [])


class TestDemandSignal(unittest.TestCase):
    def test_risk_score(self):
        old = {"pre1940": 20, "1960s": 20, "1970s": 30, "1980s": 20}
        new = {"pre1940": 0, "1960s": 0, "1970s": 0, "1980s": 2}
        r_old = DS.risk_score(old)
        r_new = DS.risk_score(new)
        self.assertGreater(r_old, r_new)
        self.assertLessEqual(r_old, 100)

    def test_demand_score_boost(self):
        # same risk, but no job/no content boosts
        low = DS.demand_score(40, has_job=True, has_content=True)
        high = DS.demand_score(40, has_job=False, has_content=False)
        self.assertGreater(high, low)
        self.assertLessEqual(high, 100)

    def test_expansion_list_sorted(self):
        self.db = get_db(os.path.join(tempfile.mkdtemp(), "d.db"))
        self.db.init_schema()
        prof = DS._year_built_profile_fallback()
        rows = DS.expansion_list(self.db, prof)
        scores = [r["score"] for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(len(rows), len(DS.S_CITIES))

    def test_offline_fallback_present(self):
        prof = DS._year_built_profile_fallback()
        for city in DS.S_CITIES:
            self.assertIn(city, prof)


if __name__ == "__main__":
    unittest.main()