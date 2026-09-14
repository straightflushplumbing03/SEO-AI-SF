#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F3 — Review-to-content mining (lightweight NLP, zero deps).

Given a raw customer review (text + rating), extract:
- sentiment: positive | neutral | negative
- service mentioned (from the site's service vocabulary)
- pain point(s) mentioned (from a domain phrase list)
- city/neighborhood if the reviewer named one

Also builds the "customer language" dataset: the real words people use
(which feeds Module A keyword targeting). Mining is deterministic and
explainable — no ML runtime, no API.

Publishing rule: a review is `approved_for_publish` only when
  rating >= 4 AND it contains a specific (service OR city) signal.
"""

from . import site_data as S

# Domain phrase -> service slug. Order matters: we match the most specific
# phrase first ("slab leak" before "leak").
_SERVICE_PHRASES = [
    ("slab leak detection", "slab leak detection"),
    ("slab leak", "slab leak detection"),
    ("acoustic leak detection", "leak detection"),
    ("leak detection", "leak detection"),
    ("leak", "leak detection"),
    ("repipe", "pex repiping"),
    ("pex", "pex repiping"),
    ("copper pipes", "pex repiping"),
    ("water heater", "water heater services"),
    ("hot water heater", "water heater services"),
    ("drain", "drain services"),
    ("clog", "drain services"),
    ("toilet", "plumbing repair"),
    ("faucet", "plumbing repair"),
    ("sink", "plumbing repair"),
    ("pipe", "plumbing repair"),
    ("plumbing", "plumbing repair"),
]

# Pain-point vocabulary -> the phrase as the customer would write it.
_PAIN_POINTS = [
    "water bill", "high water bill", "spiked", "leak", "slab leak",
    "flood", "wet spot", "water spot", "crack", "pinhole", "corrosion",
    "low pressure", "water pressure", "no hot water", "cold water",
    "water heater died", "water heater broken", "dripping", "drip",
    "mold", "musty", "smell", "puddling", "warm spot", "hot spot",
]

_NEGATIVE_WORDS = [
    "terrible", "awful", "worst", "rude", "unprofessional", "late",
    "expensive", "overcharged", "never", "avoid", "disappointed",
    "disappointment", "broke", "broken", "bad", "horrible", "scam",
    "sloppy", "left a mess", "no show", "ghosted", "refund",
]

_POSITIVE_WORDS = [
    "great", "excellent", "amazing", "awesome", "fantastic", "wonderful",
    "best", "quick", "fast", "honest", "fair", "thorough", "professional",
    "recommend", "recommended", "friendly", "polite", "clean", "careful",
    "explained", "patient", "knowledgeable", "skilled", "saved",
    "responsive", "on time", "on-time", "came same day", "trustworthy",
]


def detect_service(text):
    t = (text or "").lower()
    seen = []
    for phrase, slug in _SERVICE_PHRASES:
        if phrase in t:
            seen.append((len(phrase), slug, phrase))
    if not seen:
        return None
    # Prefer the longest (most specific) match; tie-break by list priority.
    seen.sort(key=lambda x: (-x[0], next(i for i, p in enumerate(_SERVICE_PHRASES) if p[0] == x[2])))
    slug = seen[0][1].replace(" ", "-")
    return S.SERVICE_LABEL.get(slug, slug.replace("-", " ").title())


def detect_city(text):
    t = (text or "").lower()
    for slug, label in S.CITY_LABEL.items():
        if slug.replace("-", " ") in t or label.lower() in t:
            return label
    # also match "in {city}, CA" style and comma variants
    for slug, label in S.CITY_LABEL.items():
        if label.lower() + "," in t or label.lower() + " ca" in t:
            return label
    return None


def detect_neighborhood(text):
    """Best-effort: capitalized phrase of 2+ words following 'in'/'at'."""
    import re
    m = re.search(r"\b(?:in|at|near) ([A-Z][A-Za-z' -]{2,40})", text or "")
    if m and not detect_city(m.group(1)):
        return m.group(1).strip()
    return None


def extract_pain_points(text):
    t = (text or "").lower()
    found = [p for p in _PAIN_POINTS if p in t]
    return found


def sentiment(text, rating=None):
    t = (text or "").lower()
    neg = sum(1 for w in _NEGATIVE_WORDS if w in t)
    pos = sum(1 for w in _POSITIVE_WORDS if w in t)
    if rating is not None and rating <= 2:
        return "negative"
    if rating is not None and rating >= 4 and pos and neg == 0:
        return "positive"
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract_keywords(text):
    """2-4 token windows around pain-point / service mentions (deduped)."""
    import re
    t = (text or "").lower()
    toks = re.findall(r"[a-z0-9']+", t)
    if not toks:
        return []
    out = []
    pain_anchors = set()
    for p in _PAIN_POINTS:
        span = len(p.split())
        for i in range(len(toks) - span + 1):
            if " ".join(toks[i:i + span]) == p:
                pain_anchors.add(i)
    for anchor in sorted(pain_anchors):
        window = toks[max(0, anchor): anchor + 4]
        if len(window) >= 2:
            phrase = " ".join(window)
            if phrase not in out:
                out.append(phrase)
    return out[:8]


def mine_review(text, rating=None, source="google", approve_if_specific=True):
    """Run the full mining pass. Returns dict of parsed + derived fields."""
    service = detect_service(text)
    city = detect_city(text)
    neighborhood = detect_neighborhood(text)
    pain = extract_pain_points(text)
    senti = sentiment(text, rating)
    kws = extract_keywords(text)

    specific = bool(service or city or pain)
    approved = bool(
        approve_if_specific
        and (rating or 5) >= 4
        and specific
    )
    return {
        "sentiment": senti,
        "service_type": service,
        "city": city,
        "neighborhood": neighborhood,
        "pain_points": pain,
        "keywords": kws,
        "approved_for_publish": 1 if approved else 0,
    }