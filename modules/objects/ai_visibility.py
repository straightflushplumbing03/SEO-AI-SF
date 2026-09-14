#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module E — AI search visibility tracker.

Maintains the fixed prompt panel (customer-style queries across the 20
service-area cities) and records engine citations:

- Panel: ~40 prompts (commercial + informational + emergency) derived
  deterministically from site_data, so the panel stays stable run-to-run
  (unit of measure for trend reporting).
- Probes: two ways to get answers.
    * manual  — Lance/SFGE pastes the AI engine's answer into
      `scripts/ai_visibility.py --add-result ...` (no API cost).
    * serpapi — real query API, gated behind guardrail 6 (explicit
      sign-off + SFGE_SERPAPI_KEY).
- Each check records: engine, prompt, cited (bool), competitors_cited[],
  source_urls_pulled[]. Non-citation + identifiable content gap feeds
  Module A via `build_opportunities --feed-gaps`.

This module intentionally does no scraping that violates ToS. It only
provides a recording surface + the SerpApi client for the operator to run
after sign-off.
"""
import datetime as _dt
import json
import os
import urllib.parse
import urllib.request

from . import keywords as K
from . import site_data as S

ENGINES = ("chatgpt", "perplexity", "gemini", "google-ai-overview")

BRAND_TOKENS = [
    "straight flush plumbing", "straightflush", "straight flush",
    "straight-flush", "straightflushplumbingoc",
    "(949) 374-6524", "949-374-6524", "9493746524",
]


def _city_label(slug):
    return S.CITY_LABEL.get(slug, slug.replace("-", " ").title())


def build_panel():
    """Deterministic ~40-prompt panel across all service-area cities."""
    labels = list(S.CITY_LABEL.values())
    # one commercial + one informational prompt per city (rotating service),
    # plus a handful of emergency prompts.
    services = K.CORE_SERVICES
    panel = []
    for i, city in enumerate(labels):
        svc = services[i % len(services)]
        panel.append({
            "prompt": f"best {svc.lower()} company in {city}",
            "city": city, "intent": "commercial",
        })
        panel.append({
            "prompt": f"how much does {svc.lower()} cost in {city}",
            "city": city, "intent": "informational",
        })
    # emergency prompts for a spread of big-demand cities
    for city in ("Laguna Niguel", "Mission Viejo", "Irvine", "San Clemente",
                 "Huntington Beach", "Newport Beach"):
        panel.append({
            "prompt": f"emergency slab leak plumber {city}",
            "city": city, "intent": "emergency",
        })
    return panel


def detect_citation(answer, brand_tokens=None):
    """Naive brand-citation detection in a raw AI answer string."""
    if not answer:
        return False
    text = (answer or "").lower()
    tokens = brand_tokens or BRAND_TOKENS
    return any(t in text for t in tokens)


def parse_urls(answer):
    """Extract http(s) URLs the engine pulled sources from."""
    import re
    return re.findall(r"https?://[^\s\)\"'\]]+", answer or "")


_COMPETITOR_HINTS = ("rooter", "advantage", "pro plumbing", "blue grotto",
                     "1-800", "alliance", "prestige", "bright", "gossett",
                     "vitor", "jesse", "golden state", "america's",
                     "mike diamond", "drainx", "expwy", "express plumbing")


def competitors_cited(answer, brand_tokens=None):
    """Competitors mentioned in an uncited answer (naive heuristic)."""
    if detect_citation(answer, brand_tokens):
        return []
    text = (answer or "").lower()
    found = [h.strip() for h in _COMPETITOR_HINTS if h in text]
    # dedupe, keep order
    return list(dict.fromkeys(found))[:5]


def record(db, check_date, engine, prompt, answer, brand_tokens=None):
    cited = detect_citation(answer, brand_tokens)
    comps = competitors_cited(answer, brand_tokens)
    urls = parse_urls(answer)
    db.execute(
        """INSERT INTO ai_visibility_checks
           (date, prompt, engine, cited, competitors_cited, source_urls_pulled, answer)
           VALUES (?,?,?,?,?,?,?)""",
        (check_date, prompt, engine, 1 if cited else 0,
         json.dumps(comps), json.dumps(urls), (answer or "")[:2000]),
    )
    db.conn.commit()
    return db.scalar("SELECT last_insert_rowid()")


def _suggest_opportunity(db, prompt, city, engine):
    """If uncited and we can identify a gap, insert a top-priority opp."""
    if not city:
        return None
    svc = None
    for s in K.CORE_SERVICES:
        if s.lower() in prompt.lower():
            svc = s
            break
    if not svc:
        return None
    kw = prompt.lower()
    existing = db.scalar(
        "SELECT COUNT(*) FROM opportunities WHERE keyword=? AND city=?",
        (kw, city),
    )
    if existing:
        return None
    db.execute(
        """INSERT INTO opportunities
           (keyword, city, service_type, search_volume, difficulty, intent_type,
            ai_visibility_gap_flag, status, priority_score)
           VALUES (?,?,?,?,?,'commercial',1,'open',?)""",
        (kw, city, svc, 0, 0.5, 12.0),
    )
    db.conn.commit()
    return kw


def feed_ai_gaps(db, check_date, engine):
    """Turn today's uncited checks into opportunities (Module A feedback)."""
    rows = db.rows(
        "SELECT DISTINCT prompt FROM ai_visibility_checks WHERE date=? AND cited=0",
        (check_date,),
    )
    added = []
    for r in rows:
        prompt = r["prompt"]
        city = _city_from_prompt(prompt)
        added.append(_suggest_opportunity(db, prompt, city, engine))
    return [a for a in added if a]


def _city_from_prompt(prompt):
    for slug, label in S.CITY_LABEL.items():
        if label.lower() in prompt.lower():
            return label
    return None


# ---- probes ------------------------------------------------------------
# SerpApi client — only usable after Lance signs off on cost (guardrail 6).


def serpapi_ask(prompt, engine="perplexity", api_key=None, model=None):
    """Query an AI engine through SerpApi (requires SFGE_SERPAPI_KEY + signoff).

    Returns raw answer string. `engine` selects the endpoint:
      perplexity / chatgpt / gemini / google-ai-overview.
    """
    key = api_key or os.environ.get("SFGE_SERPAPI_KEY", "")
    if not key:
        raise RuntimeError("SFGE_SERPAPI_KEY not set; cannot probe (guardrail 6 sign-off needed)")
    q = {"q": prompt, "api_key": key, "engine": engine}
    if model:
        q["model"] = model
    url = "https://serpapi.com/search?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=90) as r:
        data = json.loads(r.read().decode())
    # engines return the answer under engine-specific keys
    for key in ("answer", "perplexity_answer", "chatgpt_answer", "ai_overview",
                "organic_results", "knowledge_graph"):
        if key in data:
            if isinstance(data[key], str):
                return data[key]
            if isinstance(data[key], list) and data[key]:
                return json.dumps(data[key][:3])
            if isinstance(data[key], dict) and "text" in data[key]:
                return data[key]["text"]
    return json.dumps(data)[:2000]