#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconcile the engine ledger with the site repo's actual PR state.

Every generated page sits behind a PR (guardrail 1: human review, never auto-
merge). When Lance merges a PR, this script flips the matching content row from
'pending_approval' to 'live' so the dashboard and the Phase-6 approval gate
(counts publish_status='live' rows as clean approvals) reflect reality.

Mapping: a content row's pr_url identifies the GitHub PR; the branch is
sfge/case-study-<slug>. The script queries merged PRs in the site repo and marks
matching rows live. Rows whose PR is still open stay pending.

Usage:
  python3 scripts/sync_prs.py                    # sync live state from GitHub
  python3 scripts/sync_prs.py --site-repo OWNER/REPO
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from db import get_db  # noqa: E402

GITHUB = "https://api.github.com"


def gh_request(method, api_path, token=None, params=None):
    url = f"{GITHUB}/{api_path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")[:500]
        return e.code, {"error": raw}


def fetch_merged_prs(site_repo, token):
    """Return {branch: pr_number} for merged PRs with sfge/case-study-* heads.

    Uses pr['merged_at'] — present only when the PR was actually merged (the
    list endpoint leaves 'merged' as None for closed-but-unmerged PRs).
    """
    status, data = gh_request(
        "GET", f"repos/{site_repo}/pulls",
        token=token,
        params={"state": "closed", "per_page": 100,
                "sort": "updated", "direction": "desc"},
    )
    if status != 200:
        raise RuntimeError(f"GitHub API {status}: {data.get('error', data)}")
    merged = {}
    for pr in data or []:
        head = (pr.get("head") or {}).get("ref", "")
        if head.startswith("sfge/case-study-") and pr.get("merged_at"):
            merged[head] = pr["number"]
    return merged


def mark_live(db, site_repo, merged):
    """Flip content rows whose branch appears in `merged` to live.

    merged: {branch: pr_number}. Returns (rows_flipped, still_pending).
    """
    rows = db.conn.execute(
        "SELECT content_id, site_path, publish_status, pr_url FROM content ORDER BY content_id"
    ).fetchall()
    flips = 0
    for row in rows:
        cid, site_path, status, pr_url = row
        if status == "live":
            continue
        slug = os.path.splitext(os.path.basename(site_path))[0]
        branch = f"sfge/case-study-{slug}"
        if branch in merged:
            prno = merged[branch]
            expected = f"https://github.com/{site_repo}/pull/{prno}"
            if pr_url and pr_url != expected:
                print(f"[sfge] content {cid}: pr_url {pr_url} != {expected}; "
                      f"skipping (branch reuse?)")
                continue
            db.execute("UPDATE content SET publish_status='live', pr_url=? "
                       "WHERE content_id=? AND publish_status != 'live'",
                       (expected, cid))
            flips += 1
            print(f"[sfge] marked live: {site_path} (PR #{prno})")
    db.conn.commit()
    pend = db.conn.execute(
        "SELECT site_path, pr_url FROM content "
        "WHERE publish_status='pending_approval' ORDER BY content_id"
    ).fetchall()
    return flips, [p[0] for p in pend]


def main():
    ap = argparse.ArgumentParser(description="Sync engine ledger with merged site PRs")
    ap.add_argument("--site-repo",
                    default=os.environ.get("SFGE_SITE_REPO",
                                           "straightflushplumbing03/-Up2datewebsiteseo"))
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("[sfge] GITHUB_TOKEN not set; nothing synced")
        sys.exit(1)

    db = get_db(os.path.join(_REPO, "sfge.db"))
    merged = fetch_merged_prs(args.site_repo, token)
    if not merged:
        print("[sfge] no merged sfge/case-study-* PRs found")

    flips, pend = mark_live(db, args.site_repo, merged)
    print(f"[sfge] {flips} row(s) flipped to live")
    print(f"[sfge] still pending: {len(pend)}")
    for path in pend:
        print(f"  - {path}")


if __name__ == "__main__":
    main()