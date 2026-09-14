#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module E — AI Search Visibility tracker CLI.

Usage:
  python3 scripts/ai_visibility.py --panel                  # print the prompt panel
  python3 scripts/ai_visibility.py --panel --count          # count prompts
  python3 scripts/ai_visibility.py --add-result --engine perplexity \\
          --prompt "best slab leak detection company in Laguna Niguel" \\
          --answer "<paste AI answer>"
  python3 scripts/ai_visibility.py --run-serpapi --engine perplexity   # needs SFGE_SERPAPI_KEY + sign-off
  python3 scripts/ai_visibility.py --feed-gaps --date YYYY-MM-DD      # uncited -> opportunities
  python3 scripts/ai_visibility.py --report [--since 30d]

Guardrail 6: --run-serpapi requires Lance's explicit written sign-off on
the provider and monthly cost before any run.
"""
import argparse
import datetime as _dt
import json
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from modules.objects import ai_visibility as EV  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Module E — AI visibility tracker")
    ap.add_argument("--panel", action="store_true", help="print prompt panel")
    ap.add_argument("--count", action="store_true", help="with --panel, print count")
    ap.add_argument("--add-result", action="store_true")
    ap.add_argument("--engine", choices=EV.ENGINES, default="perplexity")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--answer", default=None)
    ap.add_argument("--run-serpapi", action="store_true",
                    help="run the full panel against an engine via SerpApi (sign-off required)")
    ap.add_argument("--max", type=int, default=0,
                    help="with --run-serpapi, limit prompts processed (0=all)")
    ap.add_argument("--feed-gaps", action="store_true")
    ap.add_argument("--date", default=_dt.date.today().isoformat())
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--since", default="30d")
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))

    if args.panel:
        panel = EV.build_panel()
        for p in panel:
            print(f"  [{p['intent']:>12}] {p['prompt']}")
        if args.count:
            print(f"\n  total prompts: {len(panel)}")
        return

    if args.add_result:
        if not (args.prompt and args.answer):
            ap.error("--add-result requires --prompt and --answer")
        rid = EV.record(db, args.date, args.engine, args.prompt, args.answer)
        print(f"[sfge] recorded check #{rid}: cited={EV.detect_citation(args.answer)}")
        return

    if args.run_serpapi:
        print("[sfge] guardrail 6: running SerpApi requires Lance's explicit "
              "written sign-off on the provider + monthly cost.")
        print("       Set SFGE_SERPAPI_KEY once approved.")
        panel = EV.build_panel()
        if args.max:
            panel = panel[: args.max]
        for i, p in enumerate(panel, 1):
            try:
                ans = EV.serpapi_ask(p["prompt"], engine=args.engine)
            except RuntimeError as e:
                print(f"[sfge] {i}. SKIP ({e})"); break
            except Exception as e:
                print(f"[sfge] {i}. error {e}"); continue
            EV.record(db, args.date, args.engine, p["prompt"], ans)
            cited = EV.detect_citation(ans)
            print(f"[sfge] {i}/{len(panel)} cited={cited} {p['prompt']}")
        return

    if args.feed_gaps:
        added = EV.feed_ai_gaps(db, args.date, "any")
        print(f"[sfge] fed {len(added)} AI-visibility gaps into opportunities")
        for a in added:
            print(f"  + {a}")
        return

    if args.report:
        since = _since_arg(args.since)
        rows = db.rows(
            "SELECT date, engine, COUNT(*) n, SUM(cited) cited FROM ai_visibility_checks "
            "WHERE date >= ? GROUP BY date, engine ORDER BY date DESC",
            (since,),
        )
        print(f"AI visibility since {since}:")
        for r in rows:
            if r["n"]:
                print(f"  {r['date']} {r['engine']:<14} {r['cited']}/{r['n']} cited")
        return

    ap.error("need an action (--panel, --add-result, --run-serpapi, --feed-gaps, --report)")


def _since_arg(s):
    delta = _dt.timedelta(days=int(s.rstrip("dD")))
    return (_dt.date.today() - delta).isoformat()


if __name__ == "__main__":
    main()