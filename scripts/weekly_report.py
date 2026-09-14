#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 — Weekly report.

Summarizes the last 7 days (or N days) into reports/weekly-YYYY-MM-DD.md:
- jobs logged (by city/service)
- reviews ingested (by sentiment + source) and approved count
- content generated (pending_approval / pr / live)
- opportunities by priority (top 10)
- AI visibility check summary
- audit findings summary

No external services required.
"""
import argparse
import datetime as dt
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402

OUT_DIR = os.path.join(_REPO, "reports")


def iso(d):
    return d.isoformat()


def main():
    ap = argparse.ArgumentParser(description="Weekly report")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))
    since = iso(dt.date.today() - dt.timedelta(days=args.days))

    jobs = db.rows("SELECT * FROM jobs WHERE date >= ? ORDER BY date", (since,))
    reviews = db.rows("SELECT * FROM reviews WHERE created_at >= ? ORDER BY created_at", (since,))
    content = db.rows("SELECT * FROM content ORDER BY created_at DESC")
    opps = db.rows("SELECT * FROM opportunities WHERE status = 'open' ORDER BY priority_score DESC LIMIT 10")
    ai = db.rows("SELECT * FROM ai_visibility_checks WHERE date >= ? ORDER BY date", (since,))
    audits = db.rows("SELECT * FROM audit_findings WHERE date >= ? ORDER BY date", (since,))

    lines = []
    lines.append(f"# SFGE Weekly Report — {dt.date.today().isoformat()}")
    lines.append(f"Period: last {args.days} days (since {since})\n")

    lines.append("## Jobs logged")
    lines.append(f"**Total:** {len(jobs)}")
    if jobs:
        by_city = {}
        by_svc = {}
        for j in jobs:
            by_city[j["city"]] = by_city.get(j["city"], 0) + 1
            by_svc[j["service_type"]] = by_svc.get(j["service_type"], 0) + 1
        lines.append(f"- By city: {', '.join(f'{k} ({v})' for k, v in sorted(by_city.items()))}")
        lines.append(f"- By service: {', '.join(f'{k} ({v})' for k, v in sorted(by_svc.items()))}")
    else:
        lines.append("_No jobs logged this period._")
    lines.append("")

    lines.append("## Reviews")
    lines.append(f"**Total ingested:** {len(reviews)}")
    senti = {}
    approved = 0
    for r in reviews:
        senti[r.get("sentiment") or "neutral"] = senti.get(r.get("sentiment") or "neutral", 0) + 1
        if r.get("approved_for_publish"):
            approved += 1
    lines.append(f"- Sentiment: {', '.join(f'{k}: {v}' for k, v in senti.items()) or 'n/a'}")
    lines.append(f"- Approved for publish: {approved}")
    lines.append("")

    lines.append("## Content generated")
    lines.append(f"**Total content rows:** {len(content)}")
    for c in content:
        lines.append(f"- [{c['publish_status']}] `{c['site_path']}` — {c['title']}")
    lines.append("")

    lines.append("## Top opportunities")
    if opps:
        for o in opps:
            lines.append(
                f"- ({o['priority_score']:.1f}) {o['keyword']} — intent={o['intent_type']} "
                f"vol={o.get('search_volume') or '?'} diff={o.get('difficulty') or '?'}"
            )
    else:
        lines.append("_No open opportunities._")
    lines.append("")

    lines.append("## AI visibility checks")
    lines.append(f"**Total checks:** {len(ai)} | **Cited:** {sum(1 for c in ai if c['cited'])}")
    for c in ai:
        lines.append(f"- [{c['engine']}] cited={c['cited']} :: {c['prompt'][:60]}")
    lines.append("")

    lines.append("## Audit findings")
    lines.append(f"**Total findings:** {len(audits)} | **Auto-fixed:** {sum(1 for a in audits if a['auto_fixed'])}")
    for a in audits:
        lines.append(f"- [{a['severity']}/{a['category']}] {a['message']} — {a['url']}")
    lines.append("")

    body = "\n".join(lines)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"weekly-{dt.date.today().isoformat()}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(body)
    print(f"\n[sge] report written to {path}")


if __name__ == "__main__":
    main()