#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 (Modules C + D) tests: link graph + audit checks + autocorrects."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from modules.objects import audit as A  # noqa: E402
from modules.objects import link_audit as LA  # noqa: E402


def make_site():
    root = tempfile.mkdtemp(prefix="sfge-test-site-")
    os.makedirs(os.path.join(root, "cities"))
    os.makedirs(os.path.join(root, "services"))
    os.makedirs(os.path.join(root, "case-studies"))
    os.makedirs(os.path.join(root, "assets", "img"))
    # home
    with open(os.path.join(root, "index.html"), "w") as f:
        f.write('''<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://straightflushplumbingoc.com/"></head>
<body><img src="logo.jpg"></body></html>''')
    # city page (linked from index)
    with open(os.path.join(root, "cities", "laguna-niguel.html"), "w") as f:
        f.write('''<html><head>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Plumber"}</script>
</head><body><a href="../services/slab-leak-detection.html">svc</a></body></html>''')
    # service page
    with open(os.path.join(root, "services", "slab-leak-detection.html"), "w") as f:
        f.write('<html><head><title>s</title></head><body><a href="../index.html">home</a></body></html>')
    # orphan case study (no inbound)
    with open(os.path.join(root, "case-studies", "laguna-niguel-slab-1.html"), "w") as f:
        f.write('<html><head><title>cs</title></head><body><p>x</p></body></html>')
    # broken link
    with open(os.path.join(root, "academy.html"), "w") as f:
        f.write('<html><body><a href="missing.html">bad</a></body></html>')
    return root


class TestLinkAudit(unittest.TestCase):
    def test_crawl_and_broken(self):
        root = make_site()
        graph = LA.crawl(root)
        broken = LA.find_broken(graph, root)
        self.assertTrue(any(page == "academy.html" and href == "missing.html"
                            for page, href in broken))

    def test_orphan_detected(self):
        root = make_site()
        graph = LA.crawl(root)
        orphans = LA.find_orphans(graph)
        self.assertIn("case-studies/laguna-niguel-slab-1.html", orphans)
        # 404 is an error page, not an orphan
        with open(os.path.join(root, "404.html"), "w") as f:
            f.write("<html><body>404</body></html>")
        graph2 = LA.crawl(root)
        self.assertNotIn("404.html", LA.find_orphans(graph2))


class TestAuditChecks(unittest.TestCase):
    def test_canonical_missing_flagged(self):
        root = make_site()
        fds = A.check_canonicals(root)
        paths = [f["url"] for f in fds]
        self.assertIn("cities/laguna-niguel.html", paths)

    def test_sitemap_robots(self):
        root = make_site()
        fds = A.check_sitemap_robots(root)
        self.assertTrue(any(f["category"] == "sitemap" and f["severity"] == "high"
                            for f in fds))  # missing sitemap
        self.assertTrue(any(f["category"] == "robots.txt" for f in fds))

    def test_schema_valid(self):
        root = make_site()
        fds = A.check_schema(root)
        # city page has valid Plumber schema, service page has none (but services/
        # should have schema -> flagged), case study has none (flagged)
        self.assertTrue(any(f["category"] == "schema" for f in fds))

    def test_images_missing_alt(self):
        root = make_site()
        fds = A.check_images(root)
        self.assertTrue(any("logo.jpg" in f["message"] for f in fds))

    def test_mobile(self):
        root = make_site()
        fds = A.check_mobile(root)
        self.assertTrue(any(f["url"].endswith("cities/laguna-niguel.html") for f in fds))

    def test_links_audit(self):
        root = make_site()
        fds = A.check_links(root)
        self.assertTrue(any(f["category"] == "links" for f in fds))

    def test_cwv_heuristic(self):
        root = make_site()
        # create a huge page
        with open(os.path.join(root, "cities", "big.html"), "w") as f:
            f.write("<html>" + ("<p>" + "x" * 5000 + "</p>") * 100 + "</html>")
        fds = A.check_cwv(root)
        self.assertTrue(any(f["category"] == "cwv" for f in fds))

    def test_autofix_canonical(self):
        root = make_site()
        path = os.path.join(root, "cities", "laguna-niguel.html")
        self.assertTrue(A.autofix_canonical(path))
        with open(path) as f:
            html = f.read()
        self.assertIn('rel="canonical"', html)
        self.assertFalse(A.autofix_canonical(path))  # idempotent

    def test_autofix_alt(self):
        root = make_site()
        path = os.path.join(root, "index.html")
        n = A.autofix_alt(path)
        self.assertEqual(n, 1)
        with open(path) as f:
            html = f.read()
        self.assertIn('alt="Straight Flush Plumbing & Leak Detection"', html)


if __name__ == "__main__":
    unittest.main()