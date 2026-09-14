#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module D — Weekly technical / GEO audit.

Usage:
  python3 scripts/audit_engine.py                 # audit local site clone at ./site-checkout
  python3 scripts/audit_engine.py --site-repo OWNER/REPO   # clone fresh, audit, auto-fix PR
  python3 scripts/audit_engine.py --local /path/to/site   # audit an existing checkout

Checks: canonicals, sitemap/robots, schema, images (alt), mobile viewport,
internal links (broken + orphans), lightweight CWV proxies.

Safe autocorrects (canonical, alt text) are applied and opened as a PR for
human review — never auto-merged (guardrail 1). Structural issues (schema
type changes, sitemap rework) are reported only.

Findings are recorded into `audit_findings`.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from modules.objects import audit as A  # noqa: E402

GITHUB = "https://api.github.com"
DEFAULT_SITE_REPO = os.environ.get("SFGE_SITE_REPO", "straightflushplumbing03/-Up2datewebsiteseo")


def run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip()


def clone_root(site_repo):
    root = tempfile.mkdtemp(prefix="sfge-audit-")
    url = os.environ.get("SFGE_SITE_CLONE_URL", f"https://github.com/{site_repo}.git")
    run(["git", "clone", "--depth", "1", "--branch", "main", url, root])
    return root


def record(db, findings):
    n = 0
    for f in findings:
        db.execute(
            """INSERT INTO audit_findings (date, category, severity, message, url, auto_fixed)
               VALUES (?,?,?,?,?,?)""",
            (f["date"], f["category"], f["severity"], f["message"], f.get("url"), f["auto_fixed"]),
        )
        n += 1
    db.conn.commit()
    return n


def open_fix_pr(root, site_repo, summary, branch):
    token = os.environ.get("GITHUB_TOKEN", "")
    run(["git", "checkout", "-b", branch], root)
    run(["git", "add", "-A"], root)
    changed = run(["git", "diff", "--cached", "--name-only"], root).splitlines()
    if not changed:
        print("[sfge] no changes to fix; nothing to PR")
        return None
    run(["git", "commit", "-m",
         f"SFGE audit autocorrect: {summary}\n\nAutomated safe fixes (missing canonical/alt). Human review required."],
        root)
    push_url = os.environ.get(
        "SFGE_PUSH_URL",
        f"https://x-access-token:{token}@github.com/{site_repo}.git",
    )
    run(["git", "push", "-u", push_url, branch], root)
    body = f"""Automated audit autocorrects from **SFGE** (Module D).

**Fixes applied:**
{summary}

All changes are safe, additive fixes (canonical insertion, img alt text).
Nothing structural is touched without a human. Requires review before merge.

_This PR was created by an AI agent (OpenHands) on behalf of the Straight Flush team._
"""
    req = urllib.request.Request(
        f"{GITHUB}/repos/{site_repo}/pulls", method="POST",
        data=json.dumps({
            "title": f"Audit fixes: {summary}",
            "head": branch,
            "base": "main",
            "body": body,
        }).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            pr = json.loads(r.read().decode())
            return pr.get("html_url")
    except urllib.error.HTTPError as e:
        print(f"[sfge] PR open failed: {e.code} {e.read().decode()[:300]}")
        return None


def main():
    ap = argparse.ArgumentParser(description="Weekly technical/GEO audit (Module D)")
    ap.add_argument("--site-repo", default=DEFAULT_SITE_REPO)
    ap.add_argument("--local", default=None,
                    help="path to existing site checkout (skip clone)")
    ap.add_argument("--no-pr", action="store_true",
                    help="record findings only; don't open a fix PR")
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))

    do_clone = not args.local
    root = args.local or clone_root(args.site_repo)
    try:
        findings = A.check_all(root)
        record(db, findings)

        # ---- safe autocorrects ----
        fixed = []
        for path in A._html_files(root):
            if A.autofix_canonical(path):
                rel = os.path.relpath(path, root)
                fixed.append(f"canonical: {rel}")
                db.execute("""INSERT INTO audit_findings
                              (date, category, severity, message, url, auto_fixed)
                              VALUES (?,?,?,?,?,1)""",
                           (A.TODAY, "canonical", "medium",
                            "missing canonical (auto-fixed)", rel))
            n_alt = A.autofix_alt(path)
            if n_alt:
                rel = os.path.relpath(path, root)
                fixed.append(f"alt text x{n_alt}: {rel}")
                db.execute("""INSERT INTO audit_findings
                              (date, category, severity, message, url, auto_fixed)
                              VALUES (?,?,?,?,?,1)""",
                           (A.TODAY, "images", "medium",
                            f"missing img alt text x{n_alt} (auto-fixed)", rel))
        db.conn.commit()

        summary = "; ".join(fixed) if fixed else "none needed"

        print(f"[sfge] audit complete: {len(findings)} findings "
              f"({sum(1 for f in findings if f['severity']=='high')} high, "
              f"{sum(1 for f in findings if f['severity']=='medium')} medium, "
              f"{sum(1 for f in findings if f['severity']=='low')} low); "
              f"auto-fixed: {summary}")

        if fixed and not args.no_pr:
            pr_url = open_fix_pr(root, args.site_repo, summary,
                                 branch=f"sfge/audit-fixes-{A.TODAY}")
            if pr_url:
                print(f"[sfge] PR: {pr_url}")
                db.execute(
                    "UPDATE audit_findings SET pr_url=? WHERE date=? AND auto_fixed=1",
                    (pr_url, A.TODAY))
                db.conn.commit()
    finally:
        if do_clone:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()