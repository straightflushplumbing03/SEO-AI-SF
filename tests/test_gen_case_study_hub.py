#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression tests for gen_case_study hub append logic.

The live case-studies hub card grid contains nested <div> elements (each card
is an <a> containing <div class="section-head"> and an inner <div class="eyebrow">),
and the grid element carries a style attribute. A naive regex anchored on a
closing </div> could either land on an inner close tag or miss the grid opener
entirely (when the class has trailing attributes). These tests lock in the
depth-counting implementation.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# scripts/gen_case_study.py imports modules.* at call time; importing it here
# triggers the argparse section only inside main(), so a plain import is safe.
import gen_case_study as G  # noqa: E402


def make_result(slug="laguna-niguel-slab-leak-detection-6"):
    return {
        "title": f"Slab Leak Detection in Laguna Niguel | Straight Flush Plumbing",
        "h1": "Slab Leak Detection \u2014 Laguna Niguel",
        "slug": slug,
        "description": "Real Slab Leak Detection work by Straight Flush Plumbing in Laguna Niguel",
    }


class TestUpsertHub(unittest.TestCase):
    def test_append_preserves_existing_card(self):
        existing = """<!DOCTYPE html>
<html><head><title>Case Studies</title></head><body>
<div class="wrap">
  <div class="card-grid reveal" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr));">
      <a class="service-card" href="./laguna-niguel-leak-detection-5.html"><div class="section-head" style="margin-bottom:12px;"><div class="eyebrow">Case study</div><h3>Leak Detection \u2014 Laguna Niguel</h3></div><p>old card</p></a>

    </div>
  </div>
</section>
</body></html>"""
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(existing)
        try:
            G._upsert_hub(path, make_result(), None)
            with open(path, encoding="utf-8") as f:
                out = f.read()
            # both cards present; old card text intact
            self.assertIn("laguna-niguel-leak-detection-5", out)
            self.assertIn("laguna-niguel-slab-leak-detection-6", out)
            self.assertIn("old card", out)
            # nested structure of the grid is preserved (old card's eyebrow intact)
            self.assertEqual(out.count('class="eyebrow"'), 2)
            self.assertEqual(out.count("service-card"), 2)
        finally:
            os.unlink(path)

    def test_already_listed_is_idempotent(self):
        existing = """<!DOCTYPE html>
<body>
<div class="card-grid reveal">
      <a class="service-card" href="./lab.html"><div class="section-head"><div class="eyebrow">Case study</div><h3>L</h3></div><p>x</p></a>
</div>
</body>"""
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(existing)
        try:
            G._upsert_hub(path, make_result("lab"), None)
            with open(path, encoding="utf-8") as f:
                out = f.read()
            self.assertEqual(out.count("service-card"), 1)
        finally:
            os.unlink(path)

    def test_missing_grid_raises(self):
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("<html><body><div class='wrap'></div></body></html>")
        try:
            with self.assertRaises(RuntimeError):
                G._upsert_hub(path, make_result(), None)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()