#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2 (F3) tests: review mining + folding."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from modules.objects import review_miner as RM  # noqa: E402
from modules.objects import review_fold as RF  # noqa: E402
from db import get_db  # noqa: E402


class TestMining(unittest.TestCase):
    def test_detects_service_city_sentiment(self):
        res = RM.mine_review(
            "Lance found our slab leak fast. Water bill had spiked $300. "
            "Excellent work in Laguna Niguel!",
            rating=5,
        )
        self.assertEqual(res["sentiment"], "positive")
        self.assertEqual(res["service_type"], "Slab Leak Detection")
        self.assertEqual(res["city"], "Laguna Niguel")
        self.assertIn("water bill", res["pain_points"])
        self.assertTrue(res["approved_for_publish"])

    def test_negative_low_rating_not_approved(self):
        res = RM.mine_review("Terrible experience, avoid this company.", rating=1)
        self.assertEqual(res["sentiment"], "negative")
        self.assertEqual(res["approved_for_publish"], 0)

    def test_vague_still_approved_if_specific(self):
        # positive but no service/city/pain => not approved (not specific)
        res = RM.mine_review("Great job! Highly recommend.", rating=5)
        self.assertEqual(res["approved_for_publish"], 0)

    def test_extract_keywords(self):
        res = RM.mine_review(
            "Pinhole leaks in our copper pipes kept springing. They repiped the whole house.",
            rating=5,
        )
        self.assertEqual(res["service_type"], "PEX Repiping")
        self.assertTrue(res["keywords"])


class TestReviewFold(unittest.TestCase):
    def test_quote_blocks_only_approved(self):
        reviews = [
            {"approved_for_publish": 1, "text": "Found our slab leak great!", "source": "google",
             "extracted_city": "Laguna Niguel", "extracted_service": "Slab Leak Detection"},
            {"approved_for_publish": 0, "text": "meh", "source": "yelp"},
        ]
        quotes = RF.quote_blocks(reviews)
        self.assertEqual(len(quotes), 1)
        self.assertIn("Laguna Niguel", quotes[0])

    def test_customer_language(self):
        reviews = [
            {"approved_for_publish": 1, "extracted_keywords": ["water bill spiked", "slab leak"],
             "extracted_service": "Slab Leak Detection", "extracted_city": "Irvine"},
        ]
        lang = RF.customer_language(reviews)
        self.assertIn("water bill spiked", lang["phrases"])
        self.assertEqual(lang["cities"], ["Irvine"])


class TestReviewIntake(unittest.TestCase):
    def test_intake_persists_mined_fields(self):
        from intake_review import process_one
        db = get_db(os.path.join(tempfile.mkdtemp(), "t.db"))
        db.init_schema()
        rid, done = process_one(
            db, "Quick honest work on our water heater in Mission Viejo. Thanks!",
            rating=5, source="google", job_id=None,
        )
        row = db.get_reviews_for_job(0)  # not used
        r = db.rows("SELECT * FROM reviews WHERE review_id = ?", (rid,))[0]
        self.assertEqual(r["sentiment"], "positive")
        self.assertEqual(r["extracted_service"], "Water Heater Services")
        self.assertEqual(r["extracted_city"], "Mission Viejo")
        self.assertEqual(r["approved_for_publish"], 1)
        db.close()


if __name__ == "__main__":
    unittest.main()