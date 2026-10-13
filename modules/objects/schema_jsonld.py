#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON-LD schema builders — clone the exact structures already on the live site.
Patterns verified on disk:
- City page:    Plumber (minimal) + BreadcrumbList + Service(OfferCatalog)
- Service page: Service + BreadcrumbList + FAQPage
- Academy page: FAQPage + BreadcrumbList + Article (author/publisher/logo)
- Home:         Plumber (rich) + FAQPage + WebSite + AggregateRating + Review[]
"""
from . import site_data as S


def business_ref():
    """Reference to the canonical business node (for provider/publisher/author).

    Use this instead of inlining a second {"@type": "Plumber", "name": ...}.
    See docs/ENTITY-MODEL.md.
    """
    return {"@id": S.BUSINESS_ID}


def plumber_min(city_label=None):
    """Deprecated shim — returns the canonical business node.

    Previously emitted a bare, @id-less Plumber node with a varying areaServed,
    which read as a separate business on every page. Kept as a thin alias so
    existing callers keep working; prefer business() or business_ref().
    """
    return business()


def breadcrumbs(crumbs):
    """crumbs: list of (position, name, url). url None => @id points to itself."""
    item_list = []
    for pos, name, url in crumbs:
        item_list.append({
            "@type": "ListItem",
            "position": pos,
            "name": name,
        })
        if url:
            item_list[-1]["item"] = url
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list,
    }


def service_with_catalog(city_label, denormalized_services=None, service_type="Plumbing & Leak Detection"):
    offers = [
        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n}}
        for n in (denormalized_services or S.OFFERED_SERVICES)
    ]
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": service_type,
        "provider": business_ref(),
        "areaServed": {"@type": "City", "name": f"{city_label}, CA"},
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Services",
            "itemListElement": offers,
        },
    }


def service(service_type, description=None, area_served="Orange County, CA"):
    """Canonical Service node referencing the business by @id."""
    node = {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": service_type,
        "provider": business_ref(),
        "areaServed": {"@type": "AdministrativeArea", "name": area_served},
    }
    if description:
        node["description"] = description
    return node


def faq(questions):
    """questions: list of (question, answer_markup). answer text kept plain+escaped."""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in questions
        ],
    }


def article(headline, date, canonical_url):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "datePublished": date,
        "dateModified": date,
        "author": business_ref(),
        "publisher": business_ref(),
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
    }


def review_schema(author, rating, date_published, body):
    return {
        "@type": "Review",
        "author": {"@type": "Person", "name": author},
        "reviewRating": {"@type": "Rating", "ratingValue": rating},
        "datePublished": date_published,
        "reviewBody": body,
    }


def local_business_review_block(reviews):
    """Review block referencing the canonical business node.

    Review bodies must come from real, verifiable platform reviews.
    """
    return {
        "@context": "https://schema.org",
        "@type": "Plumber",
        "@id": S.BUSINESS_ID,
        "name": S.BRAND,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "5.0",
            "reviewCount": str(len(reviews)),
            "bestRating": "5",
        },
        "review": reviews,
    }


# ---------------------------------------------------------------------------
# Canonical business entity (docs/ENTITY-MODEL.md).
#
# ONE node per page. `Plumber` is the most specific applicable LocalBusiness
# subtype, and LocalBusiness is itself an Organization subtype — so this single
# node is the organization too. A separate Organization node would duplicate
# the same real-world thing. It never invents data: sameAs only includes
# SAMEAS_VERIFIED, hours come from OPENING_HOURS, founding year from
# FOUNDING_YEAR.
# ---------------------------------------------------------------------------


def business(include_hours=True, include_offers=True):
    """The canonical business entity, declared once per page on #business."""
    node = {
        "@context": "https://schema.org",
        "@type": "Plumber",
        "@id": S.BUSINESS_ID,
        "name": S.BRAND,
        "slogan": S.SLOGAN,
        "url": f"{S.DOMAIN}/",
        "logo": {"@type": "ImageObject", "url": f"{S.DOMAIN}/assets/img/logo.jpg"},
        "image": f"{S.DOMAIN}/assets/img/logo.jpg",
        "telephone": S.PHONE_TEL,
        "email": S.EMAIL,
        "priceRange": "$$",
        "foundingDate": S.FOUNDING_YEAR,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "78 Cameray Heights",
            "addressLocality": "Laguna Niguel",
            "addressRegion": "CA",
            "postalCode": "92677",
            "addressCountry": "US",
        },
        "areaServed": [{"@type": "City", "name": c + ", CA"} for c in S.AREA_SERVED],
        "sameAs": list(S.SAMEAS_VERIFIED),
    }
    if include_hours:
        node["openingHoursSpecification"] = S.OPENING_HOURS
    if include_offers:
        node["makesOffer"] = [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n}}
            for n in S.SERVICE_LABEL.values()
        ]
        node["knowsAbout"] = list(S.KNOWS_ABOUT)
    return node


def organization():
    """Deprecated alias for business().

    Retained so existing callers/tests keep working. The separate
    `#organization` node was retired: `Plumber` already IS an Organization
    subtype, so a second node duplicated the same entity.
    """
    return business()


def local_business():
    """Deprecated alias for business(). See organization()."""
    return business()


def local_business_page(city_label):
    """Business node scoped to a city page: same @id, city narrowed to areaServed.

    Deliberately keeps the ONE canonical @id and does NOT create a per-city
    business entity — Straight Flush has a single real location.
    """
    node = business(include_hours=False, include_offers=False)
    node["areaServed"] = {"@type": "City", "name": f"{city_label}, CA"}
    return node


def website(site_url=None):
    """WebSite entity marking the site's SearchAction (sitemap/robots context)."""
    url = site_url or f"{S.DOMAIN}/"
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": S.WEBSITE_ID,
        "url": url,
        "name": S.BRAND,
        "publisher": business_ref(),
    }


def master_authority_schema():
    """All schema blocks for the /about/straight-flush-plumbing-orange-county/ page.

    Business(Plumber) + WebSite + BreadcrumbList. Review/AggregateRating blocks
    are intentionally NOT included here — the brief forbids fabricating or
    marking up reviews that don't comply with search-engine requirements.
    Verified reviews can be added later via the review flywheel (F3) once
    they're documented on a compliant platform.
    """
    return [
        business(),
        website(),
        breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "About", f"{S.DOMAIN}/about"),
            (3, "Straight Flush Plumbing & Leak Detection in Orange County",
             f"{S.DOMAIN}/about/straight-flush-plumbing-orange-county"),
        ]),
    ]