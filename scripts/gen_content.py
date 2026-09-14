#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module B — Generate supporting content (blog/comparison) from the
opportunities backlog + real Module F data, and open a PR.

Usage:
  python3 scripts/gen_content.py --opportunity 12
  python3 scripts/gen_content.py --topic slab-vs-general-leak          # evergreen comparison
  python3 scripts/gen_content.py --city "Mission Viejo" --service "Slab Leak Detection"
  python3 scripts/gen_content.py --auto           # top open opportunity, throttled

Behavior:
- Reads real jobs + approved reviews for the target city/service for Tier-1
  grounding; otherwise produces an honest Tier-2 page (guardrail 2).
- Throttle (guardrail 5): --auto processes at most N opportunities from the
  backlog in one run (default 1). You must have REAL job/review data before
  the backlog can be consumed faster than Module F supplies it.
- Writes into the site repo's `academy/`, patches sitemap.xml, opens a PR.
- NEVER pushes to main (guardrail 1).

Paid/API flags intentionally absent here — Module B is fully local.
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
from modules.objects import site_data as S  # noqa: E402
from modules.objects import blog_gen as BG  # noqa: E402
from modules.objects import sitemap as SITEMAP  # noqa: E402

GITHUB = "https://api.github.com"
DEFAULT_SITE_REPO = os.environ.get("SFGE_SITE_REPO", "straightflushplumbing03/-Up2datewebsiteseo")

TOPICS = set(BG._COMPARISON.keys())


def gh_request(method, api_path, body=None, token=None):
    req = urllib.request.Request(f"{GITHUB}/{api_path.lstrip('/')}", method=method)
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
        return e.code, {"error": e.read().decode("utf-8", "replace")[:500]}


def run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip()


def checkout_site(site_repo, branch="main"):
    worktree = tempfile.mkdtemp(prefix="sfge-site-")
    clone_url = os.environ.get("SFGE_SITE_CLONE_URL", f"https://github.com/{site_repo}.git")
    run(["git", "clone", "--depth", "1", "--branch", branch, clone_url, worktree])
    run(["git", "config", "user.email", "sfge-engine@users.noreply.github.com"], worktree)
    run(["git", "config", "user.name", "SFGE Engine"], worktree)
    return worktree


def _record_content(db, result, tier):
    content_id = db.execute(
        """INSERT INTO content (type, tier, city, service_type, source_job_ids,
                                site_path, canonical_url, title, schema_types,
                                publish_status, needs_field_data)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        ("blog", tier,
         result.get("city") or result.get("opportunity_city"),
         result.get("service_type") or result.get("opportunity_service"),
         json.dumps(result.get("source_job_ids") or []),
         f"academy/{result['slug']}.html",
         f"{S.DOMAIN}/{result['canonical_path']}", result["title"],
         json.dumps(result["schema_types"]), "pending_approval",
         1 if tier == "tier2" else 0),
    )
    db.conn.commit()
    return content_id


def _upsert_academy_hub(hub_path, result, worktree):
    """Create academy-index hub if missing; else append a card (like case-studies)."""
    from modules.objects import page as P
    prefix = "../"
    if os.path.exists(hub_path):
        import re as _re
        with open(hub_path, encoding="utf-8") as f:
            existing = f.read()
        if result["slug"] in existing:
            return
        card = (
            f'      <a class="service-card" href="./{result["slug"]}.html">'
            f'<div class="section-head" style="margin-bottom:12px;"><div class="eyebrow">From the blog</div>'
            f'<h3>{result["title"]}</h3></div>'
            f'<p>{result["description"]}</p>'
            f'<span style="color:var(--accent);">Read &rarr;</span></a>\n'
        )
        grid = _re.search(r'<div class="card-grid[^"]*">(.*?)</div>', existing, _re.S)
        if not grid:
            raise RuntimeError("hub page has no card-grid to extend")
        inner = grid.group(1)
        existing = existing[:grid.start(1)] + inner + "\n" + card + existing[grid.end(1):]
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(existing)
        return
    schema = [{"@context": "https://schema.org", "@type": "CollectionPage",
               "name": "Academy", "url": f"{S.DOMAIN}/academy/"}]
    html = P.head("Straight Flush Academy | Plumbing Guides",
                  "Plain-English plumbing guides from the owner-operated South OC specialist.",
                  "academy/", prefix, schema)
    html += P.nav(prefix)
    html += P.page_hero(prefix, "Academy",
                        "Plumbing guides from the field",
                        "Honest, practical answers about slab leaks, repiping, and water heaters.",
                        cta_label="Schedule Service", cta_href="contact.html",
                        trail=[("Home", "index.html"), ("Academy", None)])
    card = (f'      <a class="service-card" href="./{result["slug"]}.html">'
            f'<div class="section-head" style="margin-bottom:12px;"><div class="eyebrow">From the blog</div>'
            f'<h3>{result["title"]}</h3></div>'
            f'<p>{result["description"]}</p>'
            f'<span style="color:var(--accent);">Read &rarr;</span></a>\n')
    html += f"""<section>
  <div class="wrap">
    <div class="section-head reveal">
      <div class="eyebrow">Guides</div>
      <h2>Latest from the blog</h2>
    </div>
    <div class="card-grid reveal" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr));">
{card}
    </div>
  </div>
</section>
"""
    html += P.cta_band(prefix, "Have a plumbing problem?",
                       "Lance answers the phone. Diagnose-first, honest pricing, 24/7 emergencies.",
                       cta_label="Call (949) 374-6524", cta_href="contact.html")
    html += P.footer(prefix)
    with open(hub_path, "w", encoding="utf-8") as f:
        f.write(html)


def _pr_body(result):
    return f"""Automated blog page generated by **SFGE** (Straight Flush Growth Engine).

**Summary:** {result['title']}
**Canonical:** https://straightflushplumbingoc.com/{result['canonical_path']}

**Source of truth:** {result.get('proof_note', 'real Module F job/review data')} —
no customer-identifying details, addresses, or exact prices are included.

**What's in this PR:**
- New page `{result['slug']}.html`
- JSON-LD schema: `{', '.join(result['schema_types'])}` (matches existing site schema patterns)
- Internal links to city + service pages + nearest-neighbor chips

**Guardrail:** requires human review before merge.

_This PR was created by an AI agent (OpenHands) on behalf of the Straight Flush team._
"""


def main():
    ap = argparse.ArgumentParser(description="Generate supporting content (Module B)")
    ap.add_argument("--opportunity", type=int, default=None,
                    help="opportunities.opp_id to generate")
    ap.add_argument("--topic", choices=sorted(TOPICS),
                    help="evergreen comparison topic")
    ap.add_argument("--city", default=None)
    ap.add_argument("--service", default=None)
    ap.add_argument("--auto", action="store_true",
                    help="process top open opportunity(s) from 'auto' pool")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--site-repo", default=DEFAULT_SITE_REPO)
    ap.add_argument("--no-open-pr", action="store_true")
    args = ap.parse_args()

    db = get_db(os.path.join(_REPO, "sfge.db"))
    token = os.environ.get("GITHUB_TOKEN", "")

    # ---- pick what to generate ----
    if args.topic:
        result = BG.build_comparison_page(args.topic, jobs=[], reviews=[])
        result["proof_note"] = "a curated evergreen topic (comparison/explainer content)."
        print(f"[sfge] comparison topic: {args.topic}")
        gen = result
    elif args.city or args.service:
        if not (args.city and args.service):
            ap.error("--city and --service go together")
        opp = {"city": args.city, "service_type": args.service,
               "keyword": f"{args.service.lower()} {args.city}",
               "intent_type": "commercial"}
        gen = _gen_from_opp(db, opp)
    elif args.opportunity:
        opp = db.one("SELECT * FROM opportunities WHERE opp_id=?", (args.opportunity,))
        if not opp:
            ap.error(f"no opportunity {args.opportunity}")
        gen = _gen_from_opp(db, opp)
    elif args.auto:
        rows = db.rows("""SELECT * FROM opportunities
                          WHERE status='open' AND city IS NOT NULL AND service_type IS NOT NULL
                          ORDER BY priority_score DESC LIMIT ?""", (args.limit,))
        if not rows:
            print("[sfge] no open opportunities to consume")
            return
        for i, opp in enumerate(rows):
            print(f"[sfge] [{i+1}/{len(rows)}] generating for {opp['keyword']}")
            gen = _gen_from_opp(db, opp)
            _write_pr(db, gen, args, token)
        return
    else:
        ap.error("need --topic, --city+--service, --opportunity, or --auto")

    _write_pr(db, gen, args, token)


def _gen_from_opp(db, opp):
    city = opp["city"]
    service = opp["service_type"]
    jobs = db.rows(
        "SELECT * FROM jobs WHERE lower(city)=lower(?) AND lower(service_type)=lower(?)",
        (city, service),
    )
    reviews = db.rows(
        """SELECT * FROM reviews WHERE lower(extracted_city)=lower(?) 
           AND lower(extracted_service)=lower(?)""",
        (city, service),
    )
    result = BG.build_service_explainer(opp, jobs, reviews)
    result["opportunity_city"] = city
    result["opportunity_service"] = service
    result["source_job_ids"] = [j["job_id"] for j in jobs]
    result["proof_note"] = (f"{len(jobs)} real job(s) + {len([r for r in reviews if r.get('approved_for_publish')])} "
                            f"approved review(s) for {city} / {service}.")
    return result


def _write_pr(db, result, args, token):
    content_id = _record_content(db, result, result.get("tier", "tier2"))
    print(f"[sfge] recorded content row {content_id}: academy/{result['slug']}.html")

    branch = f"sfge/blog-{result['slug']}"
    worktree = checkout_site(args.site_repo, "main")
    try:
        out = os.path.join(worktree, "academy", f"{result['slug']}.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(result["html"])

        hub_path = os.path.join(worktree, "academy", "index.html")
        os.makedirs(os.path.dirname(hub_path), exist_ok=True)
        _upsert_academy_hub(hub_path, result, worktree)

        if os.path.exists(os.path.join(worktree, "sitemap.xml")):
            SITEMAP.patch_sitemap(os.path.join(worktree, "sitemap.xml"), result["canonical_path"])
            print(f"[sfge] patched sitemap.xml with {result['canonical_path']}")

        run(["git", "checkout", "-b", branch], worktree)
        run(["git", "add", "-A"], worktree)
        added = [ln for ln in run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"], worktree
        ).splitlines() if ln.strip()]
        if added:
            run(["git", "commit", "-m",
                 f"Add blog: {result['title']}\n\nGenerated by SFGE. Human review required."],
                worktree)
        print(f"[sfge] committed {len(added)} files on branch {branch}")

        if args.no_open_pr:
            print(f"[sfge] --no-open-pr: branch {branch} ready locally at {worktree}")
            db.execute("UPDATE content SET publish_status='pending_approval' WHERE content_id=?",
                       (content_id,))
            db.conn.commit()
            shutil.rmtree(worktree, ignore_errors=True)
            return

        push_url = os.environ.get(
            "SFGE_PUSH_URL",
            f"https://x-access-token:{token}@github.com/{args.site_repo}.git",
        )
        run(["git", "push", "-u", push_url, branch], worktree)
        status, pr = gh_request(
            "POST", f"repos/{args.site_repo}/pulls",
            body={
                "title": f"Blog: {result['title']}"[:200],
                "head": branch,
                "base": "main",
                "body": _pr_body(result),
            },
            token=token,
        )
        if status != 201:
            print(f"[sfge] PR open FAILED ({status}): {pr.get('error', pr)}")
            db.execute("UPDATE content SET publish_status='pr_failed' WHERE content_id=?", (content_id,))
            db.conn.commit()
            sys.exit(1)
        pr_url = pr.get("html_url")
        print(f"[sfge] PR: {pr_url}")
        db.execute("UPDATE content SET publish_status='pending_approval', pr_url=? WHERE content_id=?",
                   (pr_url, content_id))
        db.conn.commit()
    finally:
        shutil.rmtree(worktree, ignore_errors=True)


if __name__ == "__main__":
    main()