#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 — Technician job-close intake (MVP: CLI).

Same privacy rules as the web form will enforce: no street address, no names,
no exact price. Technicians record city/neighborhood, service, a brief issue
description, duration, a cost-range bucket, and an optional plain-language
customer quote (shared with consent).

Usage:
  python3 scripts/intake_job.py --city "Laguna Niguel" --service "Slab Leak Detection" \
    --neighborhood "Bear Brand" \
    --issue "Slab leak under kitchen; copper pinhole; rerouted through attic" \
    --duration-hours 6 --cost-bucket "15000-25000" \
    --quote "Best money we've spent on this house."

Also accepts --csv to log a batch (data/backfill/*.csv) — see docs/BACKFILL.md.
"""
import argparse
import csv
import datetime
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from db import get_db  # noqa: E402
from modules.objects import site_data as S  # noqa: E402

VALID_SERVICES = set(S.SERVICE_TYPE_BY_SLUG.values())
VALID_BUCKETS = [f"{lo}-{hi}" if hi else f"{lo}+" for _, lo, hi in S.COST_BUCKETS]


def validate(args):
    if (args.city or "").strip() and not S.is_valid_city(args.city.strip().lower().replace(" ", "-")):
        # allow free-form city names (they might be neighborhoods of a covered city)
        pass
    if args.service and args.service.title() not in VALID_SERVICES:
        # normalize display labels generously
        ok_any = any(v.lower() == args.service.lower() for v in VALID_SERVICES)
        if not ok_any:
            raise SystemExit(
                f"[sfge] unknown service '{args.service}'. Choose one of: {', '.join(sorted(VALID_SERVICES))}"
            )
        args.service = next(v for v in VALID_SERVICES if v.lower() == args.service.lower())
    if args.cost_bucket and args.cost_bucket not in VALID_BUCKETS:
        raise SystemExit(f"[sfge] unknown cost bucket '{args.cost_bucket}'. Valid: {', '.join(VALID_BUCKETS)}")
    return args


def log_one(db, r):
    raw_date = (r.get("date") or "").strip()
    if not raw_date:
        raw_date = datetime.date.today().isoformat()
    job_id = db.insert_job(
        date=raw_date,
        city=(r.get("city") or "").strip(),
        neighborhood=(r.get("neighborhood") or "").strip() or None,
        service_type=(r.get("service") or r.get("service_type") or "").strip(),
        issue_description=(r.get("issue") or r.get("issue_description") or "").strip(),
        photos=[p.strip() for p in (r.get("photos") or "").split(";") if p.strip()] or None,
        duration_hours=float(r["duration_hours"]) if r.get("duration_hours") else None,
        cost_range_bucket=(r.get("cost_bucket") or "").strip() or None,
        customer_quote=(r.get("quote") or r.get("customer_quote") or "").strip() or None,
        status="logged",
    )
    return job_id


def main():
    ap = argparse.ArgumentParser(description="Log a completed job (F1 intake)")
    ap.add_argument("--city", default="")
    ap.add_argument("--neighborhood", default="")
    ap.add_argument("--service", default="")
    ap.add_argument("--issue", default="")
    ap.add_argument("--duration-hours", type=float, default=None)
    ap.add_argument("--cost-bucket", default="")
    ap.add_argument("--quote", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--csv", default="", help="batch-import jobs from a CSV file")
    args = ap.parse_args()

    db = get_db(os.path.join(os.path.dirname(__file__), "..", "sfge.db"))

    if args.csv:
        path = args.csv
        if not os.path.exists(path):
            print(f"[sfge] csv not found: {path}")
            sys.exit(1)
        count = 0
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                log_one(db, row)
                count += 1
        print(f"[sfge] imported {count} jobs from {path}")
        db.close()
        return

    if not args.city or not args.service or not args.issue:
        print("[sfge] --city, --service, and --issue are required (or use --csv)")
        ap.print_help()
        sys.exit(1)

    args = validate(args)
    job_id = log_one(db, {
        "date": args.date or "",
        "city": args.city,
        "neighborhood": args.neighborhood,
        "service": args.service,
        "issue": args.issue,
        "duration_hours": args.duration_hours,
        "cost_bucket": args.cost_bucket,
        "quote": args.quote,
    })
    print(f"[sfge] logged job {job_id}: {args.city} / {args.service}")
    print(f"[sfge] next: python3 scripts/gen_case_study.py --job-id {job_id}")
    db.close()


if __name__ == "__main__":
    main()