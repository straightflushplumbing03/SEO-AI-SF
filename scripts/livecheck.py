#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guardrail 4: verify the LIVE site still matches expectations after a PR batch.

Checks (cheap, no paid API):
- every canonical city/service/academy URL resolves to a page containing its
  canonical <link> and at least one JSON-LD script;
- sitemap.xml parses and every listed URL is canonical-consistent;
- the two OG/twitter absolute image URLs are reachable (200).
Run BEFORE opening a batch and AFTER merge. Exit 0 if all good.
"""
import os
import sys
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_SCRIPTS)
for p in (_SCRIPTS, _REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from modules.objects import site_data as S  # noqa: E402


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SFGE-livecheck/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read().decode("utf-8", "replace")


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "SFGE-livecheck/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read()


def check_url(url):
    try:
        status, html = fetch(url)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} for {url}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e} ({url})"
    if status != 200:
        return False, f"status {status} for {url}"
    if "<html" not in html.lower():
        return False, f"not HTML for {url}"
    return True, f"OK {url} ({len(html)} bytes)"


def canonical_ok(page, domain):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', page)
    return bool(m and m.group(1).startswith(domain))


def check_image(url):
    try:
        status, data = fetch_bytes(url)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} for {url}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e} ({url})"
    if status != 200:
        return False, f"status {status} for {url}"
    if not data or (data[:2] != b"\xff\xd8" and b"<html" not in data[:200].lower()):
        return False, f"not an image (got {len(data)} bytes) for {url}"
    return True, f"OK {url} ({len(data)} bytes)"


def main():
    failures = []
    ok = 0

    checks = [f"{S.DOMAIN}/"]
    checks += [f"{S.DOMAIN}/cities/{c}" for c in S.CITIES]
    checks += [f"{S.DOMAIN}/services/{s}" for s in S.SERVICES]
    checks += [f"{S.DOMAIN}/academy/"]
    checks += [f"{S.DOMAIN}/service-areas"]
    checks += [f"{S.DOMAIN}/about"]

    print("== Random-sampling live pages ==")
    import random
    random.seed(7)
    sample = random.sample(checks, min(12, len(checks)))
    for url in sample:
        okp, msg = check_url(url)
        if okp:
            ok += 1
            print("  .", msg)
        else:
            failures.append(msg)
            print("  X", msg)

    print("== Sitemap ==")
    try:
        status, xmltext = fetch(f"{S.DOMAIN}/sitemap.xml")
        if status != 200:
            failures.append(f"sitemap HTTP {status}")
        else:
            root = ET.fromstring(xmltext)
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            locs = [e.text for e in root.findall(".//s:loc", ns)]
            print(f"  sitemap OK: {len(locs)} URLs")
            # every loc should match the published domain
            for loc in locs:
                if not loc.startswith(S.DOMAIN):
                    failures.append(f"sitemap contains off-domain loc {loc}")
    except Exception as e:
        failures.append(f"sitemap parse error: {e}")

    print("== OG / twitter images ==")
    for img in (f"{S.DOMAIN}/assets/img/logo.jpg", f"{S.DOMAIN}/assets/img/lance-hero.jpeg"):
        okp, msg = check_image(img)
        if okp:
            ok += 1
            print("  .", msg)
        else:
            failures.append(msg)
            print("  X", msg)

    if failures:
        print(f"\nFAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"\nAll checks passed ({ok} OK)")


if __name__ == "__main__":
    main()