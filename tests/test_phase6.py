#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 6 (dashboard, alerts, approval-gate) tests."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from db import get_db  # noqa: E402
from modules.objects import alerts  # noqa: E402
from modules.objects import settings as SETTINGS  # noqa: E402


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.db = get_db(os.path.join(tempfile.mkdtemp(), "s.db"))
        self.db.init_schema()

    def test_defaults_safe(self):
        self.assertFalse(SETTINGS.get_setting(self.db, "auto_publish_enabled"))
        self.assertEqual(SETTINGS.get_setting(self.db, "required_clean_approvals"), 5)

    def test_can_auto_publish_locked_by_default(self):
        self.assertFalse(SETTINGS.can_auto_publish(self.db, "tier1"))
        self.assertFalse(SETTINGS.can_auto_publish(self.db, "tier2"))

    def test_auto_publish_unlocks_only_after_clean_merges(self):
        # enable gate but with no clean live merges -> still locked
        SETTINGS.set_setting(self.db, "auto_publish_enabled", True)
        self.assertFalse(SETTINGS.can_auto_publish(self.db, "tier1"))
        # insert 5 clean live tier-1 rows
        for i in range(5):
            self.db.execute(
                """INSERT INTO content (type, tier, city, service_type, site_path,
                                        canonical_url, title, schema_types, publish_status)
                   VALUES ('case_study','tier1','Irvine','Slab Leak Detection',
                           'case-studies/x.html','https://x','t','[]','live')""")
        self.db.conn.commit()
        self.assertTrue(SETTINGS.can_auto_publish(self.db, "tier1"))

    def test_tier2_never_auto_publishes(self):
        SETTINGS.set_setting(self.db, "auto_publish_enabled", True)
        SETTINGS.set_setting(self.db, "required_clean_approvals", 1)
        # 1 clean live tier-1 row unlocks the gate for tier-1 only
        self.db.execute(
            """INSERT INTO content (type, tier, city, service_type, site_path,
                                    canonical_url, title, schema_types, publish_status)
               VALUES ('case_study','tier1','Irvine','Slab Leak Detection',
                       'case-studies/x.html','https://x','t','[]','live')""")
        # and a tier-2 needs_field_data page that must never auto-publish
        self.db.execute(
            """INSERT INTO content (type, tier, city, service_type, site_path,
                                    canonical_url, title, schema_types, publish_status,
                                    needs_field_data)
               VALUES ('city_page','tier2','Irvine','Leak Detection',
                       'cities/irvine.html','https://x','t','[]','live',1)""")
        self.db.conn.commit()
        self.assertTrue(SETTINGS.can_auto_publish(self.db, "tier1"))
        self.assertFalse(SETTINGS.can_auto_publish(self.db, "tier2"))


class TestAlerts(unittest.TestCase):
    def test_alert_degrades_to_log(self):
        # no webhook/smtp configured -> writes reports/alerts.log
        import tempfile as _t
        os.chdir(_t.mkdtemp())  # isolated cwd for reports/
        os.environ.pop("SFGE_SLACK_WEBHOOK", None)
        os.environ.pop("SFGE_SMTP_HOST", None)
        delivered = alerts.alert("Test subject", "Test body", level="warn")
        self.assertFalse(delivered)
        self.assertTrue(os.path.exists("reports/alerts.log"))


if __name__ == "__main__":
    unittest.main()