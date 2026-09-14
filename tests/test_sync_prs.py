#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scripts/sync_prs.py (merged-PR -> live marking)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from db import get_db  # noqa: E402
import sync_prs  # noqa: E402


def insert_content(db, slug, status="pending_approval", pr_url=None):
    db.execute(
        """INSERT INTO content (type, tier, city, service_type, site_path,
                                canonical_url, title, schema_types, publish_status,
                                pr_url)
           VALUES ('case_study','tier1','Laguna Niguel','Slab Leak Detection',
                   ?, 'https://sf.example/case-studies/' || ?, 'T', '[]', ?, ?)""",
        (f"case-studies/{slug}.html", slug, status, pr_url),
    )
    db.conn.commit()


class TestSyncPrs(unittest.TestCase):
    def setUp(self):
        self.db = get_db(os.path.join(tempfile.mkdtemp(), "s.db"))
        self.db.init_schema()

    def test_flips_matching_branch_to_live(self):
        insert_content(self.db, "laguna-niguel-leak-detection-5",
                       pr_url="https://github.com/o/r/pull/7")
        insert_content(self.db, "laguna-niguel-slab-leak-detection-6",
                       pr_url="https://github.com/o/r/pull/8")
        insert_content(self.db, "laguna-niguel-pex-repiping-4",
                       pr_url="https://github.com/o/r/pull/6")
        merged = {
            "sfge/case-study-laguna-niguel-leak-detection-5": 7,
            "sfge/case-study-laguna-niguel-slab-leak-detection-6": 8,
        }
        flipped, pending = sync_prs.mark_live(self.db, "o/r", merged)
        self.assertEqual(flipped, 2)
        self.assertEqual(sorted(pending), ["case-studies/laguna-niguel-pex-repiping-4.html"])
        live = self.db.scalar(
            "SELECT COUNT(*) FROM content WHERE publish_status='live'"
        )
        self.assertEqual(live, 2)

    def test_skips_when_pr_url_mismatch(self):
        insert_content(self.db, "laguna-niguel-leak-detection-5",
                       pr_url="https://github.com/o/r/pull/999")
        merged = {"sfge/case-study-laguna-niguel-leak-detection-5": 7}
        flipped, _ = sync_prs.mark_live(self.db, "o/r", merged)
        self.assertEqual(flipped, 0)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM content WHERE publish_status='live'"), 0)

    def test_no_merged_leaves_pending(self):
        insert_content(self.db, "laguna-niguel-pex-repiping-4")
        flipped, pending = sync_prs.mark_live(self.db, "o/r", {})
        self.assertEqual(flipped, 0)
        self.assertEqual(len(pending), 1)


if __name__ == "__main__":
    unittest.main()