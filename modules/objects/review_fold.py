#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F3 — Fold approved reviews into page content.

Turns mined, approved reviews into:
- standalone testimonial blocks (Review schema already handled in case_study.py),
- FAQ answers that quote real customers ("Customers in [city] often ask about X —
  here's what one recent customer said…"),
- a "customer language" summary for keyword targeting (Module A).

Rules: only reviews with approved_for_publish=1 are ever quoted; full names are
never emitted (we use the source platform + city only).
"""
import html


def approve_reviews(reviews):
    return [r for r in reviews if r.get("approved_for_publish")]


def _author_label(review):
    city = review.get("extracted_city")
    source = review.get("source") or "Google"
    if city:
        return f"Straight Flush customer in {city}"
    return f"Recent {source} review"


def quote_blocks(reviews, max_quotes=3):
    """Return list of HTML testimonial cards (mirrors case-study review-card)."""
    out = []
    for r in approve_reviews(reviews)[:max_quotes]:
        text = html.escape(str(r.get("text") or "").strip()[:400])
        if not text:
            continue
        out.append(f"""<div class="review-card-v2 reveal" style="max-width:760px;">
      <div class="stars-row"><span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span></div>
      <p style="font-style:italic;">&ldquo;{text}&rdquo;</p>
      <div class="date">{html.escape(_author_label(r))}</div>
    </div>""")
    return out


def faq_answers_from_reviews(reviews, question, product_phrase):
    """Return FAQ answer copy grounded in approved reviews, or None."""
    approved = approve_reviews(reviews)
    service_hits = [r for r in approved if r.get("extracted_service")]
    if not service_hits:
        return None
    quote = service_hits[0]["text"].strip()
    answer = (
        f"{html.escape(product_phrase)} is a common concern for homeowners in "
        f"This area. As one recent customer put it: "
        f"&ldquo;{html.escape(quote[:220])}&rdquo;" 
        " Contact Straight Flush at (949) 374-6524 to talk through your specific situation."
    )
    return answer


def customer_language(reviews):
    """Real words customers used (for Module A keyword targeting)."""
    words = set()
    services = set()
    cities = set()
    for r in approve_reviews(reviews):
        for kw in (r.get("extracted_keywords") or []):
            words.add(kw)
        if r.get("extracted_service"):
            services.add(r["extracted_service"])
        if r.get("extracted_city"):
            cities.add(r["extracted_city"])
    return {
        "phrases": sorted(words),
        "services": sorted(services),
        "cities": sorted(cities),
    }