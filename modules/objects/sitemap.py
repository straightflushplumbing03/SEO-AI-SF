#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sitemap patcher — matches the site repo's hand-maintained sitemap.xml style
(extensionless loc URLs, <lastmod>/<changefreq>/<priority> per URL). Adds or
updates a single URL for a newly generated page; the site keeps full ownership.
"""
import re
from datetime import date


def _loc(domain, path):
    return f"{domain}/{path}"


def patch_sitemap(sitemap_path, page_path, priority="0.7", changefreq="monthly"):
    """Insert or update <url> entries for page_path (e.g. 'case-studies/foo').

    Preserves ordering and formatting of the existing file.
    """
    with open(sitemap_path, encoding="utf-8") as f:
        xml = f.read()

    domain = re.search(r"<loc>(https?://[^/<]+)/", xml)
    domain = domain.group(1) if domain else "https://straightflushplumbingoc.com"

    loc = _loc(domain, page_path)
    lastmod = date.today().isoformat()
    entry = f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""

    in_urlset = ";".join(xml.split("</urlset>")[:-1])
    if f"<loc>{loc}</loc>" in in_urlset:
        # update existing entry (replace its four lines)
        xml = re.sub(
            r"  <url>\n\s*<loc>" + re.escape(loc) + r"</loc>.*?</url>",
            entry,
            xml,
            flags=re.S,
        )
    else:
        xml = xml.replace("</urlset>", entry + "\n</urlset>")

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(xml)
    return loc