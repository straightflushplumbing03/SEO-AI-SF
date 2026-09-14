#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F2 — Generate a case-study page from a real job and open a PR against the
website repo.

Usage:
  python3 scripts/gen_case_study.py --job-id 1
  python3 scripts/gen_case_study.py --job-id 5 --site-repo straightflushplumbing03/-Up2datewebsiteseo

Workflow (guardrail 1: NEVER bypass human review):
  1. reads the job (and approved reviews) from SFGE DB;
  2. writes the page to a fresh clone/worktree of the site repo
     at case-studies/<slug>.html;
  3. patches sitemap.xml (page added, priority 0.7);
  4. commits to a new branch, pushes;
  5. opens a pull request with a human-review description;
  6. records content row (publish_status=pending_approval, pr_url).

Flags:
  --job-id N          job to turn into a page
  --site-repo OWNER/REPO   target repo (default: config / env SFGE_SITE_REPO)
  --no-open-pr        generate page + commit locally only (no push/PR)
  --upgrade-tier2 CITY SERVICE   build a Tier-2 scoped page (no real job yet)
"""
import argparse
import json
import os
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
from modules.objects import site_data as S  # noqa: E402
from modules.objects import page as P  # noqa: E402
from modules.objects import case_study as CS  # noqa: E402
from modules.objects import sitemap as SITEMAP  # noqa: E402

GITHUB = "https://api.github.com"
DEFAULT_SITE_REPO = os.environ.get("SFGE_SITE_REPO", "straightflushplumbing03/-Up2datewebsiteseo")


def gh_url(api_path):
    return f"{GITHUB}/{api_path.lstrip('/')}"


def gh_request(method, api_path, body=None, token=None):
    req = urllib.request.Request(gh_url(api_path), method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    data = json.dumps(body).encode() if body is not None else None
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")[:500]
        return e.code, {"error": raw}


def run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip()


def checkout_site(site_repo, branch):
    worktree = tempfile.mkdtemp(prefix="sfge-site-")
    clone_url = os.environ.get(
        "SFGE_SITE_CLONE_URL", f"https://github.com/{site_repo}.git"
    )
    run(["git", "clone", "--depth", "1", "--branch", branch, clone_url, worktree])
    # ensure the publisher identity is sane for this local worktree only
    run(["git", "config", "user.email", "sfge-engine@users.noreply.github.com"], worktree)
    run(["git", "config", "user.name", "SFGE Engine"], worktree)
    return worktree


def main():
    ap = argparse.ArgumentParser(description="Generate a case-study page + PR")
    ap.add_argument("--job-id", type=int, default=None)
    ap.add_argument("--site-repo", default=DEFAULT_SITE_REPO)
    ap.add_argument("--no-open-pr", action="store_true")
    ap.add_argument("--upgrade-tier2", nargs=2, metavar=("CITY", "SERVICE"),
                    help="build a Tier-2 scoped page for CITY/SERVICE (no real job yet)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    db_path = os.path.join(os.path.dirname(__file__), "..", "sfge.db")

    db = get_db(db_path)
    db_path = db.path  # resolved absolute
    job = reviews = None

    if args.upgrade_tier2:
        city, service = args.upgrade_tier2
        job = {"city": city, "service_type": service, "job_id": "t2"}
        reviews = []
        tier = "tier2"
        print(f"[sfge] Tier-2 scoped page for {city} / {service}")
    elif args.job_id:
        job = db.get_job(args.job_id)
        if not job:
            print(f"[sfge] no job with id {args.job_id}")
            sys.exit(1)
        reviews = db.get_reviews_for_job(args.job_id)
        tier = "tier1"
        print(f"[sfge] Job {job['job_id']}: {job['city']} / {job['service_type']}")
    else:
        ap.error("need --job-id or --upgrade-tier2")

    result = CS.build_case_study_page(job, reviews=reviews, tier=tier)
    slug = result["slug"]
    page_file = f"case-studies/{slug}.html"
    title = result["title"]

    # ---- record content row BEFORE opening PR so we can attach pr_url ----
    content_id = db.execute(
        """INSERT INTO content (type, tier, city, service_type, source_job_ids,
                                site_path, canonical_url, title, schema_types,
                                publish_status, needs_field_data)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        ("case_study", tier, job.get("city"), job.get("service_type"),
         json.dumps([job.get("job_id")]),
         page_file, f"{S.DOMAIN}/{result['canonical_path']}", title,
         json.dumps(result["schema_types"]), "pending_approval", result["needs_field_data"]),
    )
    db.conn.commit()
    print(f"[sfge] recorded content row {content_id}: {page_file}")

    # ---- write into site worktree ----
    branch = f"sfge/case-study-{slug}"
    worktree = checkout_site(args.site_repo, "main")
    try:
        out = os.path.join(worktree, page_file)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(result["html"])

        # case-studies hub index (card list) so the page isn't orphaned.
        # If a hub already exists (from a previous run), append this page's card.
        hub_path = os.path.join(worktree, "case-studies", "index.html")
        os.makedirs(os.path.dirname(hub_path), exist_ok=True)
        _upsert_hub(hub_path, result, worktree)
        print("[sfge] case-studies/index.html hub up to date")

        if os.path.exists(os.path.join(worktree, "sitemap.xml")):
            SITEMAP.patch_sitemap(os.path.join(worktree, "sitemap.xml"), result["canonical_path"])
            print(f"[sfge] patched sitemap.xml with {result['canonical_path']}")

        run(["git", "checkout", "-b", branch], worktree)
        run(["git", "add", "-A"], worktree)
        # only commit if there's something new
        added = [ln for ln in run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"], worktree
        ).splitlines() if ln.strip()]
        if added:
            run(["git", "commit", "-m",
                 f"Add case study: {title}\n\nGenerated by SFGE (job {job.get('job_id')}). Human review required."],
                worktree)
        print(f"[sfge] committed {len(added)} files on branch {branch}")

        if args.no_open_pr:
            print(f"[sfge] --no-open-pr: branch {branch} ready locally at {worktree}")
            _update_content(db, content_id, "pending_approval", None)
            import shutil as _sh
            _sh.rmtree(worktree, ignore_errors=True)
            return

        # push
        push_url = os.environ.get(
            "SFGE_PUSH_URL",
            f"https://x-access-token:{token}@github.com/{args.site_repo}.git",
        )
        run(["git", "push", "-u", push_url, branch], worktree)
        print(f"[sfge] pushed branch {branch}")

        # open PR
        status, pr = gh_request(
            "POST", f"repos/{args.site_repo}/pulls",
            body={
                "title": f"Case study: {title}"[:200],
                "head": branch,
                "base": "main",
                "body": _pr_body(result, job),
            },
            token=token,
        )
        if status != 201:
            print(f"[sfge] PR open FAILED ({status}): {pr.get('error', pr)}")
            _update_content(db, content_id, "pr_failed", None)
            sys.exit(1)
        pr_url = pr.get("html_url")
        print(f"[sfge] PR: {pr_url}")
        _update_content(db, content_id, "pending_approval", pr_url)
    finally:
        import shutil
        shutil.rmtree(worktree, ignore_errors=True)


def _update_content(db, content_id, status, pr_url):
    if pr_url:
        db.execute("UPDATE content SET publish_status=?, pr_url=? WHERE content_id=?",
                   (status, pr_url, content_id))
    else:
        db.execute("UPDATE content SET publish_status=? WHERE content_id=?",
                   (status, content_id))
    db.conn.commit()


def _hub_card(result):
    """Card markup for the case-studies hub grid (uses the page H1, not the <title>)."""
    heading = result.get("h1") or result["title"]
    return (
        f'      <a class="service-card" href="./{result["slug"]}.html">'
        f'<div class="section-head" style="margin-bottom:12px;"><div class="eyebrow">Case study</div>'
        f'<h3>{heading}</h3></div>'
        f'<p>Straight Flush Plumbing &mdash; {result["description"]}</p>'
        f'<span style="color:var(--accent);">Read the case study &rarr;</span></a>\n'
    )


def _upsert_hub(hub_path, result, worktree):
    """Create the case-studies hub if missing; otherwise append this page's card."""
    from modules.objects import page as P
    prefix = "../"
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage",
               "name": "Case Studies",
               "url": f"{S.DOMAIN}/case-studies/"}]

    if os.path.exists(hub_path):
        # Append this page's card to the existing card grid.
        import re as _re
        with open(hub_path, encoding="utf-8") as f:
            existing = f.read()
        if result["slug"] in existing:
            return  # already listed
        card = _hub_card(result)
        # Insert into the card grid. Cards contain nested <div> elements, so a
        # naive non-greedy (.*?)</div> match lands on an inner close tag. Count
        # <div>/</div> depth to find the card-grid's real matching close tag.
        start = _re.search(r'<div class="card-grid[^"]*"[^>]*>', existing)
        if not start:
            raise RuntimeError("hub page has no card-grid to extend")
        grid_start = start.end()
        depth = 0
        grid_end = None
        for m in _re.finditer(r'<div\b|</div>', existing[grid_start:]):
            if m.group(0) == "<div":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    grid_end = grid_start + m.end()
                    break
        if grid_end is None:
            raise RuntimeError("hub page has no card-grid to extend")
        new_inner = existing[grid_start:grid_end].rstrip() + "\n" + card
        existing = existing[:grid_start] + new_inner + existing[grid_end:]
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(existing)
        return

    html = P.head("Straight Flush Case Studies | Real Jobs, Real Results",
                  "Real slab leak detection and plumbing jobs completed by Straight Flush Plumbing across South Orange County.",
                  "case-studies/", prefix, schema)
    html += P.nav(prefix)
    html += P.page_hero(prefix, "Proof of work",
                        "Straight Flush Case Studies",
                        "Real jobs, real neighborhoods, real results — documented after each completed project.",
                        cta_label="Schedule Service", cta_href="contact.html",
                        trail=[("Home", "index.html"), ("Case Studies", None)])
    card = _hub_card(result)
    html += f"""<section>
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">Work we&rsquo;ve done</div>
      <h2>Jobs completed in South Orange County</h2>
    </div>
    <div class="card-grid reveal" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr));">
{card}
    </div>
  </div>
</section>
"""
    html += P.cta_band(prefix, "Have a plumbing problem in South OC?",
                       "Lance answers the phone. Diagnose-first, honest pricing, 24/7 emergencies.",
                       cta_label="Call (949) 374-6524", cta_href="contact.html")
    html += P.footer(prefix)
    with open(hub_path, "w", encoding="utf-8") as f:
        f.write(html)


def _pr_body(result, job):
    return f"""Automated case-study page generated by **SFGE** (Straight Flush Growth Engine).

**Summary:** {result['title']}
**Canonical:** https://straightflushplumbingoc.com/{result['canonical_path']}

**Source of truth:** a real completed job (id `{job.get('job_id')}`) in the SFGE database.
No customer-identifying details, addresses, or exact prices are included.

**What's in this PR:**
- New page `{result['slug']}.html`
- JSON-LD schema: `{', '.join(result['schema_types'])}` (matches existing site schema patterns)
- Internal links: city page + service page + nearest-neighbor chips
- sitemap.xml updated

**Guardrail:** this PR requires human review before merge. Once approved and merged,
the page goes live — no push to `main` is ever made by SFGE directly.

_This PR was created by an AI agent (OpenHands) on behalf of the Straight Flush team._
"""


if __name__ == "__main__":
    main()