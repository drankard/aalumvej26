"""One-time seed script to migrate hardcoded content into DynamoDB."""
from __future__ import annotations

import os
import sys

import boto3

sys.path.insert(0, os.path.dirname(__file__))

from repositories.base import DynamoDBAdapter
from repositories.content import PostRepository, AreaRepository, CategoryRepository
from models.content import PostCreate, PostTranslation, AreaCreate, AreaTranslation, CategoryCreate, CategoryTranslation

POSTS = [
    {
        "category": "surf", "tag_key": "event", "emoji": "🏄", "sort_order": 1,
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii",
        "translations": {
            "da": {"title": "Danish Open Windsurf: Wave i Klitmøller", "excerpt": "Waveriding-konkurrencen i Danish Open 2026 afholdes 23\u201325. maj i Klitmøller. Internationale og danske windsurfere konkurrerer om DM-titlen og point til PWA/WWT verdensranglisten.", "date": "23\u201325. maj 2026"},
            "en": {"title": "Danish Open Windsurf: Waves in Klitmøller", "excerpt": "The wave riding competition at Danish Open 2026 takes place 23\u201325 May in Klitmøller. International and Danish windsurfers compete for the national title and PWA/WWT world ranking points.", "date": "23\u201325 May 2026"},
            "de": {"title": "Danish Open Windsurf: Wellen in Klitmøller", "excerpt": "Der Waveride-Wettbewerb bei den Danish Open 2026 findet vom 23.\u201325. Mai in Klitmøller statt. Internationale und dänische Windsurfer kämpfen um den DM-Titel und Punkte für die PWA/WWT-Weltrangliste.", "date": "23.\u201325. Mai 2026"},
        },
    },
    {
        "category": "natur", "tag_key": "openNow", "emoji": "🏛", "sort_order": 2,
        "url": "https://eng.nationalparkthy.dk/explore-the-national-park/visitor-centers/national-park-center-thy",
        "translations": {
            "da": {"title": "Nationalparkcenter Thy: Ny sæson", "excerpt": "Nationalparkcentret i Nr. Vorupør har udvidet åbningstider fra april: dagligt kl. 11\u201316. Gratis adgang, frivillige værter med lokaltips, og 300 m² udstilling om klithede og dyreliv.", "date": "Dagligt kl. 11\u201316 fra 1. april"},
            "en": {"title": "Thy National Park Centre: New Season", "excerpt": "The National Park Centre in Nr. Vorupør has extended opening hours from April: daily 11 am\u20134 pm. Free admission, volunteer hosts with local tips, and 300 m² exhibition on dune heath and wildlife.", "date": "Daily 11 am\u20134 pm from 1 April"},
            "de": {"title": "Nationalparkzentrum Thy: Neue Saison", "excerpt": "Das Nationalparkzentrum in Nr. Vorupør hat ab April erweiterte Öffnungszeiten: täglich 11\u201316 Uhr. Freier Eintritt, ehrenamtliche Guides mit Lokaltipps und 300 m² Ausstellung über Dünenheide und Tierwelt.", "date": "Täglich 11\u201316 Uhr ab 1. April"},
        },
    },
    {
        "category": "mad", "tag_key": "seasonBest", "emoji": "🦪", "sort_order": 3,
        "url": "https://www.visitdenmark.com/denmark/things-do/outdoor-nature/thy-national-park",
        "translations": {
            "da": {"title": "Østerssæson på Limfjorden", "excerpt": "Limfjordsøsters er verdensberømte \u2014 og sæsonen kører stadig. Tag med på guidet safari i det lave vand, eller køb dem friske hos lokale fiskehandlere.", "date": "Sæson: oktober \u2013 april"},
            "en": {"title": "Oyster Season on the Limfjord", "excerpt": "Limfjord oysters are world-famous \u2014 and the season is still running. Join a guided safari in the shallow waters, or buy them fresh from local fishmongers.", "date": "Season: October \u2013 April"},
            "de": {"title": "Austernsaison am Limfjord", "excerpt": "Limfjord-Austern sind weltberühmt \u2014 und die Saison läuft noch. Nehmen Sie an einer geführten Safari im flachen Wasser teil oder kaufen Sie sie frisch beim örtlichen Fischhändler.", "date": "Saison: Oktober \u2013 April"},
        },
    },
    {
        "category": "surf", "tag_key": "event", "emoji": "💨", "sort_order": 4,
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii",
        "translations": {
            "da": {"title": "Danish Open Freestyle i Løgstør", "excerpt": "Første stop i Danish Open 2026 er freestyle-konkurrence på Limfjorden ved Løgstør. Perfekte fladevandsbetingelser for spektakulære tricks.", "date": "14\u201317. maj 2026"},
            "en": {"title": "Danish Open Freestyle in Løgstør", "excerpt": "First stop in Danish Open 2026 is the freestyle competition on the Limfjord at Løgstør. Perfect flatwater conditions for spectacular tricks.", "date": "14\u201317 May 2026"},
            "de": {"title": "Danish Open Freestyle in Løgstør", "excerpt": "Erster Stopp der Danish Open 2026 ist der Freestyle-Wettbewerb am Limfjord bei Løgstør. Perfekte Flachwasserbedingungen für spektakuläre Tricks.", "date": "14.\u201317. Mai 2026"},
        },
    },
    {
        "category": "natur", "tag_key": "guide", "emoji": "🥾", "sort_order": 5,
        "url": "https://www.komoot.com/guide/513698/attractions-in-nationalpark-thy",
        "translations": {
            "da": {"title": "Vestkyststi: Agger til Bulbjerg", "excerpt": "En af Danmarks smukkeste vandreruter langs kysten mod nord. Passér Stenbjerg Landingsplads, Lyngby og de dramatiske klitter.", "date": "Helårsrute"},
            "en": {"title": "West Coast Trail: Agger to Bulbjerg", "excerpt": "One of Denmark's most beautiful coastal hikes heading north. Pass Stenbjerg Landing, Lyngby, and the dramatic dunes.", "date": "Year-round route"},
            "de": {"title": "Westküstenweg: Agger nach Bulbjerg", "excerpt": "Eine der schönsten Küstenwanderungen Dänemarks Richtung Norden. Vorbei an Stenbjerg Landingsplads, Lyngby und den dramatischen Dünen.", "date": "Ganzjahresroute"},
        },
    },
    {
        "category": "born", "tag_key": "kidFriendly", "emoji": "🌺", "sort_order": 6,
        "url": "https://www.jesperhus.dk/",
        "translations": {
            "da": {"title": "Jesperhus Blomsterpark åbner", "excerpt": "Skandinaviens største blomsterpark på Mors åbner udendørssæsonen 18. april. Piratland, JungleZoo, 4D-biograf og shows med Hugo & Rita.", "date": "Åbner 18. april 2026"},
            "en": {"title": "Jesperhus Flower Park Opens", "excerpt": "Scandinavia's largest flower park on Mors opens the outdoor season 18 April. Pirateland, JungleZoo, 4D cinema, and shows with Hugo & Rita.", "date": "Opens 18 April 2026"},
            "de": {"title": "Jesperhus Blumenpark öffnet", "excerpt": "Skandinaviens größter Blumenpark auf Mors eröffnet die Freiluftsaison am 18. April. Piratenland, JungleZoo, 4D-Kino und Shows mit Hugo & Rita.", "date": "Öffnet 18. April 2026"},
        },
    },
    {
        "category": "natur", "tag_key": "natureGem", "emoji": "🦅", "sort_order": 7,
        "url": "https://www.visitdenmark.com/denmark/things-do/outdoor-nature/thy-national-park",
        "translations": {
            "da": {"title": "Agger Tange: Fuglenes paradis", "excerpt": "Et af Nordeuropas vigtigste rastepladser for vandfugle. Handicapvenlig sti op til diget med udsigt over tusindvis af vadefugle. Medtag kikkert!", "date": "Bedst: forår & efterår"},
            "en": {"title": "Agger Tange: Bird Paradise", "excerpt": "One of Northern Europe's most important staging areas for wading birds. Accessible path up to the dike with views of thousands of waders. Bring binoculars!", "date": "Best: spring & autumn"},
            "de": {"title": "Agger Tange: Vogelparadies", "excerpt": "Einer der wichtigsten Rastplätze Nordeuropas für Watvögel. Barrierefreier Weg zum Deich mit Blick auf Tausende von Watvögeln. Fernglas mitbringen!", "date": "Beste Zeit: Frühjahr & Herbst"},
        },
    },
    {
        "category": "surf", "tag_key": "activity", "emoji": "🌊", "sort_order": 8,
        "url": "https://coldhawaiisurfcamp.com/",
        "translations": {
            "da": {"title": "Lær at surfe: Cold Hawaii Surf Camp", "excerpt": "Mor og Vahine \u2014 med 15 danske mesterskabstitler \u2014 driver surfskole i Klitmøller. Kurser for alle niveauer, sauna med havudsigt og surf-café.", "date": "Sæsonåbent fra maj"},
            "en": {"title": "Learn to Surf: Cold Hawaii Surf Camp", "excerpt": "Mor and Vahine \u2014 with 15 Danish championship titles \u2014 run a surf school in Klitmøller. Courses for all levels, sauna with sea view, and surf café.", "date": "Open from May"},
            "de": {"title": "Surfen lernen: Cold Hawaii Surf Camp", "excerpt": "Mor und Vahine \u2014 mit 15 dänischen Meistertiteln \u2014 betreiben eine Surfschule in Klitmøller. Kurse für alle Niveaus, Sauna mit Meerblick und Surf-Café.", "date": "Geöffnet ab Mai"},
        },
    },
    {
        "category": "kultur", "tag_key": "culturalHistory", "emoji": "⚓", "sort_order": 9,
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/whatson/thy-national-park-self-guided-tours-gdk601416",
        "translations": {
            "da": {"title": "Stenbjerg Landingsplads", "excerpt": "Fiskerne byggede selv de pittoreske nyttehuse omkring 1900. I dag huser stedet nationalparkens temacenter med lokal udstilling.", "date": "Dagligt april\u2013okt, kl. 10\u201317"},
            "en": {"title": "Stenbjerg Landing Place", "excerpt": "The fishermen built the picturesque utility houses around 1900. Today the site houses the national park's theme centre with a local exhibition.", "date": "Daily Apr\u2013Oct, 10 am\u20135 pm"},
            "de": {"title": "Stenbjerg Landingsplads", "excerpt": "Die Fischer bauten die malerischen Zweckhäuser um 1900 selbst. Heute beherbergt der Ort das Themenzentrum des Nationalparks mit einer lokalen Ausstellung.", "date": "Täglich April\u2013Okt, 10\u201317 Uhr"},
        },
    },
    {
        "category": "born", "tag_key": "kidFriendly", "emoji": "🦁", "sort_order": 10,
        "url": "https://www.gladzoo.dk/besog-os/",
        "translations": {
            "da": {"title": "Glad Zoo: Sæsonstart", "excerpt": "Familievenlig zoo nær Thisted. Åbner 28. marts, dagligt kl. 10\u201316. Dyrepasser-for-en-dag, café og 50% rabat på Jesperhus med årskort.", "date": "Åbent fra 28. marts 2026"},
            "en": {"title": "Glad Zoo: Season Start", "excerpt": "Family-friendly zoo near Thisted. Opens 28 March, daily 10 am\u20134 pm. Zookeeper-for-a-day, café, and 50% off Jesperhus with annual pass.", "date": "Open from 28 March 2026"},
            "de": {"title": "Glad Zoo: Saisonstart", "excerpt": "Familienfreundlicher Zoo bei Thisted. Öffnet am 28. März, täglich 10\u201316 Uhr. Tierpfleger-für-einen-Tag, Café und 50% Rabatt auf Jesperhus mit Jahreskarte.", "date": "Geöffnet ab 28. März 2026"},
        },
    },
    {
        "category": "mad", "tag_key": "localFavorite", "emoji": "🐟", "sort_order": 11,
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii",
        "translations": {
            "da": {"title": "Nr. Vorupør: Fisk fra kutteren", "excerpt": "Ved landingspladsen i Vorupør sælger lokale fiskere dagens fangst direkte fra kutteren. Caféer og restauranter samlet ved havnen.", "date": "Hele året"},
            "en": {"title": "Nr. Vorupør: Fish from the Boat", "excerpt": "At the landing place in Vorupør, local fishermen sell the day's catch straight from the cutter. Cafés and restaurants gathered by the harbour.", "date": "Year-round"},
            "de": {"title": "Nr. Vorupør: Fisch direkt vom Kutter", "excerpt": "Am Landeplatz in Vorupør verkaufen örtliche Fischer den Tagesfang direkt vom Kutter. Cafés und Restaurants am Hafen.", "date": "Ganzjährig"},
        },
    },
    {
        "category": "surf", "tag_key": "bigEvent", "emoji": "🏆", "sort_order": 12,
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii",
        "translations": {
            "da": {"title": "Cold Hawaii Games 2026", "excerpt": "Flere uger med surf, sport og outdoor fra Agger til Hanstholm. Red Bull King of the Air, PWA Youth World Cup, trail running, MTB og yoga.", "date": "Sep \u2013 okt 2026"},
            "en": {"title": "Cold Hawaii Games 2026", "excerpt": "Multiple weeks of surf, sport, and outdoor from Agger to Hanstholm. Red Bull King of the Air, PWA Youth World Cup, trail running, MTB, and yoga.", "date": "Sep \u2013 Oct 2026"},
            "de": {"title": "Cold Hawaii Games 2026", "excerpt": "Mehrere Wochen Surf, Sport und Outdoor von Agger bis Hanstholm. Red Bull King of the Air, PWA Youth World Cup, Trailrunning, MTB und Yoga.", "date": "Sep \u2013 Okt 2026"},
        },
    },
]

AREAS = [
    {
        "url": "https://eng.nationalparkthy.dk/explore-the-national-park/visitor-centers/national-park-center-thy", "sort_order": 0,
        "translations": {
            "da": {"name": "Nationalpark Thy", "dist": "Omgiver Agger", "desc": "Danmarks første nationalpark \u2014 244 km² vild natur med klithede, skov og kyst. Kronhjorte, oddere og havørne."},
            "en": {"name": "Thy National Park", "dist": "Surrounds Agger", "desc": "Denmark's first national park \u2014 244 km² of wild nature with dune heath, forest, and coast. Red deer, otters, and white-tailed eagles."},
            "de": {"name": "Nationalpark Thy", "dist": "Umgibt Agger", "desc": "Dänemarks erster Nationalpark \u2014 244 km² wilde Natur mit Dünenheide, Wald und Küste. Rothirsche, Fischotter und Seeadler."},
        },
    },
    {
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii", "sort_order": 1,
        "translations": {
            "da": {"name": "Cold Hawaii / Klitmøller", "dist": "~35 min (39 km)", "desc": "Nordeuropas surfmekka. 31 registrerede surfspots langs kysten. Vorupør ca. 20 min fra Agger."},
            "en": {"name": "Cold Hawaii / Klitmøller", "dist": "~35 min (39 km)", "desc": "Northern Europe's surf mecca. 31 registered surf spots along the coast. Vorupør approx. 20 min from Agger."},
            "de": {"name": "Cold Hawaii / Klitmøller", "dist": "~35 Min (39 km)", "desc": "Nordeuropas Surfmekka. 31 registrierte Surfspots entlang der Küste. Vorupør ca. 20 Min von Agger."},
        },
    },
    {
        "url": "https://www.visitdenmark.com/denmark/things-do/outdoor-nature/thy-national-park", "sort_order": 2,
        "translations": {
            "da": {"name": "Limfjorden", "dist": "Lige øst for Agger", "desc": "Agger ligger mellem havet og fjorden. Verdensberømte østers, kajak, SUP og rolige fjordvande."},
            "en": {"name": "Limfjorden", "dist": "Just east of Agger", "desc": "Agger lies between the sea and the fjord. World-famous oysters, kayaking, SUP, and calm fjord waters."},
            "de": {"name": "Limfjorden", "dist": "Direkt östlich von Agger", "desc": "Agger liegt zwischen Meer und Fjord. Weltberühmte Austern, Kajak, SUP und ruhiges Fjordwasser."},
        },
    },
    {
        "url": "https://www.visit-nordvestkysten.com/feriesteder/thy", "sort_order": 3,
        "translations": {
            "da": {"name": "Thisted", "dist": "~35 min (38 km)", "desc": "Regionens hjerte med butikker, restauranter, biograf, kulturliv og Nationalparkcenter Thy."},
            "en": {"name": "Thisted", "dist": "~35 min (38 km)", "desc": "The region's heart with shops, restaurants, cinema, cultural life, and Thy National Park Centre."},
            "de": {"name": "Thisted", "dist": "~35 Min (38 km)", "desc": "Das Herz der Region mit Geschäften, Restaurants, Kino, Kulturleben und Nationalparkzentrum Thy."},
        },
    },
    {
        "url": "https://www.jesperhus.dk/", "sort_order": 4,
        "translations": {
            "da": {"name": "Mors & Jesperhus", "dist": "~45 min kørsel", "desc": "Skandinaviens største blomsterpark, Glad Zoo og Moler-klinterne. Perfekt familiedagstur."},
            "en": {"name": "Mors & Jesperhus", "dist": "~45 min drive", "desc": "Scandinavia's largest flower park, Glad Zoo, and the Moler cliffs. Perfect family day trip."},
            "de": {"name": "Mors & Jesperhus", "dist": "~45 Min Fahrt", "desc": "Skandinaviens größter Blumenpark, Glad Zoo und die Moler-Klippen. Perfekter Familienausflug."},
        },
    },
    {
        "url": "https://www.visit-nordvestkysten.com/northwest-coast/inspiration/cold-hawaii", "sort_order": 5,
        "translations": {
            "da": {"name": "Hanstholm", "dist": "~45 min (51 km)", "desc": "Fæstningsmuseum fra 2. verdenskrig, Nordsøen Oceanarium og stor fiskerihavn."},
            "en": {"name": "Hanstholm", "dist": "~45 min (51 km)", "desc": "WWII fortress museum, North Sea Oceanarium, and large fishing harbour."},
            "de": {"name": "Hanstholm", "dist": "~45 Min (51 km)", "desc": "Festungsmuseum aus dem 2. Weltkrieg, Nordsee-Ozeanarium und großer Fischereihafen."},
        },
    },
]


CATEGORIES = [
    {"id": "natur", "icon": "🌿", "sort_order": 1, "translations": {"da": {"label": "Natur & Vandring"}, "en": {"label": "Nature & Hiking"}, "de": {"label": "Natur & Wandern"}}},
    {"id": "kultur", "icon": "✦", "sort_order": 2, "translations": {"da": {"label": "Kultur"}, "en": {"label": "Culture"}, "de": {"label": "Kultur"}}},
    {"id": "mad", "icon": "🦪", "sort_order": 3, "translations": {"da": {"label": "Mad & Drikke"}, "en": {"label": "Food & Drink"}, "de": {"label": "Essen & Trinken"}}},
    {"id": "surf", "icon": "〰", "sort_order": 4, "translations": {"da": {"label": "Surf & Strand"}, "en": {"label": "Surf & Beach"}, "de": {"label": "Surf & Strand"}}},
    {"id": "born", "icon": "☀", "sort_order": 5, "translations": {"da": {"label": "Børnevenligt"}, "en": {"label": "Family Friendly"}, "de": {"label": "Familienfreundlich"}}},
]


def seed():
    table_name = os.environ.get("TABLE_NAME", "aalumvej26-prod")
    region = os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")
    profile = os.environ.get("AWS_PROFILE", "graveyard-master")

    session = boto3.Session(profile_name=profile, region_name=region)
    table = session.resource("dynamodb").Table(table_name)
    db = DynamoDBAdapter(table)

    post_repo = PostRepository(db)
    area_repo = AreaRepository(db)
    category_repo = CategoryRepository(db)

    print(f"Seeding to {table_name} in {region} (profile: {profile})")

    for i, p in enumerate(POSTS):
        translations = {
            lang: PostTranslation(**t) for lang, t in p["translations"].items()
        }
        data = PostCreate(
            category=p["category"],
            tag_key=p["tag_key"],
            url=p["url"],
            emoji=p["emoji"],
            sort_order=p["sort_order"],
            translations=translations,
        )
        post = post_repo.create(data)
        print(f"  POST {i+1}/{len(POSTS)}: {post.id} - {post.translations['da'].title}")

    for i, a in enumerate(AREAS):
        translations = {
            lang: AreaTranslation(**t) for lang, t in a["translations"].items()
        }
        data = AreaCreate(
            url=a["url"],
            sort_order=a["sort_order"],
            translations=translations,
        )
        area = area_repo.create(data)
        print(f"  AREA {i+1}/{len(AREAS)}: {area.id} - {area.translations['da'].name}")

    for i, c in enumerate(CATEGORIES):
        translations = {
            lang: CategoryTranslation(**t) for lang, t in c["translations"].items()
        }
        data = CategoryCreate(
            id=c["id"],
            icon=c["icon"],
            sort_order=c["sort_order"],
            translations=translations,
        )
        cat = category_repo.create(data)
        print(f"  CAT {i+1}/{len(CATEGORIES)}: {cat.id} - {cat.translations['da'].label}")

    print(f"\nDone: {len(POSTS)} posts + {len(AREAS)} areas + {len(CATEGORIES)} categories seeded.")


if __name__ == "__main__":
    seed()
