#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module A — Keyword & opportunity engine (core vocabulary).

Generates the full keyword/opportunity cluster space deterministically:

- 5 core services (the site's money pages) x 20 cities = 100 base combos
- per combo, three intents:
    * informational  — how it works, cost, signs/symptoms, DIY vs pro
    * commercial     — "best / top / reputable <service> in <city>"
    * emergency      — "emergency / urgent / 24 hour <service> <city>"
- plus long-tail variants drawn from customer-language phrases (F3) and
  real-world problem vocabulary.

Each keyword carries: city, service_type, intent_type, generated volume
estimate (offline model) and difficulty estimate. A paid keyword API
(DataForSEO / SerpApi) can override these — see `opportunities_build.py
--api`. Guardrail 6 applies: never activate the API path without Lance's
sign-off on the specific provider + cost.
"""
from . import site_data as S

# Core services used for opportunity seeding (site money pages).
CORE_SERVICES = [
    "Slab Leak Detection",
    "PEX Repiping",
    "Water Heater Services",
    "Leak Detection",
]

# Intent templates. {city} / {service} / {nick} are expanded later.
_TEMPLATES = {
    "commercial": [
        "{service} {city}",
        "{service} company {city}",
        "best {service} {city}",
        "top rated {service} {city}",
        "reputable {service} company in {city}",
        "licensed {service} {city}",
        "{nick} {city} CA",
    ],
    "informational": [
        "how much does {service_lower} cost in {city}",
        "{service_lower} cost {city}",
        "signs of a slab leak {city}",
        "how is a slab leak detected {city}",
        "{service_lower} near {city}",
        "{service_lower} reviews {city}",
        "does my old house need a repipe {city}",
        "water heater replacement cost {city}",
    ],
    "emergency": [
        "emergency {service_lower} {city}",
        "emergency plumber {city}",
        "24 hour {service_lower} {city}",
        "urgent {service_lower} {city}",
        "slab leak emergency {city}",
    ],
}

# Rough volume/difficulty model (offline placeholder, replaced by API in prod).
# Base volume by service is scaled by city population-ish factor.
SERVICE_BASE_VOL = {
    "Slab Leak Detection": 800,
    "PEX Repiping": 500,
    "Water Heater Services": 1200,
    "Leak Detection": 900,
}
CITY_VOL_SCALE = {
    # relative demand proxy (population density of older stock matters more;
    # this is a stand-in until F4 supplies real housing-age data)
    "irvine": 1.5, "huntington-beach": 1.3, "mission-viejo": 1.3,
    "costa-mesa": 1.2, "newport-beach": 1.2, "orange": 1.2,
    "tustin": 1.1, "lake-forest": 1.0, "laguna-niguel": 1.0,
    "san-clemente": 1.0, "aliso-viejo": 0.9, "laguna-hills": 0.9,
    "ladera-ranch": 0.9, "foothill-ranch": 0.8, "rancho-santa-margarita": 0.9,
    "dana-point": 0.9, "san-juan-capistrano": 0.8,
    "dove-canyon": 0.7, "coto-de-caza": 0.7, "laguna-woods": 0.6,
    "laguna-beach": 0.7,
}

# Simple intent difficulty modifier: commercial is most contested.
_INTENT_DIFF = {"commercial": 0.62, "informational": 0.40, "emergency": 0.30}


def _city_scaled_volume(city_slug, base_vol):
    return int(base_vol * CITY_VOL_SCALE.get(city_slug, 1.0))


def _nick(service):
    return {
        "Slab Leak Detection": "slab leak specialist",
        "PEX Repiping": "repipe plumber",
        "Water Heater Services": "water heater plumber",
        "Leak Detection": "leak detection specialist",
    }.get(service, "plumber")


def cluster_keywords(city_label):
    """Return list of keyword dicts for one city across all services/intents."""
    city_slug = None
    for slug, label in S.CITY_LABEL.items():
        if label.lower() == city_label.lower():
            city_slug = slug
            break
    if city_slug is None:
        city_slug = city_label.lower().replace(" ", "-")

    out = []
    for service in CORE_SERVICES:
        low = service.lower()
        nick = _nick(service)
        for intent, templates in _TEMPLATES.items():
            for t in templates:
                kw = t.format(
                    service=service,
                    service_lower=low,
                    city=city_label,
                    nick=nick,
                )
                vol = _city_scaled_volume(city_slug, SERVICE_BASE_VOL[service])
                # long-tail informational queries have lower volume but lower diff
                if len(kw.split()) >= 5 and intent == "informational":
                    vol = int(vol * 0.25)
                diff = round(_INTENT_DIFF[intent] * (0.8 + 0.2 * (len(kw.split()) / 6)), 2)
                out.append({
                    "keyword": kw,
                    "city": city_label,
                    "service_type": service,
                    "intent_type": intent,
                    "search_volume": vol,
                    "difficulty": diff,
                })
    return out


def generate_all():
    """Keyword list for every service-area city."""
    out = []
    for slug, label in S.CITY_LABEL.items():
        out.extend(cluster_keywords(label))
    return out


# PAA-style question templates (source for FAQ schema on new pages).
PAA_TEMPLATES = {
    "Slab Leak Detection": [
        "How do you know if you have a slab leak?",
        "How much does slab leak detection cost in {city}?",
        "Can a slab leak be repaired without breaking the slab?",
        "What causes a slab leak in an older home?",
        "Is slab leak damage covered by homeowners insurance?",
    ],
    "PEX Repiping": [
        "How much does a whole-house repipe cost in {city}?",
        "How long does a repipe take?",
        "Copper vs PEX — which is better?",
        "Do I need a repipe or just a re-route?",
        "Signs your old copper pipes need replacing",
    ],
    "Water Heater Services": [
        "How long do water heaters last?",
        "Signs a water heater needs replacing",
        "How much is a new water heater installed in {city}?",
        "Tank vs tankless water heater",
        "Why is my water heater leaking?",
    ],
    "Leak Detection": [
        "How much does leak detection cost in {city}?",
        "How do plumbers detect hidden water leaks?",
        "What does a slab leak sound like?",
        "Can a leak under the slab cause foundation problems?",
        "How urgent is a slab leak?",
    ],
}


def paa_questions(service, city_label):
    tmpl = PAA_TEMPLATES.get(service, PAA_TEMPLATES["Leak Detection"])
    return [q.format(city=city_label) for q in tmpl]