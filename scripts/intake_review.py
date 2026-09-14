#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F3 — Review intake (CLI + CSV).

Ingests a customer review, runs the lightweight NLP mining pass, and persists it.
Reviews with rating >= 4 AND a specific signal (service, city, or pain point)
are flagged approved_for_publish=1 for use in content/schema.

Usage:
  python3 scripts/intake_review.py --text "Lance found a slab leak quickly..." \
      --rating 5 --source google --job-id 1
  python3 scripts/intake_review.py --csv reviews.csv
"""
import argparse
import csv
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from modules.objects import review_miner as RM  # noqa: E402

APPROVE_MIN_RATING = 4


def process_one(db, text, rating, source, job_id=None, approve=True):
    done = RM.mine_review(text, rating=rating, source=source)
    review_id = db.insert_review(
        job_id=job_id,
        source=source,
        rating=rating,
        text=text,
        sentiment=done["sentiment"],
        extracted_keywords=done["keywords"],
        extracted_city=done["city"],
        extracted_service=done["service_type"],
        approved_for_publish=(1 if approve and done["approved_for_publish"] else 0),
    )
    return review_id, done


def main():
    ap = argparse.ArgumentParser(description="Ingest + mine a customer review")
    ap.add_argument("--text", default="")
    ap.add_argument("--rating", type=int, default=None)
    ap.add_argument("--source", default="google", choices=["google", "yelp", "sms", "email", "manual"])
    ap.add_argument("--job-id", type=int, default=None)
    ap.add_argument("--csv", default="")
    ap.add_argument("--no-approve", action="store_true",
                    help="never auto-approve for publish (manual review gate)")
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))

    if args.csv:
        with open(args.csv, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        total = 0
        for r in rows:
            try:
                rating = int(r.get("rating") or 0)
            except ValueError:
                rating = 0
            text = (r.get("text") or r.get("review") or "").strip()
            if not text:
                continue
            rid, _ = process_one(
                db, text, rating or None, r.get("source") or "google",
                job_id=int(r["job_id"]) if r.get("job_id") else None,
                approve=not args.no_approve,
            )
            total += 1
            print(f"  review {rid}: {text[:60]}...")
        print(f"[sfge] imported {total} reviews from {args.csv}")
        return

    if not args.text.strip():
        ap.error("need --text or --csv")

    rid, done = process_one(
        db, args.text.strip(), args.rating, args.source, args.job_id,
        approve=not args.no_approve,
    )
    print(f"[sfge] review {rid}: sentiment={done['sentiment']} "
          f"service={done['service_type']} city={done['city']} "
          f"pain={len(done['pain_points'])} approved={done['approved_for_publish']}")


if __name__ == "__main__":
    main()