# Straight Flush — Entity Model (stable @id graph)

Source of truth for the canonical business entity and the `@id` values every
page and schema block must reference. Nothing here is invented.

## The problem this fixes

Before this change, **no page on the site carried an `@id`**. All 74 pages
re-declared a disconnected `Plumber` node with slightly different fields, and
`Service.provider` was an inline `{"@type": "Plumber", "name": ...}` object.
To a search engine or AI system this reads as many unrelated businesses that
happen to share a name, not one entity.

## Canonical identifiers

| Entity | `@id` | `@type` | Notes |
|---|---|---|---|
| Business | `https://straightflushplumbingoc.com/#business` | `Plumber` | **Primary node.** Plumber is the most specific applicable `LocalBusiness` subtype. Carries full NAP, hours, `areaServed`, `sameAs`, `makesOffer`, `knowsAbout`. |
| Website | `https://straightflushplumbingoc.com/#website` | `WebSite` | `publisher` → `#business` |

`Plumber` is a subtype of `LocalBusiness`, which is a subtype of `Organization`.
A single `Plumber` node therefore **is** the organization — a separate
`Organization` node would duplicate the same real-world thing, which the
brief explicitly warns against. The former `#organization` and `#plumber` ids
are retired in favour of the single `#business` id.

## Referencing rule

The business entity is declared **once per page** (each HTML document is its
own graph) on `#business`, and every other block points at it by reference:

```
Service.provider              -> {"@id": "...#business"}
WebSite.publisher             -> {"@id": "...#business"}
Article.author / .publisher   -> {"@id": "...#business"}
```

Do **not** inline a second `{"@type": "Plumber", "name": ...}` object.

## What is deliberately NOT here

- **No per-city LocalBusiness nodes.** Straight Flush has one real location
  (Laguna Niguel). Cities are `areaServed` / `City` values only — never fake
  office entities.
- **No review or rating markup** unless it comes from a real, verifiable
  platform review (see `review_miner.py` and the F3 flywheel).
- **No licensing/credential fields** until verified — see
  `BUSINESS-ENTITY-CANONICAL.md` `[VERIFY]` items.

## Enforcement

`modules/objects/schema_jsonld.py` builds every node from these constants.
`tests/test_entity_graph.py` asserts that no page emits a bare, `@id`-less
`Plumber` node and that all references resolve to `#business`.