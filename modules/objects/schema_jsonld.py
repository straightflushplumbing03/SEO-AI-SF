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