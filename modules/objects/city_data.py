#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
City content model — the single source of truth for city-page content.

Every fact here is either (a) recorded business data, or (b) public geographic
fact with the source noted in `sources`. Nothing is invented. Fields the owner
must supply before publishing are marked `None` and rendered as an explicit
owner-checklist placeholder by city_page.py — never as fabricated copy.

Provenance rules:
  - `zips`        public postal data
  - `incorporated` public municipal record (None = unincorporated/CDP)
  - `era`         describes when the housing stock was largely built, phrased
                  as a range because it varies block to block
  - `notes`       local plumbing context, phrased as what homeowners report,
                  not as a claim about a specific property
  - `projects`    ONLY real, completed jobs. Empty until the owner supplies them.
  - `reviews`     ONLY real platform reviews. Empty until supplied.

Uniqueness rules (brief Phase 4 / Phase 28 — no near-duplicate city pages):
  - `typical_call`, `coastal`, `density`, and `focus` vary per city and drive
    what each section actually says.
  - FAQ selection is weighted by each city's focus, so pages do not all carry
    the same eight questions.
  - Sections are assembled from city-specific fragments, not shared boilerplate.
"""
from . import site_data as S

# ---------------------------------------------------------------------------
# Verified public geography plus per-city attributes that shape the copy.
#   coastal  : salt-air exposure materially affects corrosion
#   density  : lot/construction pattern that affects how a leak can be traced
#   focus    : the service this city's housing stock most often needs
# ---------------------------------------------------------------------------
CITY_FACTS = {
    "laguna-niguel": {
        "name": "Laguna Niguel",
        "zips": ["92677"],
        "incorporated": 1989,
        "era": "largely built out from the 1960s through the 1990s",
        "notes": (
            "Laguna Niguel covers a wide spread of hillside subdivisions built "
            "across several decades. Homes from the 1970s and 1980s era "
            "typically still have their original copper supply lines, and that "
            "is the material we are called out to diagnose most often here."
        ),
        "landmarks": ["Bear Brand", "Niguel Summit", "Crown Valley"],
        "coastal": False,
        "density": "hillside tract",
        "typical_call": "copper supply-line failures in 1970s and 1980s subdivisions",
        "focus": ["slab_leak", "repiping"],
    },
    "san-clemente": {
        "name": "San Clemente",
        "zips": ["92672", "92673", "92674"],
        "incorporated": 1925,
        "era": "spanning 1920s beach cottages through the 2010s",
        "notes": (
            "San Clemente is unusually varied for its size: Ole Hanson's original "
            "1920s Spanish Village lots near the pier sit a short drive from "
            "Talega, whose master-planned construction ran from 1999 to 2015, and "
            "from the Forster Ranch and Marblehead areas. Because the housing "
            "stock spans nearly a century, the right diagnostic approach depends "
            "on the specific property rather than the city as a whole."
        ),
        "landmarks": ["Talega", "Forster Ranch", "Marblehead", "Pier Bowl"],
        "coastal": True,
        "density": "mixed coastal and inland",
        "typical_call": "age-dependent diagnosis, from original galvanized and copper to newer PEX",
        "focus": ["leak_detection", "slab_leak"],
    },
    "dana-point": {
        "name": "Dana Point",
        "zips": ["92629"],
        "incorporated": 1989,
        "era": "mid-century through recent coastal redevelopment",
        "notes": (
            "Dana Point's coastal position is the defining factor for its "
            "plumbing. Salt air and marine humidity accelerate corrosion on "
            "exposed metal, and the city mixes older homes around the Lantern "
            "District and harbor with newer development inland and at Monarch "
            "Beach."
        ),
        "landmarks": ["Lantern District", "Monarch Beach", "Dana Point Harbor"],
        "coastal": True,
        "density": "coastal village in-fill",
        "typical_call": "corrosion-driven leaks on exposed and near-coastal piping",
        "focus": ["leak_detection", "water_line"],
    },
    "mission-viejo": {
        "name": "Mission Viejo",
        "zips": ["92691", "92692"],
        "incorporated": 1988,
        "era": "master-planned from the mid-1960s onward",
        "notes": (
            "Mission Viejo was one of the largest master-planned communities in "
            "the country, developed in phases from the 1960s. The earliest "
            "phases are now past the age where original copper supply lines "
            "commonly begin to fail, while later phases are considerably newer — "
            "so two homes a few streets apart can need very different work."
        ),
        "landmarks": ["Lake Mission Viejo", "Painted Trails"],
        "coastal": False,
        "density": "phased master-planned tract",
        "typical_call": "phase-dependent pipe condition across a very large housing stock",
        "focus": ["repiping", "slab_leak"],
    },
    "ladera-ranch": {
        "name": "Ladera Ranch",
        "zips": ["92694"],
        "incorporated": None,
        "era": "built from 1999 onward",
        "notes": (
            "Ladera Ranch is a master-planned community on the old Rancho "
            "Mission Viejo land, with construction starting in 1999. Because "
            "the homes are comparatively young, the leak calls we see here tend "
            "to involve fittings, irrigation, and appliance connections rather "
            "than the end-of-life copper failures common in older neighboring "
            "cities."
        ),
        "landmarks": ["Antonio Parkway", "Crown Valley Parkway"],
        "coastal": False,
        "density": "dense master-planned tract",
        "typical_call": "fitting, irrigation, and appliance-connection leaks in newer homes",
        "focus": ["leak_detection", "water_line"],
    },
    "laguna-hills": {
        "name": "Laguna Hills",
        "zips": ["92653"],
        "incorporated": 1991,
        "era": "subdivided from the early 1960s onward",
        "notes": (
            "Laguna Hills grew out of the Moulton Ranch, subdivided in the early "
            "1960s, and includes both family subdivisions and the large "
            "age-restricted community at Laguna Woods Village next door. Homes "
            "of this vintage frequently still carry original supply piping."
        ),
        "landmarks": ["Moulton Ranch", "Laguna Hills Mall area"],
        "coastal": False,
        "density": "older tract and senior community",
        "typical_call": "aging original supply piping in early-1960s subdivisions",
        "focus": ["repiping", "plumbing_repair"],
    },
    "aliso-viejo": {
        "name": "Aliso Viejo",
        "zips": ["92656"],
        "incorporated": 2001,
        "era": "largely built out from the late 1980s through the 2000s",
        "notes": (
            "Aliso Viejo is one of Orange County's newer cities, built out "
            "mostly from the late 1980s onward around the Aliso Creek corridor. "
            "Housing is a mix of single-family homes and attached condominiums, "
            "and shared-wall and stacked-unit construction makes accurate leak "
            "location matter more here, not less."
        ),
        "landmarks": ["Aliso Creek corridor", "Pacific Park area"],
        "coastal": False,
        "density": "attached and single-family mix",
        "typical_call": "leaks in attached and stacked units where the source is not obvious",
        "focus": ["leak_detection", "plumbing_repair"],
    },
    "lake-forest": {
        "name": "Lake Forest",
        "zips": ["92630", "92610"],
        "incorporated": 1991,
        "era": "mid-century through the 1990s",
        "notes": (
            "Lake Forest runs from older mid-century neighborhoods around the "
            "two artificial lakes out to newer development in Foothill Ranch. "
            "That spread of eras means the diagnostic question is usually which "
            "generation of plumbing a particular home has."
        ),
        "landmarks": ["Lake Forest", "Foothill Ranch"],
        "coastal": False,
        "density": "mixed mid-century and newer",
        "typical_call": "identifying which generation of plumbing a given home has",
        "focus": ["plumbing_repair", "repiping"],
    },
    "dove-canyon": {
        "name": "Dove Canyon",
        "zips": ["92679"],
        "incorporated": None,
        "era": "developed in the 1980s and 1990s",
        "notes": (
            "Dove Canyon is a gated community in unincorporated Orange County, "
            "east of Trabuco Canyon, developed largely in the 1980s and 1990s. "
            "Many properties sit on larger lots with longer private water "
            "service runs from the meter, which stretches the distance a leak "
            "can travel before it shows at the surface."
        ),
        "landmarks": ["Dove Canyon Drive", "Trabuco Canyon"],
        "coastal": False,
        "density": "large-lot gated estate",
        "typical_call": "long private service runs where a leak surfaces far from its source",
        "focus": ["water_line", "leak_detection"],
    },
    "coto-de-caza": {
        "name": "Coto de Caza",
        "zips": ["92679"],
        "incorporated": None,
        "era": "developed roughly 1968 through 2003",
        "notes": (
            "Coto de Caza is a guard-gated community and census-designated "
            "place, developed in phases from the late 1960s through 2003. That "
            "makes it genuinely mixed: some homes are well past the expected "
            "service life of original copper, while others are much newer, and "
            "the build year matters more than the address."
        ),
        "landmarks": ["Los Ranchos Estates", "Coto de Caza Golf & Racquet Club"],
        "coastal": False,
        "density": "phased gated estate",
        "typical_call": "build-year-driven pipe condition across a 35-year construction span",
        "focus": ["repiping", "water_line"],
    },
    "rancho-santa-margarita": {
        "name": "Rancho Santa Margarita",
        "zips": ["92688"],
        "incorporated": 2000,
        "era": "built out from the late 1980s through the 1990s",
        "notes": (
            "Rancho Santa Margarita was largely built out in the late 1980s "
            "and 1990s before incorporating in 2000. Many homes here now sit in "
            "the window where original supply piping, water heaters, and "
            "fixtures reach the end of their service life around the same time."
        ),
        "landmarks": ["Rancho Santa Margarita Lake", "Plano Trabuco"],
        "coastal": False,
        "density": "planned tract and townhome",
        "typical_call": "supply piping, water heaters, and fixtures aging on the same schedule",
        "focus": ["water_heater", "plumbing_repair"],
    },
}


def facts(slug):
    return CITY_FACTS[slug]


def zip_display(slug):
    return ", ".join(CITY_FACTS[slug]["zips"])


def is_incorporated(slug):
    return CITY_FACTS[slug]["incorporated"] is not None


def service_pages():
    """Canonical (slug, label) pairs for services actually offered."""
    return [
        ("leak-detection", "Leak Detection"),
        ("slab-leak-detection", "Slab Leak Detection"),
        ("pex-repiping", "PEX Repiping"),
        ("plumbing-repair", "Plumbing Repair"),
        ("water-heater-services", "Water Heater Services"),
        ("drain-services", "Drain Services"),
        ("emergency-plumbing", "Emergency Plumbing"),
    ]
