#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module D — Technical / GEO audit checks.

Each check is a pure function against a site-root directory. They return
findings: dicts with {date, category, severity, message, url, auto_fixed}.

Categories: canonical, sitemap, robots, schema, images, mobile, links, cwv.

Safe autocorrects (used by scripts/audit_engine.py):
- missing image alt text  -> insert descriptive alt
- missing canonical link  -> insert canonical into <head>
- broken internal link    -> report only (never guess a replacement)

Everything else is reported for human review (guardrail 4: protect the
existing SEO baseline, don't change it without a human).
"""
import datetime as _dt
import json
import os
import re
import urllib.parse

from . import link_audit as LA
from . import site_data as S

TODAY = _dt.date.today().isoformat()


def _finding(category, severity, message, url=None):
    return {
        "date": TODAY,
        "category": category,
        "severity": severity,
        "message": message,
        "url": url,
        "auto_fixed": False,
    }


def check_all(root):
    findings = []
    findings += check_canonicals(root)
    findings += check_sitemap_robots(root)
    findings += check_schema(root)
    findings += check_images(root)
    findings += check_mobile(root)
    findings += check_links(root)
    findings += check_cwv(root)
    return findings


def _html_files(root):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in files:
            if fn.endswith(".html"):
                out.append(os.path.join(dirpath, fn))
    return out


def check_canonicals(root):
    fds = []
    for path in _html_files(root):
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if "rel=\"canonical\"" not in html:
            fds.append(_finding("canonical", "high",
                                f"missing canonical link", rel))
    return fds


def check_sitemap_robots(root):
    fds = []
    sm_path = os.path.join(root, "sitemap.xml")
    rob_path = os.path.join(root, "robots.txt")
    if not os.path.exists(sm_path):
        fds.append(_finding("sitemap", "high", "sitemap.xml missing"))
    else:
        with open(sm_path, encoding="utf-8") as f:
            sm = f.read()
        if "<urlset" not in sm or "</urlset>" not in sm:
            fds.append(_finding("sitemap", "high", "sitemap.xml is not a valid <urlset>"))
        else:
            locs = re.findall(r"<loc>(.*?)</loc>", sm)
            if len(set(locs)) != len(locs):
                fds.append(_finding("sitemap", "medium", "sitemap.xml contains duplicate <loc>"))
            for loc in locs:
                # verify referenced page exists on disk (strip domain, leading /)
                path = urllib.parse.urlparse(loc).path.lstrip("/").rstrip("/")
                # clean-URL extensionless pages map to .html on disk
                if not os.path.exists(os.path.join(root, path)):
                    if path and not os.path.exists(os.path.join(root, path + ".html")):
                        fds.append(_finding("sitemap", "medium",
                                            f"sitemap references missing page: {loc}", loc))
    if not os.path.exists(rob_path):
        fds.append(_finding("robots.txt", "high", "robots.txt missing"))
    return fds


_SCHEMA_TYPES = ("BreadcrumbList", "Service", "Plumber", "LocalBusiness",
                 "FAQPage", "Article", "Review", "AggregateRating", "WebSite")


def check_schema(root):
    fds = []
    for path in _html_files(root):
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not blocks:
            # informational pages may legitimately have no schema; only flag
            # pages that should (case studies, services, cities, blog)
            if any(rel.startswith(d) for d in ("case-studies/", "services/", "cities/")):
                fds.append(_finding("schema", "medium", "no JSON-LD schema found", rel))
            continue
        for block in blocks:
            try:
                obj = json.loads(block)
            except ValueError:
                fds.append(_finding("schema", "high", "invalid JSON-LD (unparseable)", rel))
                continue
            # handle arrays or single objects
            objs = obj if isinstance(obj, list) else [obj]
            for one in objs:
                t = one.get("@type") or one.get("@graph", [{}])[0].get("@type")
                if t and t not in _SCHEMA_TYPES:
                    fds.append(_finding("schema", "low",
                                        f"unrecognized schema type {t}", rel))
    return fds


def check_images(root):
    fds = []
    for path in _html_files(root):
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        for m in re.finditer(r"<img\b([^>]*)>", html):
            tag = m.group(1)
            alt = re.search(r'alt="([^"]*)"', tag)
            if alt is None:
                src = re.search(r'src="([^"]*)"', tag)
                srclabel = src.group(1) if src else "(no src)"
                fds.append(_finding("images", "medium",
                                    f"img missing alt text: {srclabel}", rel))
    return fds


def check_mobile(root):
    fds = []
    for path in _html_files(root):
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if 'name="viewport"' not in html:
            fds.append(_finding("mobile", "medium", "missing viewport meta", rel))
    return fds


def check_links(root):
    graph = LA.crawl(root)
    fds = []
    broken = LA.find_broken(graph, root)
    for page, href in broken:
        fds.append(_finding("links", "medium",
                            f"broken internal link -> {href}", page))
    orphans = LA.find_orphans(graph)
    for o in orphans:
        fds.append(_finding("links", "medium", f"orphan page (no inbound)", o))
    return fds


def _doc_size_kb(path):
    return os.path.getsize(path) / 1024.0


def check_cwv(root):
    """Lightweight stand-in for Core Web Vitals scoring.

    Flags very large HTML (proxy for slow LCP) and image assets over 300KB
    (proxy for layout shift / CLS risk). Real CWV requires the CrUX API or a
    headless browser; this is a deterministic local heuristic that keeps
    the audit runnable with zero external services.
    """
    fds = []
    big = []
    for path in _html_files(root):
        if _doc_size_kb(path) > 200:
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            big.append(f"{rel} ({_doc_size_kb(path):.0f}KB)")
    if big:
        fds.append(_finding("cwv", "medium", "large HTML pages: " + "; ".join(big[:5])))
    img_dir = os.path.join(root, "assets", "img")
    if os.path.isdir(img_dir):
        heavy = []
        for fn in os.listdir(img_dir):
            fp = os.path.join(img_dir, fn)
            sz = os.path.getsize(fp) / 1024.0
            if sz > 300:
                heavy.append(f"{fn} ({sz:.0f}KB)")
        if heavy:
            fds.append(_finding("cwv", "medium",
                                "heavy images >300KB: " + "; ".join(heavy[:8])))
    return fds


# ---- safe autocorrects -------------------------------------------------

def autofix_canonical(path):
    """Insert a canonical link into <head> if missing. Returns True if fixed."""
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    if 'rel="canonical"' in html:
        return False
    rel = os.path.basename(path).replace(".html", "")
    m = re.search(r"(<head>)(.*?)(</head>)", html, re.S)
    if not m:
        return False
    canon = (f'<link rel="canonical" href="{S.DOMAIN}/{rel}">\n')
    new = m.group(1) + "\n" + canon + m.group(2) + m.group(3)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def autofix_alt(path, default_alt="Straight Flush Plumbing & Leak Detection"):
    """Add descriptive alt to <img> with no alt attribute. Returns count fixed."""
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    count = 0

    def fix(m):
        nonlocal count
        tag = m.group(1)
        if 'alt=' in tag:
            return m.group(0)
        count += 1
        return f"<img{tag} alt=\"{default_alt}\">"

    new = re.sub(r"<img\b([^>]*)>", fix, html)
    if count:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    return count