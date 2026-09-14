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


def plumber_min(city_label):
    return {
        "@context": "https://schema.org",
        "@type": "Plumber",
        "name": S.BRAND,
        "telephone": S.PHONE_TEL,
        "areaServed": f"{city_label}, CA",
    }


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
        "provider": {"@type": "Plumber", "name": S.BRAND},
        "areaServed": {"@type": "City", "name": f"{city_label}, CA"},
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Services",
            "itemListElement": offers,
        },
    }


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
        "author": {"@type": "Organization", "name": S.BRAND},
        "publisher": {
            "@type": "Organization",
            "name": S.BRAND,
            "logo": {"@type": "ImageObject", "url": f"{S.DOMAIN}/assets/img/logo.jpg"},
        },
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
    return {
        "@context": "https://schema.org",
        "@type": "Plumber",
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
# AI-Authority entity builders (Sections 2-4 of the brief).
# These emit a *single* rich entity per page. They are used by the master
# authority page generator and can be reused by other generators. They never
# invent data: sameAs only includes SAMEAS_VERIFIED, hours come from
# OPENING_HOURS, founding year from FOUNDING_YEAR.
# ---------------------------------------------------------------------------


def organization():
    """Organization block for the master authority page."""
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{S.DOMAIN}/#organization",
        "name": S.BRAND,
        "url": f"{S.DOMAIN}/",
        "logo": {"@type": "ImageObject", "url": f"{S.DOMAIN}/assets/img/logo.jpg"},
        "image": f"{S.DOMAIN}/assets/img/logo.jpg",
        "sameAs": list(S.SAMEAS_VERIFIED),
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": S.PHONE_TEL,
            "contactType": "customer service",
            "areaServed": "US",
            "availableLanguage": "en",
        },
    }


def local_business():
    """LocalBusiness (Plumber subtype) entity with verified NAP only."""
    return {
        "@context": "https://schema.org",
        "@type": "Plumber",
        "@id": f"{S.DOMAIN}/#plumber",
        "name": S.BRAND,
        "image": f"{S.DOMAIN}/assets/img/logo.jpg",
        "url": f"{S.DOMAIN}/",
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
        "openingHoursSpecification": S.OPENING_HOURS,
        "sameAs": list(S.SAMEAS_VERIFIED),
        "makesOffer": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n}}
            for n in S.SERVICE_LABEL.values()
        ],
        "knowsAbout": list(S.KNOWS_ABOUT),
    }


def website(site_url=None):
    """WebSite entity marking the site's SearchAction (sitemap/robots context)."""
    url = site_url or f"{S.DOMAIN}/"
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": f"{S.DOMAIN}/#website",
        "url": url,
        "name": S.BRAND,
        "publisher": {"@id": f"{S.DOMAIN}/#organization"},
    }


def master_authority_schema():
    """All schema blocks for the /about/straight-flush-plumbing-orange-county/ page.

    Combines Organization + LocalBusiness(Plumber) + WebSite + BreadcrumbList.
    Review/AggregateRating blocks are intentionally NOT included here — the
    brief forbids fabricating or marking up reviews that don't comply with
    search-engine requirements. Verified reviews can be added later via the
    review flywheel (F3) once they're documented on a compliant platform.
    """
    return [
        organization(),
        local_business(),
        website(),
        breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "About", f"{S.DOMAIN}/about"),
            (3, "Straight Flush Plumbing & Leak Detection in Orange County",
             f"{S.DOMAIN}/about/straight-flush-plumbing-orange-county"),
        ]),
    ]