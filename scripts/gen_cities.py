#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate or refresh city pages into the site checkout.

Usage:
  python3 scripts/gen_cities.py --site-dir PATH --dry-run
  python3 scripts/gen_cities.py --site-dir PATH --write

Writes only pages built from verified city_data. Never invents facts.
"""
import argparse
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.objects import city_page as CP  # noqa: E402
from modules.objects import city_data as C   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", help="comma-separated city slugs")
    args = ap.parse_args()

    slugs = sorted(C.CITY_FACTS)
    if args.only:
        slugs = [s for s in args.only.split(",") if s]

    for slug in slugs:
        page = CP.build_city_page(slug)
        target = os.path.join(args.site_dir, page["path"])
        exists = os.path.exists(target)
        old_len = os.path.getsize(target) if exists else 0

        if args.write:
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(page["html"])
            print(f"  wrote {page['path']}  ({old_len} -> {len(page['html'])} bytes)")
        else:
            print(f"  [dry-run] {page['path']}: {old_len} -> "
                  f"{len(page['html'])} bytes, title={page['title']!r}")

    if not (args.write or args.dry_run):
        print("specify --dry-run or --write")


if __name__ == "__main__":
    main()