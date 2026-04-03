"""Source registry tool — returns crawl sources by tier."""
import logging

from strands import tool

logger = logging.getLogger(__name__)

SOURCES = {
    1: {
        "label": "Agger Local (highest priority)",
        "sources": [
            {"name": "7770thy.dk", "url": "https://7770thy.dk/", "type": "Community directory, events", "notes": "Landsbyklyngen. /find-alle/ for directory."},
            {"name": "Agger Bio", "url": "https://www.aggerbio.dk/", "type": "Cinema", "notes": "/upcomming_movies/ for schedule."},
            {"name": "Agger Booking events", "url": "https://aggerbooking.dk/oplevelser/det-sker/", "type": "Events", "notes": "Heavy Agger, Lady Walk, Cold Hawaii Ultra."},
            {"name": "Agger Darling", "url": "https://www.aggerdarling.dk/", "type": "Restaurant, concerts", "notes": "/menu for menu. Live music. Year-round."},
            {"name": "Restaurant Tri", "url": "https://www.restaurant-tri.com/", "type": "Fine dining", "notes": "Michelin-starred. Check seasonal open/close."},
            {"name": "Signalmasten Agger", "url": "https://signalmasten-agger.dk/", "type": "Restaurant", "notes": "Year-round."},
            {"name": "Vesterhavshytten", "url": "https://www.vesterhavshytten-agger.dk/", "type": "Grillbar", "notes": "Seasonal — verify open/closed."},
            {"name": "Agger Surf & Events", "url": "https://www.aggersurfandevents.com/", "type": "Surf, activities", "notes": "Surf school, SUP, bar. Seasonal."},
            {"name": "Cold Hawaii Watersport", "url": "https://coldhawaiiwatersport.dk/", "type": "Water activities", "notes": "RIB boats, seal/dolphin safaris."},
            {"name": "Agger Bådelaug", "url": "https://agger-baadelaug.dk/", "type": "Community events", "notes": "De Sorte Huse: Krabbefest, Tørfiskedag."},
            {"name": "Agger Feriehuse", "url": "https://www.aggerferiehuse.dk/dk/kystbyen-agger", "type": "Town overview", "notes": "Business listings."},
            {"name": "Agger Glamping", "url": "https://aggerglamping.dk/en/look-in-the-area/", "type": "Area guide", "notes": "Curated local guide."},
            {"name": "Agger Holidays", "url": "https://aggerholidays.dk/", "type": "Area tips", "notes": "/spisesteder and /en/agger-and-other-experiences-thy."},
        ],
    },
    2: {
        "label": "Thy Regional",
        "sources": [
            {"name": "Thy360 calendar", "url": "https://www.thy360.dk/kalender", "type": "Events", "notes": "Primary structured event source for Thy."},
            {"name": "KultuNaut", "url": "https://www.kultunaut.dk/", "type": "Events by venue", "notes": "Filter to 7770 area."},
            {"name": "Nationalpark Thy news", "url": "https://nationalparkthy.dk/om-os/nyheder/", "type": "Nature events", "notes": "Seasonal programs, guided tours."},
            {"name": "Nationalparkbooking", "url": "https://nationalparkbooking.dk/", "type": "Bookable experiences", "notes": "Guided tours, lectures."},
            {"name": "VisitThy events", "url": "https://www.visitthy.com/thy/experiences/events-thy", "type": "Tourism events", "notes": "Official tourism portal."},
            {"name": "VisitNordvestkysten", "url": "https://www.visitnordvestkysten.dk/", "type": "Regional tourism", "notes": "Agger-specific pages exist."},
            {"name": "Museum Thy", "url": "https://museumthy.dk/", "type": "Exhibitions", "notes": "Thisted Museum, Heltborg."},
            {"name": "Kunsthal Thy", "url": "https://kunsthalthy.dk/", "type": "Art exhibitions", "notes": "Open Fri–Sun."},
            {"name": "SMK Thy", "url": "https://www.smkthy.dk/", "type": "Art exhibitions", "notes": "National art in Doverodde."},
            {"name": "Filmklubben Thy", "url": "https://filmklubben-thy.dk/", "type": "Film screenings", "notes": "Art-house at Kino Thisted."},
            {"name": "Kino Thisted", "url": "https://www.kinothisted.dk/", "type": "Cinema", "notes": "/programbestil-billetter/ for schedule."},
            {"name": "Cold Hawaii Ultra", "url": "https://thyultra.dk/", "type": "Trail race", "notes": "Finishes in Agger. September."},
            {"name": "Thyborøn Turist", "url": "https://www.thyboron-turist.dk/", "type": "Tourism portal", "notes": "Day trip via ferry ~15 min."},
            {"name": "JyllandsAkvariet", "url": "https://jyllandsakvariet.dk/", "type": "Aquarium", "notes": "Touch pools, safaris. Thyborøn."},
            {"name": "Sea War Museum", "url": "https://www.seawarmuseum.dk/", "type": "WW1 museum", "notes": "Thyborøn."},
            {"name": "Bunkermuseum", "url": "https://bunkermuseumhanstholm.dk/", "type": "WW2 museum", "notes": "Hanstholm. Closed Nov–Mar."},
            {"name": "Cold Hawaii Surf Camp", "url": "https://coldhawaiisurfcamp.com/", "type": "Surf school", "notes": "Klitmøller."},
            {"name": "Thy Whisky", "url": "https://www.thy-whisky.dk/", "type": "Distillery tours", "notes": "Near Agger."},
            {"name": "VesterhavsCaminoen", "url": "https://vesterhavscaminoen.dk/", "type": "Walking holidays", "notes": "Thyborøn–Vestervig."},
        ],
    },
    3: {
        "label": "Wider Area (1-2 hour radius, major events only)",
        "sources": [
            {"name": "VisitMors", "url": "https://www.visitmors.com/", "type": "Tourism", "notes": "Mors island. ~45 min."},
            {"name": "Destination Limfjorden", "url": "https://www.destinationlimfjorden.com/", "type": "Tourism", "notes": "Skive, Struer, Morsø."},
            {"name": "Jesperhus", "url": "https://www.jesperhus.dk/", "type": "Family park", "notes": "Major family attraction on Mors."},
            {"name": "Museum Mors", "url": "https://museummors.dk/", "type": "Museums", "notes": "Dueholm Kloster, fossil hunts."},
            {"name": "Dansk Skaldyrcenter", "url": "https://skaldyrcenteret.dk/", "type": "Shellfish", "notes": "Nykøbing Mors."},
            {"name": "Limfjordsmuseet", "url": "https://limfjordsmuseet.dk/", "type": "Maritime museum", "notes": "Løgstør."},
            {"name": "Bovbjerg Fyr", "url": "https://bovbjergfyr.dk/", "type": "Lighthouse, art", "notes": "~1 hr south."},
        ],
    },
    4: {
        "label": "News & Supplementary (background only)",
        "sources": [
            {"name": "Vores Thy", "url": "https://vores-thy.dk/", "type": "Local news", "notes": "/artikler for latest."},
            {"name": "Thisted Kommune", "url": "https://www.thisted.dk/nyheder", "type": "Municipal", "notes": "Official announcements."},
        ],
    },
}

KNOWN_CLOSED = [
    {"name": "Agger Badehotel", "url": "agger-hotel.dk", "status": "CLOSED — renovating."},
    {"name": "Agger Is-Café", "url": "", "status": "UNKNOWN — no web presence."},
    {"name": "Kystcentret Thyborøn", "url": "", "status": "CLOSED INDEFINITELY."},
]


@tool
def get_sources(tier: int | None = None) -> str:
    """Get crawl source URLs organized by tier (1=Agger local, 2=Thy regional, 3=wider area, 4=news).

    Call this at the start of your run to get source URLs to fetch from.
    Tier 1 sources are highest priority. Always check Tier 1 and 2.
    Only use Tier 3 for major events. Tier 4 is background/supplementary.

    Args:
        tier: Specific tier to return (1-4). If None, returns all tiers.

    Returns:
        Formatted source list with URLs and notes.
    """
    tiers = [tier] if tier else [1, 2, 3, 4]
    lines = []

    for t in tiers:
        if t not in SOURCES:
            continue
        group = SOURCES[t]
        lines.append(f"## Tier {t} — {group['label']}")
        for s in group["sources"]:
            lines.append(f"- {s['name']}: {s['url']} — {s['type']}. {s['notes']}")
        lines.append("")

    lines.append("## KNOWN CLOSED — DO NOT RECOMMEND")
    for s in KNOWN_CLOSED:
        lines.append(f"- {s['name']}: {s['status']}")

    return "\n".join(lines)
