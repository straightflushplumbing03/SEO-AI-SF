#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
City page builder — the reusable COMPONENT architecture (not copied text).

Every city page renders the same section skeleton from city_data facts, so the
structure is consistent, while the prose comes from each city's own verified
data. This is deliberately built so that adding a city means adding a fact
entry, not writing a new page by hand.

Section order (brief Phase 3):
  1. Hero + breadcrumb
  2. Local plumbing context
  3. Leak detection
  4. Slab leak detection
  5. Water-line detection & repair
  6. Whole-house repiping
  7. Plumbing services (links)
  8. Why homeowners call Straight Flush
  9. Nearby communities
 10. FAQs
 11. CTA

Copy rules enforced here:
  - No "best plumber in X" claims.
  - No invented projects, reviews, response times, prices, or credentials.
  - Local facts come from city_data, which records provenance.
"""
from . import page as P
from . import city_data as C
from . import site_data as S
from . import schema_jsonld as J

PREFIX = "../"


def _section(eyebrow, heading, inner, cls="section"):
    return f"""<section class="{cls}">
  <div class="wrap">
    <div class="section-head reveal" style="margin-bottom:22px;">
      <div class="eyebrow">{P.esc(eyebrow)}</div>
      <h2>{P.esc(heading)}</h2>
    </div>
    <div class="reveal">{inner}</div>
  </div>
</section>"""


def _svc(slug, label):
    return f'<a href="{PREFIX}services/{slug}.html">{P.esc(label)}</a>'


def _context(prefix, slug):
    f = C.facts(slug)
    name = f["name"]
    zips = C.zip_display(slug)
    if C.is_incorporated(slug):
        inc = f"Incorporated in {f['incorporated']}"
    else:
        inc = "An unincorporated Orange County community"
    return (
        f"<p class=\"muted\">{P.esc(f['notes'])}</p>"
        f"<p class=\"muted\">Housing here is {P.esc(f['era'])}. "
        f"{P.esc(inc)}, with ZIP code{'s' if ',' in zips else ''} {P.esc(zips)}. "
        f"Straight Flush provides residential plumbing and leak-detection "
        f"services to homeowners in {P.esc(name)} and the surrounding "
        f"South Orange County communities.</p>"
    )


def _leak_detection(prefix, slug):
    f = C.facts(slug)
    name = f["name"]
    if f["coastal"]:
        why = (f"Coastal exposure matters on the detection side too. Salt air "
               f"corrodes exposed metal fittings, shutoffs, and outdoor "
               f"connections faster than inland air does, so a leak in "
               f"{P.esc(name)} is as likely to originate at a fitting or an "
               f"exterior run as it is in a buried line.")
    else:
        why = (f"Because the homes here are {P.esc(f['era'])}, the likely "
               f"location of a leak narrows considerably once the build year is "
               f"known. That is the first question worth answering, and it costs "
               f"nothing to ask.")
    return (
        f"<p class=\"muted\">Most hidden leaks announce themselves indirectly: a "
        f"water bill that climbs without a change in habit, a meter that keeps "
        f"turning with every fixture off, or the sound of moving water when "
        f"nothing is running. Straight Flush provides leak detection in "
        f"{P.esc(name)} using acoustic listening equipment, thermal imaging, and "
        f"pressure testing to narrow down where the water is actually escaping "
        f"before anyone opens a wall or breaks concrete.</p>"
        f"<p class=\"muted\">{why}</p>"
        f"<p class=\"muted\">The purpose of detection is to answer one question "
        f"accurately: where is it leaking? A confirmed location is what lets a "
        f"homeowner in a {P.esc(f['density'])} setting choose between a targeted "
        f"repair, a reroute, or a larger repiping project with real information "
        f"rather than a guess.</p>"
        f"<p class=\"muted\">Learn more about "
        f"{_svc('leak-detection', 'how leak detection works')}.</p>"
    )


def _slab_leak(prefix, slug):
    f = C.facts(slug)
    name = f["name"]
    if "slab_leak" in f["focus"]:
        relevance = (f"Slab leaks come up often enough in {P.esc(name)} that "
                     f"they are worth understanding before you need the "
                     f"information. The plumbing here is {P.esc(f['era'])}, and "
                     f"the most common call we take is "
                     f"{P.esc(f['typical_call'])}.")
    else:
        relevance = (f"Slab leaks are not the most common problem in "
                     f"{P.esc(name)}, and it is worth saying so plainly. The "
                     f"housing here is {P.esc(f['era'])}, and the calls we "
                     f"actually take most often involve "
                     f"{P.esc(f['typical_call'])}. A slab leak is still "
                     f"possible, but the odds should shape what gets tested "
                     f"first.")
    return (
        f"<p class=\"muted\">A slab leak is a failure in a water line that runs "
        f"through or beneath a home's concrete foundation. Warm spots on the "
        f"floor, the sound of running water with everything shut off, a spike in "
        f"the water or gas bill, or unexplained moisture at the base of a wall "
        f"are the reasons homeowners call us to investigate. Not every one of "
        f"those symptoms turns out to be a slab leak, and that is precisely why "
        f"the diagnostic step matters.</p>"
        f"<p class=\"muted\">{relevance}</p>"
        f"<p class=\"muted\">Detection means confirming the location first: "
        f"acoustic equipment to listen for the signature of pressurized water "
        f"escaping, thermal imaging to look for the temperature difference a "
        f"hot-water line creates, and pressure testing to establish which line is "
        f"losing water. Only once the leak is located does it make sense to "
        f"discuss the repair itself. See "
        f"{_svc('slab-leak-detection', 'slab leak detection')} for the process.</p>"
    )


def _water_line(prefix, slug):
    f = C.facts(slug)
    name = f["name"]
    if "water_line" in f["focus"]:
        emph = (f"This is one of the more frequent calls we get in "
                f"{P.esc(name)}. The {P.esc(f['density'])} pattern here means "
                f"water can travel a long way from the failure before it shows, "
                f"so tracing it rather than digging at the first wet patch saves "
                f"real money.")
    else:
        emph = (f"In {P.esc(name)} the supply side is worth ruling out early, "
                f"because a pressurized line loses water continuously and "
                f"quietly. That distinguishes it from a drain problem, which "
                f"usually only shows when something is running.")
    return (
        f"<p class=\"muted\">Water service lines and pressurized supply lines "
        f"carry water under constant pressure, so a failure can lose a "
        f"significant volume of water before it ever reaches the surface. "
        f"Underground service lines between the meter and the house are a "
        f"common source, particularly where soil movement or age has stressed "
        f"the pipe.</p>"
        f"<p class=\"muted\">{emph}</p>"
        f"<p class=\"muted\">The useful first step is establishing whether the "
        f"loss is on the pressurized supply side or the drainage side, and "
        f"whether it is inside the structure or outside it. Straight Flush "
        f"diagnoses pressurized water line leaks, including underground lines, "
        f"before recommending repair or rerouting. Related: "
        f"{_svc('plumbing-repair', 'plumbing repair')} and "
        f"{_svc('emergency-plumbing', 'emergency plumbing')}.</p>"
    )


def _repiping(prefix, slug):
    f = C.facts(slug)
    name = f["name"]
    if "repiping" in f["focus"]:
        emph = (f"With housing {P.esc(f['era'])}, a meaningful share of "
                f"{P.esc(name)} homes are now in the window where original "
                f"supply piping reaches the end of its service life. That does "
                f"not mean every one of them needs repiping &mdash; it means the "
                f"question deserves a straight answer rather than a default.")
    elif "water_heater" in f["focus"] or "plumbing_repair" in f["focus"]:
        emph = (f"In {P.esc(name)}, repiping is usually the second question "
                f"rather than the first. Most systems here are not yet at that "
                f"point, and the more common work is "
                f"{P.esc(f['typical_call'])}.")
    else:
        emph = (f"Most homes in {P.esc(name)} are not there yet, because the "
                f"housing is {P.esc(f['era'])}. When repiping does come up here, "
                f"it is usually driven by a pattern of failures rather than "
                f"age on its own.")
    return (
        f"<p class=\"muted\">When a home has had several leaks in a relatively "
        f"short period, the question shifts from &ldquo;how do we fix this "
        f"one?&rdquo; to &ldquo;how much of this piping is near the end of its "
        f"service life?&rdquo; Repeated pinhole failures on aging copper are the "
        f"most common reason homeowners start evaluating whole-house repiping "
        f"rather than continuing to repair one section at a time.</p>"
        f"<p class=\"muted\">{emph}</p>"
        f"<p class=\"muted\">Repiping is not automatically the right answer, and "
        f"it is not a decision to make under pressure. Straight Flush walks "
        f"{P.esc(name)} homeowners through the honest options &mdash; a "
        f"targeted repair, a reroute around the failing section, or full "
        f"repiping in PEX &mdash; with the trade-offs of each, so the choice "
        f"matches the actual condition of the plumbing. See "
        f"{_svc('pex-repiping', 'whole-house PEX repiping')}.</p>"
    )


def _where(prefix, slug):
    """Landmark/neighborhood section. Public geographic reference only —
    no claim of an office or presence in these areas."""
    f = C.facts(slug)
    name = f["name"]
    lm = f["landmarks"]
    listed = ", ".join(lm[:-1]) + f" and {lm[-1]}" if len(lm) > 1 else lm[0]
    return (
        f"<p class=\"muted\">Straight Flush works throughout {P.esc(name)}, "
        f"including the areas around {P.esc(listed)}. These are places we "
        f"travel to for service calls &mdash; they are neighborhoods and "
        f"landmarks within the city, not office locations.</p>"
        f"<p class=\"muted\">Because the housing within {P.esc(name)} is "
        f"{P.esc(f['era'])}, the plumbing in one part of the city can be a "
        f"generation different from another. If you tell us roughly when your "
        f"home was built, that alone narrows down what is most likely to be "
        f"worth testing first.</p>"
    )


def _services(prefix, slug):
    name = C.facts(slug)["name"]
    items = "\n".join(
        f'      <li><span class="tick">{P.TICK_ICON}</span> '
        f'{_svc(s, l)}</li>'
        for s, l in C.service_pages()
    )
    return f"""<ul class="founder-list">
{items}
    </ul>
    <p class="muted" style="margin-top:14px;">All services above are available to
    homeowners in {P.esc(name)} and nearby communities.</p>"""


def _why(prefix, slug):
    items = [
        f"Owner-operated and based in Laguna Niguel &mdash; you speak with the person doing the work.",
        "Diagnose-first: the leak is located before a repair is recommended.",
        "Acoustic, thermal, and pressure-testing equipment, not guesswork demolition.",
        "Plain-language explanations and honest options, including when a smaller fix is the right call.",
    ]
    return f"""<ul class="founder-list">
{P.tick_list(items)}
    </ul>"""


# Question bank. Each entry is tagged with the focus areas it serves, so a
# city draws a weighted subset rather than all cities sharing one identical set.
_FAQ_BANK = {
    "serve": {
        "tags": [],
        "q": "Does Straight Flush serve {city}?",
        "a": ("Yes. Straight Flush Plumbing & Leak Detection provides residential "
              "plumbing and leak-detection services to homeowners in {city} and "
              "the surrounding South Orange County area."),
    },
    "hidden": {
        "tags": ["leak_detection", "water_line"],
        "q": "How do I know if I have a hidden water leak?",
        "a": ("Common signs are a water bill that rises without a change in usage, "
              "a water meter that keeps moving after every fixture is shut off, the "
              "sound of running water when nothing is on, or unexplained damp or "
              "warm spots on the floor. Any of these is a good reason to have the "
              "system tested."),
    },
    "slabsigns": {
        "tags": ["slab_leak"],
        "q": "What are the signs of a slab leak?",
        "a": ("A warm spot on the floor over a hot-water line, the sound of water "
              "running with everything off, an unexplained increase in the water or "
              "gas bill, or moisture and cracking at the base of a wall. These "
              "symptoms have several possible causes, so confirmation requires "
              "testing rather than assumption."),
    },
    "noopen": {
        "tags": ["leak_detection"],
        "q": "Can a leak be detected without opening the wall or breaking the slab?",
        "a": ("In most cases the location can be narrowed down first. Acoustic "
              "listening, thermal imaging, and pressure testing are all "
              "non-destructive, and they are used to identify where the leak is "
              "before any access work is discussed."),
    },
    "acoustic": {
        "tags": ["leak_detection", "slab_leak"],
        "q": "What is acoustic leak detection?",
        "a": ("It uses specialized listening equipment to pick up the sound "
              "pressurized water makes as it escapes a pipe. It is particularly "
              "useful for locating leaks under a concrete slab, where there is "
              "nothing visible to inspect."),
    },
    "repiping": {
        "tags": ["repiping"],
        "q": "When should a homeowner consider repiping?",
        "a": ("Repiping is worth evaluating when a home has had repeated leaks in a "
              "short period, which usually points to piping that is broadly near "
              "the end of its service life rather than one isolated failure. The "
              "condition of the pipe, not age alone, should drive the decision."),
    },
    "reroute": {
        "tags": ["water_line", "repiping"],
        "q": "What is the difference between repairing a leak and rerouting a line?",
        "a": ("A repair fixes the failed section of pipe in place. A reroute "
              "abandons the failing section and runs a new line by a different "
              "path, which is often preferable when the original line is buried in "
              "a slab or otherwise difficult to reach."),
    },
    "whatdo": {
        "tags": [],
        "q": "What should I do if I suspect a water leak?",
        "a": ("Shut off fixtures and appliances that use water and check whether "
              "the meter still moves. If it does, water is escaping somewhere in "
              "the system. Then call a leak-detection specialist rather than "
              "opening walls or flooring on a guess. For an active or worsening "
              "leak, call (949) 374-6524."),
    },
    "meter": {
        "tags": ["water_line", "leak_detection"],
        "q": "The meter still turns with everything off. What does that mean?",
        "a": ("It means water is moving through the meter with no fixture calling "
              "for it, which points to a leak on a pressurized line rather than a "
              "drain. The next step is isolating whether the loss is inside the "
              "house or on the service line between the meter and the structure."),
    },
    "hotwater": {
        "tags": ["slab_leak", "repiping"],
        "q": "How can you tell a hot-water leak from a cold-water one?",
        "a": ("A hot-water line leak usually warms the floor or wall above it and "
              "can raise the gas or electric bill, while a cold-water leak shows "
              "as dampness or a higher water bill. Thermal imaging makes the "
              "difference visible, and pressure testing confirms which line is "
              "losing water."),
    },
    "heaterlife": {
        "tags": ["water_heater"],
        "q": "How long should a water heater last in South Orange County?",
        "a": ("Tank water heaters commonly last around a decade and tankless units "
              "longer, though actual service life depends heavily on water "
              "chemistry and maintenance. A tank that is rusting at the base, "
              "rumbling, or leaving rusty water is usually near the end of its "
              "life."),
    },
    "diy": {
        "tags": ["plumbing_repair"],
        "q": "Is there anything a homeowner should check before calling?",
        "a": ("Checking the water meter with everything shut off, noting whether "
              "the floor is warm in a particular spot, and writing down when the "
              "water bill changed all give a technician a faster starting point. "
              "None of it replaces proper testing."),
    },
    "insurance": {
        "tags": ["slab_leak", "water_line"],
        "q": "Will homeowners insurance cover leak detection or repair?",
        "a": ("Coverage varies by policy and by whether the damage is considered "
              "sudden and accidental. Straight Flush documents what was found and "
              "how, which is useful when you talk to your insurer. Coverage "
              "decisions are your insurer's to make."),
    },
    "cost": {
        "tags": ["plumbing_repair", "water_heater"],
        "q": "What determines the cost of a plumbing repair here?",
        "a": ("Access is usually the biggest variable. A repair at a reachable "
              "fitting and one buried under a slab involve very different work, "
              "which is why locating the problem accurately before quoting matters "
              "so much."),
    },
    "gate": {
        "tags": ["water_line", "leak_detection"],
        "q": "Does a gated community change how leak detection is scheduled?",
        "a": ("It can affect access timing rather than the work itself. Let us "
              "know the gate procedure when you book so the technician is not "
              "delayed at the entrance."),
    },
}


def _select_faqs(slug):
    """Serve + a focus-weighted subset, so no two cities share an identical set."""
    f = C.facts(slug)
    focus = list(f["focus"])
    name = f["name"]

    chosen = ["serve"]
    # Focus-tagged questions first, up to 3, preserving bank order.
    for key, item in _FAQ_BANK.items():
        if key == "serve":
            continue
        if len(chosen) >= 4:
            break
        if any(t in focus for t in item["tags"]):
            chosen.append(key)
    # Fill to 6 with general questions in a stable order.
    for key in ("hidden", "acoustic", "whatdo", "noopen", "reroute", "slabsigns"):
        if len(chosen) >= 6:
            break
        if key not in chosen:
            chosen.append(key)

    out = []
    for key in chosen:
        item = _FAQ_BANK[key]
        out.append((item["q"].format(city=name),
                    item["a"].format(city=P.esc(name))))
    return out


def _faqs(slug):
    return _select_faqs(slug)


def _schema(slug):
    f = C.facts(slug)
    name = f["name"]
    return [
        J.business(),
        J.service_with_catalog(name),
        J.faq(_faqs(slug)),
        J.breadcrumbs([
            (1, "Home", f"{S.DOMAIN}/"),
            (2, "Service Areas", f"{S.DOMAIN}/service-areas"),
            (3, name, f"{S.DOMAIN}/cities/{slug}"),
        ]),
    ]


def build_city_page(slug, projects=(), reviews=()):
    """Build one city page. projects/reviews are real records or empty."""
    f = C.facts(slug)
    name = f["name"]
    title = f"{name} Plumber & Leak Detection | Straight Flush Plumbing"
    description = (
        f"Straight Flush Plumbing & Leak Detection provides residential plumbing, "
        f"acoustic leak detection, slab leak detection, and PEX repiping to "
        f"homeowners in {name}, CA. Call (949) 374-6524."
    )
    h1 = f"Plumber & Leak Detection in {name}, CA"

    html = P.head(title, description, f"cities/{slug}", PREFIX, _schema(slug))
    html += P.nav(PREFIX)
    html += P.page_hero(
        PREFIX,
        eyebrow=f"Serving {name}",
        h1=h1,
        sub=(f"Straight Flush Plumbing & Leak Detection provides residential "
             f"plumbing and leak-detection services to homeowners in {P.esc(name)}."),
        cta_label=f"Schedule Service in {name}",
        trail=[("Home", "index.html"), ("Service Areas", "service-areas.html"),
               (name, None)],
    )

    body = []
    body.append(_section("Local context", f"What we see in {name} homes",
                         _context(PREFIX, slug)))
    body.append(_section("Leak detection", f"Leak Detection in {name}",
                         _leak_detection(PREFIX, slug), "section-sand"))
    body.append(_section("Slab leaks", f"Slab Leak Detection in {name}",
                         _slab_leak(PREFIX, slug)))
    body.append(_section("Water lines", "Water Line Leak Detection & Repair",
                         _water_line(PREFIX, slug), "section-sand"))
    body.append(_section("Repiping", f"Whole-House Repiping in {name}",
                         _repiping(PREFIX, slug)))
    body.append(_section("Services", f"Plumbing Services in {name}",
                         _services(PREFIX, slug), "section-sand"))
    body.append(_section("Where we work", f"Where We Work in {name}",
                         _where(PREFIX, slug)))
    body.append(_section("Why us", "Why Homeowners Call Straight Flush",
                         _why(PREFIX, slug), "section-sand"))
    body.append(P.neighbor_chips(PREFIX, slug))
    body.append(P.faq_section(PREFIX, "Common questions",
                              f"{name} plumbing & leak detection FAQs",
                              _faqs(slug)))
    body.append(P.cta_band(
        PREFIX,
        f"Ready to schedule service in {name}?",
        f"Diagnose-first leak detection and plumbing for {P.esc(name)} homeowners.",
        cta_label=f"Call {S.PHONE_DISPLAY}",
        cta_href="contact.html",
    ))

    html += "\n".join(body) + "\n"
    html += P.footer(PREFIX)

    return {
        "slug": slug,
        "path": f"cities/{slug}.html",
        "html": html,
        "canonical_path": f"cities/{slug}",
        "title": title,
        "description": description,
    }