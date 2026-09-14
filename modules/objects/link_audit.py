#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module C — Link-graph audit + auto-linking.

Given a checkout/worktree of the site repo, crawls the flat HTML files and
builds a link graph:

- files -> relative outbound hrefs (excluding mailto/tel/#anchors/external)
- reports orphan pages (no inbound links, not an entry point)
- reports broken internal links (target file missing on disk)
- can AUTO-INJECT a "related services" link block into orphaned generated
  pages (case-studies/ or academy/) pointing back to their city/service
  pages — this is a *safe* autocorrect (guardrail: never touches index/sitemap).

Used by scripts/audit_engine.py (Module D) weekly.
"""
import os
import re

from . import links as L

# Files that crawlers reach directly — never considered orphans.
ENTRY_POINTS = L.LinkGraph.ENTRY_POINTS

# Only auto-inject into pages we generate (never hand-authored marketing pages).
GENERATED_DIRS = ("case-studies/", "academy/")


def _hrefs(html):
    """Yield relative internal hrefs (normalized, no fragment)."""
    for m in re.finditer(r'href="([^"]+)"', html):
        href = m.group(1)
        if href.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:")):
            continue
        href = href.split("#")[0].split("?")[0]
        if href:
            yield href


def crawl(root):
    """Return {page_relpath: {outbound set}}. page paths use forward slashes."""
    graph = {p: set() for p in ENTRY_POINTS if os.path.exists(os.path.join(root, p))}
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in files:
            if not fn.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            with open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace") as f:
                html = f.read()
            # resolve relative hrefs from this page's directory
            base = os.path.dirname(rel) if os.path.dirname(rel) else ""
            outbound = set()
            for href in _hrefs(html):
                joined = os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
                # The site author writes root-level pages with "../foo.html"
                # hrefs (Cloudflare serves them at the site root). Normalize
                # escaping-of-root to root-relative so inbound links count.
                while joined == ".." or joined.startswith("../"):
                    joined = joined[3:] if joined != ".." else ""
                    joined = joined.lstrip("/")
                if not joined:
                    continue
                outbound.add(joined)
            graph[rel] = outbound
    return graph


_ASSET_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
               ".css", ".js", ".mp4", ".webm", ".pdf", ".woff", ".woff2",
               ".json", ".webmanifest", ".txt", ".xml"}


def _is_page_target(href):
    """True if href looks like a navigable HTML page (or clean-URL page)."""
    if href.endswith("/"):
        return True  # directory hub
    basename = href.rsplit("/", 1)[-1]
    if "." in basename:
        ext = "." + basename.rsplit(".", 1)[-1].lower()
        return ext not in _ASSET_EXTS
    return True  # extensionless clean URL


def find_broken(graph, root):
    """Return list of (page, broken_href) where a PAGE target file is absent.

    Asset hrefs (.jpg/.css/.js/etc.) are not page links and are not reported.
    Extensionless clean-URL targets that map to an existing .html on disk are
    considered valid (the site serves them that way).
    """
    existing = set(graph.keys())
    existing_html = {p for p in existing if p.endswith(".html")}
    broken = []
    for page, outs in graph.items():
        for o in outs:
            if not _is_page_target(o):
                continue
            # normalize: extensionless clean URLs resolve to .html on disk,
            # and a directory target (e.g. "academy/") maps to its index.html
            o2 = o.rstrip("/")
            candidates = {o, o + ".html", o2, o2 + ".html", o2 + "/index.html"}
            if not (candidates & existing_html):
                broken.append((page, o))
    return broken


def find_orphans(graph):
    """Pages with no inbound *page* link. 404 and asset-less pages excluded."""
    inbound = {}
    for _page, outs in graph.items():
        for o in outs:
            inbound[o] = inbound.get(o, 0) + 1
    return [
        u for u in graph
        if inbound.get(u, 0) == 0
        and u not in ENTRY_POINTS
        and os.path.basename(u) != "404.html"
    ]


def related_block(page_rel, prefix="", title="More from Straight Flush"):
    """HTML snippet linking back to the page's city/service via its filename."""
    slug = os.path.basename(page_rel).replace(".html", "")
    label = slug.replace("-", " ").title()
    return (
        f'<div class="cta-band reveal" style="margin-top:28px;">'
        f'<div><h2 style="font-size:1.4rem;">{prefix}{label}</h2>'
        f'<p>Call (949) 374-6524 — diagnose-first, honest pricing.</p></div>'
        f'<a href="{L.city_page_absolute("laguna-niguel")}" class="btn btn-primary">Service Areas</a>'
        f'</div>'
    )