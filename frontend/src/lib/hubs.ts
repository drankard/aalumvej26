// Hand-written copy for the category hubs.
//
// The hubs previously rendered a card grid and nothing else, which left the
// queries with actual search volume ("hvad kan man lave i Nationalpark Thy",
// "surf for begyndere Cold Hawaii") sitting on pages with zero unique text.
//
// Everything here is deliberately general and verifiable — the national park's
// designation, the geography of the coast, how the seasons behave. Specific,
// perishable facts (opening hours, prices, dates) belong on the individual
// experience pages, where the pipeline can source them.

import type { Lang } from "./i18n";
import type { FaqItem } from "./types";

export interface HubContent {
  intro: string;
  body: string;
  faq: FaqItem[];
}

type HubMap = Record<string, Record<Lang, HubContent>>;

export const HUBS: HubMap = {
  natur: {
    da: {
      intro:
        "Nationalpark Thy er Danmarks første nationalpark, udpeget i 2008, og strækker sig langs vestkysten fra Agger i syd til Hanstholm i nord. Det er klithede, klitplantage, søer og 55 kilometer kyst — det største sammenhængende naturområde af sin art i Vesteuropa.",
      body: `## Hvad landskabet består af

Klitheden er kernen. Det er et åbent, lavt landskab af lyng, revling og sand, formet af vinden og holdt lysåbent af havgusen. Ind mod land ligger klitplantagerne, plantet for at dæmpe sandflugten, og mellem dem ligger klitsøerne.

## Hvornår man skal tage af sted

Landskabet skifter markant hen over året. Lyngen blomstrer sidst på sommeren og farver heden lilla. Efterår og vinter giver de kraftigste vestenvinde og det mest dramatiske hav. Forår er bedst til fugletræk — Agger Tange er en vigtig rasteplads for trækfugle.

## Før du går ud

Vejret på vestkysten skifter hurtigt, og der er langt mellem læ. Tag vindtæt tøj med, også om sommeren. Havet har kraftig strøm og revlehuller — bad kun hvor der er opsyn, og aldrig alene i høj bølgegang.`,
      faq: [
        {
          question: "Hvornår blev Nationalpark Thy oprettet?",
          answer:
            "Nationalpark Thy blev indviet i 2008 som Danmarks første nationalpark. Den dækker et bælte langs vestkysten fra Agger i syd til Hanstholm i nord.",
        },
        {
          question: "Hvad er klithede?",
          answer:
            "Klithede er et åbent landskab af lyng, revling og sand bag klitrækken. Det holdes lysåbent af vind og salt, og det er den naturtype nationalparken er udpeget for at beskytte.",
        },
        {
          question: "Må man gå frit i nationalparken?",
          answer:
            "Store dele af nationalparken er offentligt tilgængelige, og der er afmærkede stier og ruter. Vær opmærksom på skiltning i yngletiden og i militære øvelsesområder, hvor adgangen kan være begrænset.",
        },
      ],
    },
    en: {
      intro:
        "Thy National Park is Denmark's first national park, designated in 2008, running along the west coast from Agger in the south to Hanstholm in the north. It is dune heath, dune plantation, lakes and 55 kilometres of coast — the largest continuous area of its kind in Western Europe.",
      body: `## What the landscape is made of

Dune heath is the core of it: an open, low landscape of heather, crowberry and sand, shaped by wind and kept treeless by salt spray. Inland lie the dune plantations, planted to stop the sand drift, with dune lakes in between.

## When to go

The landscape changes sharply through the year. The heather flowers in late summer and turns the heath purple. Autumn and winter bring the strongest westerlies and the most dramatic sea. Spring is best for migration — Agger Tange is an important stopover for migrating birds.

## Before you set out

Weather on the west coast turns quickly and there is little shelter. Bring windproof clothing, including in summer. The sea has strong currents and rip channels — swim only where supervised, and never alone in heavy surf.`,
      faq: [
        {
          question: "When was Thy National Park established?",
          answer:
            "Thy National Park opened in 2008 as Denmark's first national park. It covers a belt along the west coast from Agger in the south to Hanstholm in the north.",
        },
        {
          question: "What is dune heath?",
          answer:
            "Dune heath is the open landscape of heather, crowberry and sand behind the dune ridge. Wind and salt keep it treeless, and it is the habitat the national park was designated to protect.",
        },
        {
          question: "Can you walk freely in the national park?",
          answer:
            "Large parts of the park are open to the public, with marked paths and routes. Watch for signage during the breeding season and in military training areas, where access can be restricted.",
        },
      ],
    },
    de: {
      intro:
        "Der Nationalpark Thy ist Dänemarks erster Nationalpark, ausgewiesen 2008, und erstreckt sich entlang der Westküste von Agger im Süden bis Hanstholm im Norden. Dünenheide, Dünenplantagen, Seen und 55 Kilometer Küste — das größte zusammenhängende Gebiet seiner Art in Westeuropa.",
      body: `## Woraus die Landschaft besteht

Die Dünenheide ist der Kern: eine offene, niedrige Landschaft aus Heidekraut, Krähenbeere und Sand, vom Wind geformt und durch Salzluft baumfrei gehalten. Landeinwärts liegen die Dünenplantagen, gepflanzt gegen die Sandflucht, dazwischen die Dünenseen.

## Wann man fahren sollte

Die Landschaft verändert sich im Jahresverlauf deutlich. Die Heide blüht im Spätsommer und färbt sich violett. Herbst und Winter bringen die stärksten Westwinde und die dramatischste See. Das Frühjahr eignet sich am besten für den Vogelzug — Agger Tange ist ein wichtiger Rastplatz für Zugvögel.

## Bevor es losgeht

Das Wetter an der Westküste schlägt schnell um, und Schutz gibt es kaum. Winddichte Kleidung gehört auch im Sommer dazu. Das Meer hat starke Strömungen und Rinnen — nur an beaufsichtigten Stellen baden und nie allein bei hohem Wellengang.`,
      faq: [
        {
          question: "Wann wurde der Nationalpark Thy gegründet?",
          answer:
            "Der Nationalpark Thy wurde 2008 als erster Nationalpark Dänemarks eröffnet. Er umfasst einen Streifen entlang der Westküste von Agger im Süden bis Hanstholm im Norden.",
        },
        {
          question: "Was ist Dünenheide?",
          answer:
            "Dünenheide ist die offene Landschaft aus Heidekraut, Krähenbeere und Sand hinter dem Dünenkamm. Wind und Salz halten sie baumfrei — es ist der Lebensraum, für dessen Schutz der Nationalpark ausgewiesen wurde.",
        },
        {
          question: "Darf man sich im Nationalpark frei bewegen?",
          answer:
            "Große Teile des Parks sind öffentlich zugänglich, mit markierten Wegen und Routen. Beschilderung während der Brutzeit und in militärischen Übungsgebieten beachten — dort kann der Zugang eingeschränkt sein.",
        },
      ],
    },
  },

  surf: {
    da: {
      intro:
        "Cold Hawaii er navnet på surfspottene langs Thys vestkyst, med Klitmøller som omdrejningspunkt. Kombinationen af nordvestlig vind, revler og et hav uden læ giver bølger stort set året rundt — og et af Nordeuropas mest kendte områder for wave-windsurfing og surf.",
      body: `## Hvorfor kysten virker

Vinden kommer ind fra Nordatlanten uden noget at bremse den, og revlerne uden for kysten former bølgerne, inden de når ind. Det giver forudsigelige forhold på tværs af mange spots, så der næsten altid er et sted, der virker på en given vindretning.

## Sæson og forhold

Efterår og vinter giver de største og mest konsistente bølger, men også koldt vand — heldragt er nødvendig størstedelen af året. Sommeren er roligere og bedre for begyndere, med varmere vand og mindre bølger.

## Hvis du er begynder

Start med en skole. Vestkysten er ikke et sted at lære sig selv: strømmen er kraftig, revlehullerne trækker udad, og forholdene kan skifte i løbet af en time. Skoler og udlejning findes flere steder langs kysten og kan rådgive om, hvilket spot der passer til dagens vind.`,
      faq: [
        {
          question: "Hvad er Cold Hawaii?",
          answer:
            "Cold Hawaii er samlebetegnelsen for surfspottene langs Thys vestkyst med Klitmøller som centrum. Navnet henviser til de gode bølgeforhold kombineret med koldt nordatlantisk vand.",
        },
        {
          question: "Hvornår er der bedst bølger?",
          answer:
            "Efterår og vinter giver de største og mest konsistente bølger, fordi vestenvinden er kraftigst da. Sommeren er roligere og bedre egnet til begyndere.",
        },
        {
          question: "Kan man surfe som begynder på vestkysten?",
          answer:
            "Ja, men gør det gennem en skole. Strømmen er kraftig og forholdene skifter hurtigt, så det er ikke en kyst at lære sig selv på. Skoler langs kysten udlejer udstyr og vurderer, hvilket spot der passer til dagens vind.",
        },
      ],
    },
    en: {
      intro:
        "Cold Hawaii is the name for the surf spots along the west coast of Thy, centred on Klitmøller. North-westerly wind, offshore sandbars and a sea with no shelter produce waves more or less year-round — and one of Northern Europe's best-known areas for wave windsurfing and surfing.",
      body: `## Why the coast works

Wind arrives from the North Atlantic with nothing to slow it, and the sandbars offshore shape the waves before they reach the beach. The result is predictable conditions across many spots, so there is nearly always somewhere that works for a given wind direction.

## Season and conditions

Autumn and winter bring the biggest and most consistent waves, and also cold water — a wetsuit is needed for most of the year. Summer is calmer and better for beginners, with warmer water and smaller surf.

## If you are a beginner

Start with a school. This is not a coast to teach yourself on: the current is strong, rip channels pull seaward, and conditions can change within an hour. Schools and rental operate at several points along the coast and can advise which spot suits the day's wind.`,
      faq: [
        {
          question: "What is Cold Hawaii?",
          answer:
            "Cold Hawaii is the collective name for the surf spots along the west coast of Thy, centred on Klitmøller. The name refers to the quality of the wave conditions combined with cold North Atlantic water.",
        },
        {
          question: "When are the waves best?",
          answer:
            "Autumn and winter give the largest and most consistent waves, as the westerlies are strongest then. Summer is calmer and better suited to beginners.",
        },
        {
          question: "Can beginners surf on the west coast?",
          answer:
            "Yes, but go through a school. The current is strong and conditions shift quickly, so it is not a coast to learn on alone. Schools along the coast rent equipment and judge which spot suits the day's wind.",
        },
      ],
    },
    de: {
      intro:
        "Cold Hawaii ist der Name für die Surfspots entlang der Westküste von Thy, mit Klitmøller als Zentrum. Nordwestwind, vorgelagerte Sandbänke und eine schutzlose See sorgen nahezu ganzjährig für Wellen — und für eines der bekanntesten Wavewindsurf- und Surfgebiete Nordeuropas.",
      body: `## Warum die Küste funktioniert

Der Wind kommt vom Nordatlantik, ohne dass ihn etwas bremst, und die Sandbänke vor der Küste formen die Wellen, bevor sie den Strand erreichen. Das ergibt verlässliche Bedingungen über viele Spots hinweg — fast immer funktioniert einer bei der jeweiligen Windrichtung.

## Saison und Bedingungen

Herbst und Winter bringen die größten und beständigsten Wellen, aber auch kaltes Wasser — ein Neoprenanzug ist den größten Teil des Jahres nötig. Der Sommer ist ruhiger und für Anfänger besser geeignet, mit wärmerem Wasser und kleineren Wellen.

## Für Anfänger

Mit einer Schule anfangen. Diese Küste eignet sich nicht zum Selbstbeibringen: Die Strömung ist stark, Rinnen ziehen seewärts, und die Bedingungen ändern sich innerhalb einer Stunde. Schulen und Verleih gibt es an mehreren Stellen entlang der Küste; sie beraten, welcher Spot zum Wind des Tages passt.`,
      faq: [
        {
          question: "Was ist Cold Hawaii?",
          answer:
            "Cold Hawaii ist die Sammelbezeichnung für die Surfspots entlang der Westküste von Thy mit Klitmøller als Zentrum. Der Name verweist auf die guten Wellenbedingungen bei kaltem nordatlantischem Wasser.",
        },
        {
          question: "Wann sind die Wellen am besten?",
          answer:
            "Herbst und Winter bringen die größten und beständigsten Wellen, da der Westwind dann am stärksten ist. Der Sommer ist ruhiger und für Anfänger besser geeignet.",
        },
        {
          question: "Können Anfänger an der Westküste surfen?",
          answer:
            "Ja, aber über eine Schule. Die Strömung ist stark und die Bedingungen wechseln schnell — allein lernen sollte man hier nicht. Schulen entlang der Küste verleihen Ausrüstung und beurteilen, welcher Spot zum Wind des Tages passt.",
        },
      ],
    },
  },

  born: {
    da: {
      intro:
        "Vestkysten med børn kræver lidt planlægning — havet er ikke et badeland, og vejret skifter. Til gengæld er der brede strande, lavvandede fjordsider, museer med noget at røre ved og en natur, hvor børn kan få lov at løbe.",
      body: `## Strand og sikkerhed

Vesterhavet har kraftig strøm og revlehuller, der trækker udad. Bad kun hvor der er livredder eller opsyn, hold børn inden for rækkevidde, og lad være med at gå i vandet i høj bølgegang. På rolige dage er de brede sandstrande ideelle til at grave, flyve med drage og lede efter rav.

## Når vejret svigter

Regn og blæst hører til på vestkysten. Museer, akvarier og besøgscentre i området fungerer som plan B, og flere af dem er indrettet med aktiviteter for børn frem for montrer.

## Roligere vand

Fjord- og tangesiderne er markant mere beskyttede end havsiden. Vil man have lavvandet og roligt badevand med mindre børn, er det den side, man skal søge mod.`,
      faq: [
        {
          question: "Er Vesterhavet sikkert at bade i med børn?",
          answer:
            "Kun med forbehold. Der er kraftig strøm og revlehuller, der trækker udad. Bad hvor der er opsyn, hold børn inden for rækkevidde, og hold jer på land ved høj bølgegang.",
        },
        {
          question: "Hvad kan man lave med børn, når det regner?",
          answer:
            "Områdets museer og besøgscentre fungerer som indendørs alternativer, og flere er indrettet med aktiviteter frem for udstillingsmontrer. Se de enkelte oplevelser for åbningstider.",
        },
        {
          question: "Hvor er der roligt badevand?",
          answer:
            "Fjord- og tangesiden er mere beskyttet end havsiden og har lavvandede partier, der egner sig bedre til mindre børn end den åbne vestkyst.",
        },
      ],
    },
    en: {
      intro:
        "The west coast with children takes a little planning — the sea is not a swimming pool and the weather shifts. What it offers instead is wide beaches, sheltered shallow water on the fjord side, museums with things to touch, and space to let children run.",
      body: `## Beach and safety

The North Sea has strong currents and rip channels that pull seaward. Swim only where there is a lifeguard or supervision, keep children within reach, and stay out of the water in heavy surf. On calm days the wide sand beaches are ideal for digging, kite-flying and hunting for amber.

## When the weather turns

Rain and wind come with the territory. Museums, aquariums and visitor centres in the area work as a plan B, and several are built around activities rather than display cases.

## Calmer water

The fjord and spit sides are markedly more sheltered than the sea side. For shallow, calm bathing water with younger children, that is the side to head for.`,
      faq: [
        {
          question: "Is the North Sea safe for swimming with children?",
          answer:
            "Only with care. There are strong currents and rip channels that pull seaward. Swim where there is supervision, keep children within reach, and stay ashore in heavy surf.",
        },
        {
          question: "What is there to do with children when it rains?",
          answer:
            "The area's museums and visitor centres work as indoor alternatives, and several are built around activities rather than display cases. See the individual experiences for opening times.",
        },
        {
          question: "Where is the calmer bathing water?",
          answer:
            "The fjord and spit side is more sheltered than the sea side and has shallow stretches better suited to younger children than the open west coast.",
        },
      ],
    },
    de: {
      intro:
        "Die Westküste mit Kindern erfordert etwas Planung — das Meer ist kein Schwimmbad, und das Wetter wechselt. Dafür gibt es breite Strände, geschütztes flaches Wasser auf der Fjordseite, Museen zum Anfassen und Natur, in der Kinder laufen dürfen.",
      body: `## Strand und Sicherheit

Die Nordsee hat starke Strömungen und Rinnen, die seewärts ziehen. Nur dort baden, wo Aufsicht besteht, Kinder in Reichweite halten und bei hohem Wellengang aus dem Wasser bleiben. An ruhigen Tagen eignen sich die breiten Sandstrände hervorragend zum Graben, Drachensteigen und Bernsteinsuchen.

## Wenn das Wetter kippt

Regen und Wind gehören dazu. Museen, Aquarien und Besucherzentren in der Region funktionieren als Plan B, und mehrere davon setzen auf Mitmachen statt auf Vitrinen.

## Ruhigeres Wasser

Die Fjord- und Nehrungsseite ist deutlich geschützter als die Meerseite. Wer flaches, ruhiges Badewasser für kleinere Kinder sucht, sollte dorthin ausweichen.`,
      faq: [
        {
          question: "Ist die Nordsee zum Baden mit Kindern sicher?",
          answer:
            "Nur mit Vorsicht. Es gibt starke Strömungen und Rinnen, die seewärts ziehen. Nur mit Aufsicht baden, Kinder in Reichweite halten und bei hohem Wellengang an Land bleiben.",
        },
        {
          question: "Was kann man mit Kindern bei Regen unternehmen?",
          answer:
            "Museen und Besucherzentren der Region eignen sich als Alternative bei Regen, mehrere davon setzen auf Mitmachangebote statt auf Vitrinen. Öffnungszeiten stehen bei den einzelnen Erlebnissen.",
        },
        {
          question: "Wo ist das Badewasser ruhiger?",
          answer:
            "Die Fjord- und Nehrungsseite ist geschützter als die Meerseite und hat flache Abschnitte, die für kleinere Kinder besser geeignet sind als die offene Westküste.",
        },
      ],
    },
  },

  mad: {
    da: {
      intro:
        "Maden i Thy hænger sammen med kysten: fisk landet i Hanstholm og Thyborøn, østers og muslinger fra Limfjorden, og en håndfuld steder, der laver noget ud af det. Uden for højsæsonen har mange steder begrænset åbningstid — ring før du kører.",
      body: `## Hvad området er kendt for

Limfjordsøsters er den mest kendte råvare, og de høstes typisk i den kolde halvdel af året. Dertil kommer fisk fra vestkysthavnene og et voksende antal lokale producenter — røgerier, bryggerier og destillerier.

## Sæson og åbningstider

Det er værd at tage alvorligt: mange spisesteder i området holder åbent efter sæson snarere end efter kalender. Uden for sommermånederne kan åbningstiderne være kortere eller kun i weekenden, og enkelte steder lukker helt.

## Book, hvis du kan

Antallet af pladser er begrænset i et tyndt befolket område, og et enkelt busselskab eller en gruppe kan fylde et sted. Reservation er sjældent et krav, men ofte en god idé.`,
      faq: [
        {
          question: "Hvornår er der østerssæson i Limfjorden?",
          answer:
            "Østers høstes traditionelt i den kolde del af året. Konkrete datoer og guidede østersture varierer fra år til år — se de enkelte oplevelser for aktuelle oplysninger.",
        },
        {
          question: "Har spisestederne åbent hele året?",
          answer:
            "Ikke nødvendigvis. Mange steder i området følger sæsonen, og uden for sommermånederne kan åbningstiden være kortere, begrænset til weekenden eller helt lukket. Tjek før du kører.",
        },
        {
          question: "Skal man bestille bord?",
          answer:
            "Det er sjældent et krav, men ofte fornuftigt. Området har begrænset kapacitet, og et enkelt selskab kan fylde et spisested — særligt i højsæsonen og i weekenden.",
        },
      ],
    },
    en: {
      intro:
        "Food in Thy follows the coast: fish landed at Hanstholm and Thyborøn, oysters and mussels from the Limfjord, and a handful of places that make something of it. Outside high season many places keep limited hours — call before you drive.",
      body: `## What the area is known for

Limfjord oysters are the best-known ingredient, harvested mainly in the colder half of the year. Alongside them are fish from the west coast harbours and a growing number of local producers — smokehouses, breweries and distilleries.

## Season and opening hours

Worth taking seriously: many places in the area open according to the season rather than the calendar. Outside the summer months hours may be shorter, weekend-only, or the place may close entirely.

## Book if you can

Capacity is limited in a thinly populated area, and a single group can fill a place. Reservation is rarely required, but it is often a good idea.`,
      faq: [
        {
          question: "When is oyster season in the Limfjord?",
          answer:
            "Oysters are traditionally harvested in the colder part of the year. Exact dates and guided oyster safaris vary year to year — see the individual experiences for current information.",
        },
        {
          question: "Are restaurants open all year?",
          answer:
            "Not necessarily. Many places in the area follow the season, and outside the summer months hours may be shorter, weekend-only, or closed entirely. Check before you drive.",
        },
        {
          question: "Should I book a table?",
          answer:
            "Rarely required, but often sensible. The area has limited capacity and a single party can fill a restaurant — particularly in high season and at weekends.",
        },
      ],
    },
    de: {
      intro:
        "Das Essen in Thy folgt der Küste: Fisch aus Hanstholm und Thyborøn, Austern und Muscheln aus dem Limfjord und eine Handvoll Orte, die etwas daraus machen. Außerhalb der Hochsaison haben viele nur eingeschränkt geöffnet — vorher anrufen.",
      body: `## Wofür die Region bekannt ist

Limfjord-Austern sind das bekannteste Produkt, geerntet vor allem in der kalten Jahreshälfte. Dazu kommen Fisch aus den Westküstenhäfen und eine wachsende Zahl lokaler Produzenten — Räuchereien, Brauereien und Destillerien.

## Saison und Öffnungszeiten

Das sollte man ernst nehmen: Viele Betriebe richten sich nach der Saison, nicht nach dem Kalender. Außerhalb der Sommermonate können die Zeiten kürzer sein, nur am Wochenende gelten oder ganz entfallen.

## Reservieren, wenn möglich

Die Kapazitäten sind in einer dünn besiedelten Region begrenzt, und eine einzige Gruppe kann ein Lokal füllen. Eine Reservierung ist selten Pflicht, aber oft sinnvoll.`,
      faq: [
        {
          question: "Wann ist Austernsaison im Limfjord?",
          answer:
            "Austern werden traditionell in der kalten Jahreszeit geerntet. Konkrete Termine und geführte Austerntouren variieren von Jahr zu Jahr — aktuelle Angaben stehen bei den einzelnen Erlebnissen.",
        },
        {
          question: "Haben die Lokale ganzjährig geöffnet?",
          answer:
            "Nicht unbedingt. Viele Betriebe richten sich nach der Saison; außerhalb der Sommermonate können die Zeiten kürzer sein, nur am Wochenende gelten oder ganz entfallen. Vorher prüfen.",
        },
        {
          question: "Sollte man einen Tisch reservieren?",
          answer:
            "Selten Pflicht, aber oft sinnvoll. Die Region hat begrenzte Kapazität, und eine einzelne Gesellschaft kann ein Lokal füllen — besonders in der Hochsaison und am Wochenende.",
        },
      ],
    },
  },

  kultur: {
    da: {
      intro:
        "Kulturen i Thy er formet af havet: fyrtårne, redningsstationer, fiskerihistorie og bunkers fra Atlantvolden. Dertil kommer museer og kunstinstitutioner, der har fået uventet vægt i et tyndtbefolket område.",
      body: `## Kysten som historie

Vestkysten har altid været farlig at sejle ved, og det har sat sig i landskabet: fyrtårne, redningsstationer og vrag. Fyrene kan flere steder besøges, og de fortæller samtidig historien om sandflugten, der flyttede hele kystlinjen.

## Krigens spor

Under besættelsen blev kysten en del af Atlantvolden, og bunkerne står stadig — nogle er sunket i klitterne, andre er gjort tilgængelige som museer eller udstillingsrum.

## Museer og kunst

Området har en håndfuld museer og kunstinstitutioner af mere end lokal betydning. Åbningstiderne følger ofte sæsonen, så tjek før du kører — særligt uden for sommermånederne.`,
      faq: [
        {
          question: "Kan man komme op i fyrtårnene?",
          answer:
            "Flere af fyrene på kysten kan besøges, men adgang og åbningstider varierer og følger typisk sæsonen. Se de enkelte oplevelser for aktuelle oplysninger.",
        },
        {
          question: "Hvad er bunkerne på kysten?",
          answer:
            "De stammer fra Atlantvolden, den tyske kystbefæstning fra besættelsestiden. Nogle er sunket i klitterne og står frit tilgængelige, andre indgår i museer eller udstillinger.",
        },
        {
          question: "Har museerne åbent hele året?",
          answer:
            "Ikke alle. Mange museer og besøgssteder i området har sæsonbestemte åbningstider med begrænset åbning uden for sommermånederne. Tjek det aktuelle museum, før du kører.",
        },
      ],
    },
    en: {
      intro:
        "Culture in Thy is shaped by the sea: lighthouses, rescue stations, fishing history and bunkers from the Atlantic Wall. Alongside them are museums and art institutions that carry unexpected weight for a thinly populated area.",
      body: `## The coast as history

The west coast has always been dangerous to sail, and that has left its mark: lighthouses, rescue stations and wrecks. Several lighthouses can be visited, and they also tell the story of the sand drift that moved the coastline itself.

## Traces of the war

During the occupation the coast became part of the Atlantic Wall, and the bunkers are still there — some sunk into the dunes, others opened up as museums or exhibition spaces.

## Museums and art

The area has a handful of museums and art institutions of more than local significance. Opening hours often follow the season, so check before you drive — particularly outside the summer months.`,
      faq: [
        {
          question: "Can you go up the lighthouses?",
          answer:
            "Several lighthouses on the coast can be visited, but access and opening hours vary and usually follow the season. See the individual experiences for current information.",
        },
        {
          question: "What are the bunkers along the coast?",
          answer:
            "They date from the Atlantic Wall, the German coastal fortification built during the occupation. Some have sunk into the dunes and stand freely accessible; others form part of museums or exhibitions.",
        },
        {
          question: "Are the museums open all year?",
          answer:
            "Not all of them. Many museums and visitor sites in the area have seasonal hours with limited opening outside the summer months. Check the specific museum before you drive.",
        },
      ],
    },
    de: {
      intro:
        "Die Kultur in Thy ist vom Meer geprägt: Leuchttürme, Rettungsstationen, Fischereigeschichte und Bunker des Atlantikwalls. Dazu kommen Museen und Kunstinstitutionen, die für eine dünn besiedelte Region ein bemerkenswertes Gewicht haben.",
      body: `## Die Küste als Geschichte

Die Westküste war immer gefährlich zu befahren, und das hat Spuren hinterlassen: Leuchttürme, Rettungsstationen und Wracks. Mehrere Leuchttürme lassen sich besichtigen; sie erzählen zugleich die Geschichte der Sandflucht, die die Küstenlinie verschoben hat.

## Spuren des Krieges

Während der Besatzung wurde die Küste Teil des Atlantikwalls, und die Bunker stehen noch — manche in den Dünen versunken, andere als Museum oder Ausstellungsraum zugänglich gemacht.

## Museen und Kunst

Die Region hat eine Handvoll Museen und Kunstinstitutionen von mehr als lokaler Bedeutung. Die Öffnungszeiten folgen oft der Saison — besonders außerhalb der Sommermonate vorher prüfen.`,
      faq: [
        {
          question: "Kann man die Leuchttürme besteigen?",
          answer:
            "Mehrere Leuchttürme an der Küste können besichtigt werden, Zugang und Öffnungszeiten variieren jedoch und richten sich meist nach der Saison. Aktuelle Angaben stehen bei den einzelnen Erlebnissen.",
        },
        {
          question: "Was hat es mit den Bunkern an der Küste auf sich?",
          answer:
            "Sie stammen vom Atlantikwall, der deutschen Küstenbefestigung aus der Besatzungszeit. Manche sind in den Dünen versunken und frei zugänglich, andere gehören zu Museen oder Ausstellungen.",
        },
        {
          question: "Haben die Museen ganzjährig geöffnet?",
          answer:
            "Nicht alle. Viele Museen und Besucherorte der Region haben saisonale Öffnungszeiten mit eingeschränktem Betrieb außerhalb der Sommermonate. Vor der Fahrt beim jeweiligen Museum prüfen.",
        },
      ],
    },
  },
};

export const getHub = (categoryId: string | undefined, lang: Lang): HubContent | undefined =>
  categoryId ? HUBS[categoryId]?.[lang] : undefined;
