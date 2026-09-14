#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module A — Build the prioritized `opportunities` backlog.

Steps:
1. Generate the deterministic keyword cluster (Module A vocabulary).
2. Exclude combos that already have generated/live content
   (from the `content` table by city + service_type).
3. Boost combos that are Tier-2 'needs_field_data' (highest priority: next
   real job there auto-upgrades the page) and combos flagged by Module E
   (ai_visibility_gap_flag) — see scripts/ai_visibility.py --feed-gaps.
4. Score: opportunity = volume x (1 - difficulty) + boosters,
   normalized, written to `opportunities`.

Paid keyword API (DataForSEO / SerpApi) can override volumes/difficulties:
  python3 scripts/build_opportunities.py --api serpapi   # requires SFGE_SERPAPI_KEY
Guardrail 6 — never run --api without Lance's written sign-off on provider+cost.
"""
import argparse
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from modules.objects import keywords as K  # noqa: E402


def existing_combos(db):
    rows = db.rows("SELECT DISTINCT city, service_type, tier FROM content")
    return {(r["city"] or "").lower(), (r["service_type"] or "").lower()}  # drop-old


def _have_content(db, city, service):
    return db.scalar(
        "SELECT COUNT(*) FROM content WHERE lower(city)=lower(?) AND lower(service_type)=lower(?)",
        (city, service),
    ) or 0


def _tier2_needs_field(db, city, service):
    return db.scalar(
        """SELECT COUNT(*) FROM content
           WHERE lower(city)=lower(?) AND lower(service_type)=lower(?)
             AND needs_field_data=1""",
        (city, service),
    ) or 0


def _ai_gap(db, keyword, city):
    return db.scalar(
        """SELECT COUNT(*) FROM opportunities
           WHERE lower(keyword)=lower(?) AND city=lower(?) AND ai_visibility_gap_flag=1""",
        (keyword, city),
    ) or 0


def priority_score(kw, db, boost_tier2=6.0, boost_ai=4.0):
    vol = int(kw.get("search_volume") or 0)
    diff = float(kw.get("difficulty") or 0.5)
    score = vol * (1 - diff) / 100.0
    if _tier2_needs_field(db, kw["city"], kw["service_type"]):
        score += boost_tier2
    if _ai_gap(db, kw["keyword"], kw["city"]):
        score += boost_ai
    return round(score, 2)


def seed_opportunities(db):
    """Insert all not-yet-seeded opportunity rows. Returns count inserted."""
    inserted = 0
    for kw in K.generate_all():
        if _have_content(db, kw["city"], kw["service_type"]):
            continue
        existing = db.scalar(
            "SELECT COUNT(*) FROM opportunities WHERE keyword=? AND city=? AND service_type=?",
            (kw["keyword"], kw["city"], kw["service_type"]),
        )
        if existing:
            continue
        score = priority_score(kw, db)
        db.execute(
            """INSERT INTO opportunities
               (keyword, city, service_type, search_volume, difficulty,
                intent_type, priority_score)
               VALUES (?,?,?,?,?,?,?)""",
            (kw["keyword"], kw["city"], kw["service_type"],
             kw["search_volume"], kw["difficulty"], kw["intent_type"], score),
        )
        inserted += 1
    return inserted


def main():
    ap = argparse.ArgumentParser(description="Build opportunities backlog (Module A)")
    ap.add_argument("--api", choices=["", "serpapi", "dataforseo"], default="",
                    help="paid keyword API (guardrail 6: requires sign-off)")
    ap.add_argument("--limit", type=int, default=0, help="truncate per city (0=none)")
    args = ap.parse_args()

    if args.api:
        print("[sfge] WARNING: --api requires Lance's explicit sign-off on the paid provider "
              "and monthly cost (guardrail 6). Refusing to run without it.")
        sys.exit(1)

    db = get_db(os.path.join(_REPO, "sfge.db"))
    inserted = seed_opportunities(db)

    top = db.rows(
        "SELECT keyword, city, service_type, intent_type, priority_score "
        "FROM opportunities WHERE status='open' ORDER BY priority_score DESC LIMIT 15"
    )
    print(f"[sfge] inserted {inserted} opportunities; open total:")
    total = db.scalar("SELECT COUNT(*) FROM opportunities WHERE status='open'")
    print(f"  open backlog: {total}")
    print("  top 15 by priority:")
    for r in top:
        print(f"    {r['priority_score']:>5}  [{r['intent_type']:>12}] {r['keyword']}")


if __name__ == "__main__":
    main()