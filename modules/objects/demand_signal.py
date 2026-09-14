#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module F4 — Demand-signal pre-positioning model.

The thesis: slab leaks correlate with home age. Pre-1990 copper piping
(especially 1970s-80s construction) is the highest-risk bracket for pinhole
leaks. Homes in the highest-risk age bracket, in cities where Straight Flush
has thin/no content or GBP presence, are the neighborhoods most likely to
need the service soon — and currently don't know Straight Flush exists.

Data sources (public, no paid API):
- Census ACS 5-year median year structure built / housing units by
  year built, at city/place level: use api.census.gov endpoints.
- Straight Flush's own job history by city (jobs table) as proof signal.

Scoring (0-100) per city/neighborhood:
  demand_score = (risk_bracket_share x weight) + (no_job_boost) + (thin_content_boost)
  where:
    risk_bracket_share = share of housing built 1960-1980 (peak copper failure)
    no_job_boost       = 25 if no jobs on record in that city
    thin_content_boost = 15 if no generated city page exists yet

ACS fetch is gated: SFGE runs offline by default; the CLI fetches live
Census data only when --fetch-census is passed (no API key needed, but
network+cost of Census Bureau service — fine, it's free/public).
"""
import datetime as _dt
import json
import os
import urllib.parse
import urllib.request

CENSUS_BASE = "https://api.census.gov/data/2022/acs/acs5"
# Variables describing housing units by year built (counts, total universe).
# We use B25035_MEDIAN (median year structure built) as the primary signal
# plus B25034_012 (units built 1970s) etc. when available.
YEAR_BUILT_VARS = {
    "total": "B25034_001E",       # total housing units
    "1960s": "B25034_008E",       # built 1960 to 1969
    "1970s": "B25034_007E",       # built 1970 to 1979
    "1980s": "B25034_006E",       # built 1980 to 1989
    "pre1940": "B25034_003E",
}
# Median year structure built (calendar year).
MEDIAN_YEAR_VAR = "B25035_001E"

CITY_ZIP_MAP = {
    # rough city -> primary ZIPs for Census place queries (used as fallback)
    "Aliso Viejo": "92656", "Costa Mesa": "92626", "Coto de Caza": "92679",
    "Dana Point": "92624", "Dove Canyon": "92679", "Foothill Ranch": "92610",
    "Huntington Beach": "92646", "Irvine": "92620", "Ladera Ranch": "92694",
    "Laguna Beach": "92651", "Laguna Hills": "92653", "Laguna Niguel": "92677",
    "Laguna Woods": "92637", "Lake Forest": "92630",
    "Mission Viejo": "92692", "Newport Beach": "92660", "Orange": "92866",
    "Rancho Santa Margarita": "92688", "San Clemente": "92672",
    "San Juan Capistrano": "92675", "Tustin": "92780",
}

_RISK_WEIGHT = {
    "pre1940": 0.55,
    "1960s": 0.90,
    "1970s": 1.00,
    "1980s": 0.80,
}


def _year_built_profile_fallback():
    """Offline default so the model runs without network.

    Values are approximate 2018-2022 ACS place-level medians for the major
    OC cities (1970s/80s dominant for inland, mixed coastal). These are
    *model defaults* and should be replaced by --fetch-census for real runs.
    """
    return {
        "Aliso Viejo": {"pre1940": 0, "1960s": 3, "1970s": 12, "1980s": 58},
        "Costa Mesa": {"pre1940": 8, "1960s": 22, "1970s": 25, "1980s": 15},
        "Coto de Caza": {"pre1940": 0, "1960s": 0, "1970s": 2, "1980s": 55},
        "Dana Point": {"pre1940": 8, "1960s": 15, "1970s": 22, "1980s": 20},
        "Dove Canyon": {"pre1940": 0, "1960s": 0, "1970s": 0, "1980s": 60},
        "Foothill Ranch": {"pre1940": 0, "1960s": 0, "1970s": 0, "1980s": 60},
        "Huntington Beach": {"pre1940": 6, "1960s": 18, "1970s": 22, "1980s": 18},
        "Irvine": {"pre1940": 0, "1960s": 2, "1970s": 20, "1980s": 35},
        "Ladera Ranch": {"pre1940": 0, "1960s": 0, "1970s": 0, "1980s": 2},
        "Laguna Beach": {"pre1940": 12, "1960s": 15, "1970s": 18, "1980s": 8},
        "Laguna Hills": {"pre1940": 0, "1960s": 3, "1970s": 15, "1980s": 40},
        "Laguna Niguel": {"pre1940": 0, "1960s": 2, "1970s": 12, "1980s": 52},
        "Laguna Woods": {"pre1940": 0, "1960s": 5, "1970s": 55, "1980s": 25},
        "Lake Forest": {"pre1940": 0, "1960s": 2, "1970s": 8, "1980s": 35},
        "Mission Viejo": {"pre1940": 0, "1960s": 1, "1970s": 20, "1980s": 40},
        "Newport Beach": {"pre1940": 8, "1960s": 12, "1970s": 18, "1980s": 12},
        "Orange": {"pre1940": 18, "1960s": 15, "1970s": 18, "1980s": 15},
        "Rancho Santa Margarita": {"pre1940": 0, "1960s": 0, "1970s": 0, "1980s": 5},
        "San Clemente": {"pre1940": 6, "1960s": 12, "1970s": 18, "1980s": 18},
        "San Juan Capistrano": {"pre1940": 10, "1960s": 8, "1970s": 14, "1980s": 18},
        "Tustin": {"pre1940": 12, "1960s": 20, "1970s": 22, "1980s": 12},
    }


def fetch_census_profile():
    """Fetch ACS year-built shares for each city (by ZIP ZCTA) via Census API.

    Returns {city: {bracket: share_pct}}. Uses ZIP-code (ZCTA5) queries.
    Falls back to _year_built_profile_fallback on network failure.
    """
    out = {}
    for city, zipcode in CITY_ZIP_MAP.items():
        params = {
            "get": ("," .join(YEAR_BUILT_VARS.values())),
            "for": "zip code tabulation area:" + zipcode,
            "key": os.environ.get("SFGE_CENSUS_KEY", "")  # Census is keyless for low volume
        }
        # strip empty key
        params = {k: v for k, v in params.items() if v}
        url = CENSUS_BASE + "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read().decode())
            header, *rows = data
            if not rows:
                raise ValueError("no data")
            vals = {h: (int(v) if v not in (None, "", "-") and v.isdigit() else 0)
                    for h, v in zip(header, rows[0])}
            total = max(vals.get(YEAR_BUILT_VARS["total"], 0), 1)
            rev = {k: v for v, k in YEAR_BUILT_VARS.items()}
            out[city] = {
                rev[YEAR_BUILT_VARS[b]]: round(vals.get(YEAR_BUILT_VARS[b], 0) / total * 100, 1)
                for b in ("pre1940", "1960s", "1970s", "1980s")
            }
        except Exception as e:
            out[city] = _year_built_profile_fallback().get(city, {})
    return out


def risk_score(profile):
    """Weighted risk from year-built bracket shares (0-100)."""
    total_weight = sum(_RISK_WEIGHT[b] * profile.get(b, 0) for b in _RISK_WEIGHT)
    # normalize to 0-100: cap at 80 share is ~80 score; scale down
    return round(min(100, total_weight), 1)


def demand_score(risk, has_job, has_content):
    """0-100 score combining housing risk + SFGE presence gaps."""
    s = risk * 0.55
    if not has_job:
        s += 25
    if not has_content:
        s += 15
    return round(min(100, s), 1)


def expansion_list(db, profiles=None):
    """Return sorted list of {city, risk, has_job, has_content, score}."""
    profiles = profiles or _year_built_profile_fallback()
    jobs = {r["city"].lower() for r in db.rows("SELECT DISTINCT city FROM jobs")}
    content = {r["city"].lower() for r in db.rows("SELECT DISTINCT city FROM content")}
    out = []
    for city in S_CITIES:
        prof = profiles.get(city, {})
        has_job = city.lower() in jobs
        has_content = city.lower() in content
        risk = risk_score(prof)
        out.append({
            "city": city,
            "risk": risk,
            "has_job": has_job,
            "has_content": has_content,
            "score": demand_score(risk, has_job, has_content),
        })
    return sorted(out, key=lambda x: x["score"], reverse=True)


S_CITIES = (
    "Aliso Viejo", "Costa Mesa", "Coto de Caza", "Dana Point", "Dove Canyon",
    "Foothill Ranch", "Huntington Beach", "Irvine", "Ladera Ranch", "Laguna Beach",
    "Laguna Hills", "Laguna Niguel", "Laguna Woods", "Lake Forest",
    "Mission Viejo", "Newport Beach", "Orange", "Rancho Santa Margarita",
    "San Clemente", "San Juan Capistrano", "Tustin",
)