#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module F4 — Demand-signal pre-positioning CLI.

Priority: which South OC neighborhoods are statistically about to need slab
leak / repipe work (older housing stock) and currently have thin or no
Straight Flush presence.

Usage:
  python3 scripts/demand_signal.py                     # offline defaults
  python3 scripts/demand_signal.py --fetch-census      # live ACS data (free, public)
  python3 scripts/demand_signal.py --jobs DB           # point at another sqlite db

Output is a ranked expansion list. The top of the list = neighborhoods where
Straight Flush should target content / GBP / ads first, because demand is
probabilistically rising there and Straight Flush isn't established yet.
"""
import argparse
import json
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from modules.objects import demand_signal as DS  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Module F4 — demand-signal expansion list")
    ap.add_argument("--fetch-census", action="store_true",
                    help="query the free public Census ACS API for year-built data "
                         "(falls back to offline defaults on failure)")
    ap.add_argument("--jobs", default=os.path.join(_REPO, "sfge.db"),
                    help="path to SFGE sqlite db")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    db = get_db(args.jobs)
    profiles = DS.fetch_census_profile() if args.fetch_census else DS._year_built_profile_fallback()
    if args.fetch_census and profiles == DS._year_built_profile_fallback():
        print("[sfge] census fetch failed/falls back to offline profile defaults",
              file=sys.stderr)

    rows = DS.expansion_list(db, profiles)
    if args.json:
        print(json.dumps(rows, indent=2))
        return

    print("Demand-signal expansion list (score 0-100):")
    print(f"{'score':>5}  {'city':<22} {'risk':>4}  job content")
    print("-" * 56)
    for r in rows:
        print(f"{r['score']:>5}  {r['city']:<22} {r['risk']:>4}  "
              f"{'yes' if r['has_job'] else 'no ':>3}  "
              f"{'yes' if r['has_content'] else 'no ':>3}")
    print()
    print("Top signal (high risk + no SFGE presence yet): "
          f"{rows[0]['city'] if rows else '-'}")


if __name__ == "__main__":
    main()