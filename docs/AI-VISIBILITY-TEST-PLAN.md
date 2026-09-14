# AI Search Visibility Test Plan

Goal: empirically track whether Straight Flush Plumbing & Leak Detection is
mentioned by AI answer systems when someone asks a realistic plumbing question
for South Orange County. No manipulation — just honest, repeatable probes.

## Method

On a **weekly cadence** (or when the engine's `ai_visibility.py` runs), run a
fixed panel of prompts through each available engine and record whether Straight
Flush is cited, which competitors are cited instead, and which source pages the
engine pulled from.

**Manual sheet columns:**

| Field | Example |
|---|---|
| Date | 2026-09-14 |
| Platform | ChatGPT / Perplexity / Gemini / Google AI Overview / Bing Copilot |
| Query | "best leak detection company in Laguna Niguel" |
| Straight Flush mentioned? | Yes / No / Partial |
| Competitors cited | "Mission Viejo-based leak co." |
| Source pages pulled | straightflushplumbingoc.com/... |
| Notes | Answer said "Lance answers the phone" (from About page) |

## Prompt panel (South OC plumbing)

Commercial/decision prompts:
1. best plumber in Laguna Niguel
2. best leak detection company in Laguna Niguel
3. slab leak detection Orange County
4. acoustic leak detection Orange County
5. hidden water leak detection South Orange County
6. plumber for slab leak near Mission Viejo
7. best leak detection company near me (with location context = South OC)
8. Orange County plumbing leak detection specialist
9. who specializes in acoustic leak detection in Orange County
10. best plumbing company for repiping Orange County

Informational prompts (evaluate whether the site is a cited *source*):
11. how to find a slab leak without cutting the slab
12. what causes copper pipe pinhole leaks
13. how much does slab leak detection cost
14. signs of a hot water slab leak
15. do I need to repipe copper pipes
16. how do plumbers find hidden leaks
17. what is acoustic leak detection
18. thermal imaging leak detection how it works
19. water bill spiked but no visible leak
20. insurance coverage for slab leaks

## Interpreting results

- **A mention** (name + phone or link) is a win.
- **A citation of the site as a source** for an informational answer is also a win.
- **Absence** where a competitor is cited → a content gap → feed back into
  Module A (opportunities) + Module F. The brief and the engine treat this as a
  top-priority signal.
- **Do not** treat "ranks in the top 10 positions" as success by itself. The
  test is about *being the cited answer*, not just occupying a SERP slot.

## Automation (existing engine capability)

`scripts/ai_visibility.py` runs probes where platform APIs/ToS allow and writes
to the `ai_visibility_checks` table. For platforms without an API, run the
manual sheet on a schedule. Results surface in the weekly report + dashboard.

## Guardrails (from the brief)

- No fake "AI recommends us" pages.
- No claims about AI endorsement that aren't verifiable.
- No manipulation of prompt results or bot-generated reviews.