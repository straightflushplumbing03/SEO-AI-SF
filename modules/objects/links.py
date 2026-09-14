#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal-link engine (Module C foundation, used by F2).

Rules (mirror the site's conventions):
- relative paths only, no leading slash;
- every new page links to its 2-3 nearest neighboring city pages (city-chip grid);
- every case study links to its city page + service page;
- a link graph is maintained so no page is orphaned (hub index lists every page).
"""
from . import site_data as S


def city_page_url(slug):
    return f"cities/{slug}.html"


def service_page_url(slug):
    return f"services/{slug}.html"


def case_study_url(slug):
    return f"case-studies/{slug}.html"


def city_page_absolute(slug):
    return f"{S.DOMAIN}/cities/{slug}"


def case_study_absolute(slug):
    return f"{S.DOMAIN}/case-studies/{slug}"


def nearest_city_links(city_slug, limit=3):
    return [c for c in S.city_neighbors(city_slug) if S.is_valid_city(c)][:limit]


class LinkGraph:
    """Tracks pages and their outbound links so writers can check for orphans."""

    def __init__(self):
        self.pages = {}  # url -> set(outbound relative urls)

    def add(self, url, outbound):
        self.pages.setdefault(url, set()).update(outbound)

    # Entry points a crawler reads directly (never "orphans").
    ENTRY_POINTS = {"index.html", "sitemap.xml", "robots.txt"}

    def orphaned(self):
        """Return pages with no inbound links (excluding crawler entry points)."""
        inbound = {}
        for outs in self.pages.values():
            for o in outs:
                inbound.setdefault(o, 0)
                inbound[o] += 1
        return [u for u in self.pages if inbound.get(u, 0) == 0 and u not in self.ENTRY_POINTS]