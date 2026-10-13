#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entity-graph tests: the site must present ONE business entity with a stable
@id, referenced by every other node — never a bare, @id-less Plumber per page.

See docs/ENTITY-MODEL.md.
"""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.objects import site_data as S  # noqa: E402
from modules.objects import schema_jsonld as J  # noqa: E402


class TestEntityIds(unittest.TestCase):
    def test_business_id_is_stable_https_url(self):
        self.assertEqual(S.BUSINESS_ID, "https://straightflushplumbingoc.com/#business")
        self.assertTrue(S.BUSINESS_ID.startswith(S.DOMAIN))

    def test_website_id_is_stable_https_url(self):
        self.assertEqual(S.WEBSITE_ID, "https://straightflushplumbingoc.com/#website")

    def test_ids_are_distinct(self):
        self.assertNotEqual(S.BUSINESS_ID, S.WEBSITE_ID)

    def test_retired_ids_not_reintroduced(self):
        """#organization / #plumber were retired in favour of single #business."""
        self.assertNotIn("#organization", S.BUSINESS_ID)
        self.assertNotIn("#plumber", S.BUSINESS_ID)


class TestBusinessNode(unittest.TestCase):
    def test_business_declares_id_and_type(self):
        b = J.business()
        self.assertEqual(b["@id"], S.BUSINESS_ID)
        self.assertEqual(b["@type"], "Plumber")

    def test_business_ref_is_pure_reference(self):
        self.assertEqual(J.business_ref(), {"@id": S.BUSINESS_ID})
        # A reference must not restate the name — it points at the node.
        self.assertNotIn("name", J.business_ref())

    def test_city_page_keeps_global_id(self):
        """No per-city business entities: one real location only."""
        node = J.local_business_page("San Clemente")
        self.assertEqual(node["@id"], S.BUSINESS_ID)
        self.assertEqual(node["areaServed"]["name"], "San Clemente, CA")

    def test_service_provider_is_a_reference(self):
        svc = J.service_with_catalog("San Clemente")
        self.assertEqual(svc["provider"], {"@id": S.BUSINESS_ID})

    def test_article_author_and_publisher_are_references(self):
        a = J.article("Test", "2026-01-01", f"{S.DOMAIN}/test")
        self.assertEqual(a["author"], {"@id": S.BUSINESS_ID})
        self.assertEqual(a["publisher"], {"@id": S.BUSINESS_ID})

    def test_website_publisher_is_a_reference(self):
        w = J.website()
        self.assertEqual(w["publisher"], {"@id": S.BUSINESS_ID})

    def test_no_inline_plumber_in_non_business_nodes(self):
        for node in (J.service_with_catalog("Dana Point"),
                     J.service("Leak Detection"),
                     J.article("T", "2026-01-01", f"{S.DOMAIN}/t"),
                     J.website(),
                     J.breadcrumbs([(1, "Home", f"{S.DOMAIN}/")])):
            blob = json.dumps(node)
            self.assertNotIn('"@type": "Plumber"', blob,
                             f"inline Plumber object leaked into {node['@type']}")

    def test_deprecated_aliases_kept_for_compatibility(self):
        """organization()/local_business()/plumber_min() still resolve to #business."""
        for fn in (J.organization, J.local_business, J.plumber_min):
            self.assertEqual(fn()["@id"], S.BUSINESS_ID)


class TestLiveSiteSchema(unittest.TestCase):
    """Validate the actual published HTML when a site checkout is available."""

    def setUp(self):
        self.site_dir = os.environ.get("SFGE_SITE_DIR", "")
        if not self.site_dir or not os.path.isdir(self.site_dir):
            self.skipTest("SFGE_SITE_DIR not set (site checkout not available)")

    def _pages(self):
        pages = ["index.html", "about.html", "service-areas.html"]
        for sub in ("cities", "services"):
            d = os.path.join(self.site_dir, sub)
            if os.path.isdir(d):
                pages += [os.path.join(sub, f) for f in sorted(os.listdir(d))
                          if f.endswith(".html")]
        # Include every subdirectory page (academy, guides, case-studies, ...)
        for root, dirs, files in os.walk(self.site_dir):
            dirs[:] = [d for d in dirs if d not in (".git", ".git-2", "assets", "scripts")]
            for f in files:
                if f.endswith(".html"):
                    pages.append(os.path.relpath(os.path.join(root, f), self.site_dir))
        return sorted({p for p in pages
                       if os.path.exists(os.path.join(self.site_dir, p))})

    def test_no_bare_plumber_nodes_on_site(self):
        """Every Plumber node must carry an @id (the entity must not fork)."""
        offenders = []
        for page in self._pages():
            with open(os.path.join(self.site_dir, page), encoding="utf-8") as fh:
                html = fh.read()
            for block in re.findall(
                    r'application/ld\+json[^>]*>(.*?)</script>', html, re.S):
                try:
                    d = json.loads(block)
                except Exception:
                    continue
                stack = [d]
                while stack:
                    node = stack.pop()
                    if isinstance(node, dict):
                        if node.get("@type") == "Plumber" and "@id" not in node:
                            offenders.append(page)
                        stack.extend(node.values())
                    elif isinstance(node, list):
                        stack.extend(node)
        self.assertEqual(offenders, [], f"bare Plumber nodes on: {sorted(set(offenders))}")


if __name__ == "__main__":
    unittest.main()
