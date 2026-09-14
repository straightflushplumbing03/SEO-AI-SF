#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ground-truth facts about the Straight Flush website repo
(straightflushplumbing03/-Up2datewebsiteseo), captured from the live site and
the gold HTML on disk. The page/schema/link generators in this package clone
these EXACT patterns so new pages are byte-compatible with the published site.
"""
DOMAIN = "https://straightflushplumbingoc.com"

BRAND = "Straight Flush Plumbing & Leak Detection"
PHONE_DISPLAY = "(949) 374-6524"
EMAIL = "straightflushplumbing03@gmail.com"
ADDRESS = "78 Cameray Heights, Laguna Niguel, CA 92677"
PHONE_TEL = "+19493746524"
SLOGAN = "Always A Safe Bet"

OG_IMAGE = f"{DOMAIN}/assets/img/lance-hero.jpeg"

# 21 canonical city pages (filenames as on disk).
CITIES = [
    "aliso-viejo", "costa-mesa", "coto-de-caza", "dana-point", "dove-canyon",
    "foothill-ranch", "huntington-beach", "irvine", "ladera-ranch",
    "laguna-beach", "laguna-hills", "laguna-niguel", "laguna-woods",
    "lake-forest", "mission-viejo", "newport-beach", "orange",
    "rancho-santa-margarita", "san-clemente", "san-juan-capistrano", "tustin",
]

CITY_LABEL = {slug: slug.replace("-", " ").title() for slug in CITIES}

# Service slugs as they exist in services/.
SERVICES = [
    "drain-services", "emergency-plumbing", "leak-detection",
    "pex-repiping", "plumbing-repair", "slab-leak-detection",
    "water-heater-services",
]

SERVICE_LABEL = {
    "drain-services": "Drain Services",
    "emergency-plumbing": "Emergency Plumbing",
    "leak-detection": "Leak Detection",
    "pex-repiping": "PEX Repiping",
    "plumbing-repair": "Plumbing Repair",
    "slab-leak-detection": "Slab Leak Detection",
    "water-heater-services": "Water Heater Services",
}

# Nearest-neighbour city graph (city slug -> list of neighbor slugs).
# Derived from the city-chip sections already present on the live pages.
NEIGHBORS = {
    "aliso-viejo": ["laguna-niguel", "mission-viejo", "laguna-hills", "laguna-beach"],
    "costa-mesa": ["huntington-beach", "newport-beach", "irvine", "tustin"],
    "coto-de-caza": ["rancho-santa-margarita", "dove-canyon", "ladera-ranch", "mission-viejo"],
    "dana-point": ["san-juan-capistrano", "laguna-niguel", "san-clemente", "laguna-beach"],
    "dove-canyon": ["rancho-santa-margarita", "coto-de-caza", "ladera-ranch", "mission-viejo"],
    "foothill-ranch": ["lake-forest", "irvine", "rancho-santa-margarita", "mission-viejo"],
    "huntington-beach": ["costa-mesa", "newport-beach", "fountain-valley", "westminster"],
    "irvine": ["tustin", "lake-forest", "costa-mesa", "newport-beach"],
    "ladera-ranch": ["mission-viejo", "rancho-santa-margarita", "aliso-viejo", "coto-de-caza"],
    "laguna-beach": ["laguna-niguel", "dana-point", "aliso-viejo", "laguna-hills"],
    "laguna-hills": ["laguna-niguel", "aliso-viejo", "mission-viejo", "laguna-woods"],
    "laguna-niguel": ["dana-point", "san-clemente", "mission-viejo", "aliso-viejo"],
    "laguna-woods": ["laguna-hills", "laguna-niguel", "irvine"],
    "lake-forest": ["foothill-ranch", "irvine", "mission-viejo", "laguna-hills"],
    "mission-viejo": ["laguna-niguel", "aliso-viejo", "lake-forest", "rancho-santa-margarita"],
    "newport-beach": ["costa-mesa", "huntington-beach", "irvine"],
    "orange": ["tustin", "anaheim", "villa-park"],
    "rancho-santa-margarita": ["mission-viejo", "ladera-ranch", "lake-forest", "coto-de-caza"],
    "san-clemente": ["dana-point", "san-juan-capistrano", "laguna-niguel"],
    "san-juan-capistrano": ["san-clemente", "dana-point", "laguna-niguel"],
    "tustin": ["irvine", "orange", "costa-mesa", "santa-ana"],
}

# Service types that appear in the site nav / offers (used for schema + footer).
OFFERED_SERVICES = [
    "Leak Detection",
    "Slab Leak Detection",
    "PEX Repiping",
    "Water Heater Services",
    "Drain Services",
    "Plumbing Repair",
]

# Map SFGE job.service_type values to schema-safe labels used on the site.
SERVICE_TYPE_BY_SLUG = {
    "slab_leak_detection": "Slab Leak Detection",
    "slab-leak-detection": "Slab Leak Detection",
    "leak_detection": "Leak Detection",
    "pex_repiping": "PEX Repiping",
    "water_heater": "Water Heater Services",
    "drain": "Drain Services",
    "plumbing_repair": "Plumbing Repair",
}

# Cost buckets: (label, min, max). Displayed as ranges only — never exact.
COST_BUCKETS = [
    ("Under $2,500", 0, 2500),
    ("$2,500–$5,000", 2500, 5000),
    ("$5,000–$10,000", 5000, 10000),
    ("$10,000–$15,000", 10000, 15000),
    ("$15,000–$25,000", 15000, 25000),
    ("$25,000+", 25000, None),
]

def cost_bucket_label(bucket):
    """Translate a stored bucket slug into a display string."""
    if not bucket:
        return None
    for label, lo, hi in COST_BUCKETS:
        key = f"{lo}-{hi}" if hi else f"{lo}+"
        if bucket == key:
            return label
    return bucket

def service_label_for(service_type):
    return SERVICE_TYPE_BY_SLUG.get(service_type.lower(), service_type or "Plumbing")

def is_valid_city(slug):
    return slug.lower() in CITY_LABEL

def city_neighbors(slug):
    return NEIGHBORS.get(slug.lower(), [])[:4]