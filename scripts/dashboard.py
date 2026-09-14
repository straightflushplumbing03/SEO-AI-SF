#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 — SFGE dashboard + alerting.

Pulls everything into one status view:
- jobs / reviews / content / opportunities / AI visibility / audit
- demand-signal expansion list (F4)
- approval-gate state (settings.auto_publish_*)
- pending approvals (content awaiting human merge)
- alerts high-priority gaps to Slack/email if configured

Usage:
  python3 scripts/dashboard.py                 # print dashboard
  python3 scripts/dashboard.py --alerts        # + fire alerts for new high-priority items
  python3 scripts/dashboard.py --gate          # show approval-gate status
  python3 scripts/dashboard.py --gate --auto@  # (never used by the engine itself)
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
from modules.objects import alerts  # noqa: E402
from modules.objects import demand_signal as DS  # noqa: E402
from modules.objects import settings as SETTINGS  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="SFGE dashboard")
    ap.add_argument("--alerts", action="store_true", help="fire alerts for new priorities")
    ap.add_argument("--gate", action="store_true", help="show approval-gate status")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))
    today = dt.date.today().isoformat()

    # ---- gather ----
    jobs_total = db.scalar("SELECT COUNT(*) FROM jobs") or 0
    jobs_recent = db.scalar(
        "SELECT COUNT(*) FROM jobs WHERE date >= ?",
        ((dt.date.today() - dt.timedelta(days=7)).isoformat(),),
    ) or 0
    rev_total = db.scalar("SELECT COUNT(*) FROM reviews") or 0
    rev_approved = db.scalar("SELECT COUNT(*) FROM reviews WHERE approved_for_publish=1") or 0
    content_total = db.scalar("SELECT COUNT(*) FROM content") or 0
    content_pending = db.scalar("SELECT COUNT(*) FROM content WHERE publish_status='pending_approval'") or 0
    content_live = db.scalar("SELECT COUNT(*) FROM content WHERE publish_status='live'") or 0
    opp_open = db.scalar("SELECT COUNT(*) FROM opportunities WHERE status='open'") or 0
    top_opp = db.rows("SELECT keyword, priority_score FROM opportunities "
                      "WHERE status='open' ORDER BY priority_score DESC LIMIT 5")
    ai_checks = db.scalar("SELECT COUNT(*) FROM ai_visibility_checks") or 0
    ai_cited = db.scalar("SELECT COUNT(*) FROM ai_visibility_checks WHERE cited=1") or 0
    audit_high = db.scalar("SELECT COUNT(*) FROM audit_findings WHERE severity='high' AND date=?", (today,)) or 0

    # demand signal
    expansion = DS.expansion_list(db)

    # approval gate
    gate_enabled = SETTINGS.get_setting(db, "auto_publish_enabled")
    required = SETTINGS.get_setting(db, "required_clean_approvals")
    clean_merges = db.scalar(
        "SELECT COUNT(*) FROM content WHERE publish_status='live' AND needs_field_data=0") or 0
    gate_open = SETTINGS.can_auto_publish(db)

    # ---- render ----
    lines = []
    lines.append(f"# SFGE Dashboard — {today}")
    lines.append(f"- Jobs total: {jobs_total} (last 7d: {jobs_recent})")
    lines.append(f"- Reviews: {rev_total} ({rev_approved} approved)")
    lines.append(f"- Content: {content_total} rows ({content_pending} pending, {content_live} live)")
    lines.append(f"- Open opportunities: {opp_open}")
    lines.append(f"- AI checks: {ai_checks} ({ai_cited} cited)")
    lines.append(f"- Audit high-sev today: {audit_high}")

    if top_opp:
        lines.append("\n## Top opportunities")
        for o in top_opp:
            lines.append(f"- ({o['priority_score']:.1f}) {o['keyword']}")
    lines.append("\n## Demand-signal expansion (F4)")
    lines.append("| city | score | risk | job | content |")
    lines.append("|---|---|---|---|---|")
    for r in expansion[:6]:
        lines.append(f"| {r['city']} | {r['score']} | {r['risk']} | "
                     f"{'Y' if r['has_job'] else 'n'} | {'Y' if r['has_content'] else 'n'} |")

    lines.append("\n## Approval gate")
    lines.append(f"- auto_publish_enabled: {gate_enabled}")
    lines.append(f"- required_clean_approvals: {required}")
    lines.append(f"- clean merges (live tier-1): {clean_merges}")
    lines.append(f"- gate currently: {'OPEN (auto-publish allowed)' if gate_open else 'LOCKED (human only)'}")

    if content_pending:
        lines.append(f"\n## Pending approvals ({content_pending})")
        for c in db.rows("SELECT site_path, title FROM content "
                         "WHERE publish_status='pending_approval' ORDER BY created_at"):
            lines.append(f"- `{c['site_path']}` — {c['title']}")

    body = "\n".join(lines)
    print(body)

    if args.alerts:
        if top_opp and top_opp[0]["priority_score"] >= 12.0:
            alerts.alert("High-priority opportunity unlocked",
                         f"Top opportunity: {top_opp[0]['keyword']} "
                         f"(priority {top_opp[0]['priority_score']:.1f})")
        if expansion and expansion[0]["score"] >= 80:
            alerts.alert("Demand-signal greenfield",
                         f"{expansion[0]['city']} is high-risk with no SFGE presence "
                         f"(score {expansion[0]['score']}).")
        if audit_high:
            alerts.alert(f"{audit_high} high-severity audit finding(s) today",
                         "Check audit_findings in dashboard.")

    if args.json:
        import json as _j
        print(_j.dumps({
            "jobs_total": jobs_total, "jobs_recent": jobs_recent,
            "reviews_total": rev_total, "reviews_approved": rev_approved,
            "content_total": content_total, "content_pending": content_pending,
            "content_live": content_live, "open_opportunities": opp_open,
            "ai_checks": ai_checks, "ai_cited": ai_cited,
            "audit_high_today": audit_high,
            "gate": {"enabled": gate_enabled, "open": gate_open, "clean_merges": clean_merges},
            "expansion_top": expansion[:5],
        }, indent=2))


if __name__ == "__main__":
    main()