// Canonical facts about the house itself.
//
// This is the one subject where the site *is* the primary source, so the values
// live here rather than coming from the content pipeline. Everything below is
// drawn from the existing locale copy (src/i18n/locales/*.json) — nothing is
// estimated. Keep this file and the locale JSON in agreement: the structured
// data on /huset/ and the home page are both generated from these values, and a
// mismatch between markup and visible copy is worse than omitting the claim.

import type { Lang } from "./i18n";
import type { Fact, FaqItem } from "./types";

export const HOUSE_GEO = { latitude: 56.7925, longitude: 8.2647 } as const;

export const HOUSE_ADDRESS = {
  "@type": "PostalAddress",
  streetAddress: "Ålumvej 26",
  addressLocality: "Agger",
  postalCode: "7770",
  addressRegion: "Nordjylland",
  addressCountry: "DK",
} as const;

export const HOUSE_SIZE_M2 = 60;
export const HOUSE_BEDROOMS = 2;
export const HOUSE_SLEEPS = 4;
export const HOUSE_PLOT_M2 = 1000;
export const BEACH_DISTANCE_M = 200;

/** Facts table for /huset/. `computed: true` — the site is the source here. */
export const HOUSE_FACTS: Record<Lang, Fact[]> = {
  da: [
    { label: "Størrelse", value: "60 m²", computed: true },
    { label: "Soverum", value: "2 soverum, 4 sovepladser", computed: true },
    { label: "Grund", value: "1.000 m² naturgrund", computed: true },
    { label: "Afstand til stranden", value: "200 m", computed: true },
    { label: "Bygget / renoveret", value: "Bygget 1900, renoveret 2000", computed: true },
    { label: "Opvarmning", value: "Brændeovn og energi-varmepumpe", computed: true },
    { label: "Husdyr", value: "Max 1 hund tilladt", computed: true },
    { label: "Internet", value: "WiFi og Chromecast", computed: true },
    { label: "Køkken", value: "Opvaskemaskine og vaskemaskine", computed: true },
    { label: "Adresse", value: "Ålumvej 26, 7770 Vestervig", computed: true },
  ],
  en: [
    { label: "Size", value: "60 m²", computed: true },
    { label: "Bedrooms", value: "2 bedrooms, sleeps 4", computed: true },
    { label: "Plot", value: "1,000 m² natural garden", computed: true },
    { label: "Distance to the beach", value: "200 m", computed: true },
    { label: "Built / renovated", value: "Built 1900, renovated 2000", computed: true },
    { label: "Heating", value: "Wood-burning stove and heat pump", computed: true },
    { label: "Pets", value: "One dog allowed", computed: true },
    { label: "Internet", value: "WiFi and Chromecast", computed: true },
    { label: "Kitchen", value: "Dishwasher and washing machine", computed: true },
    { label: "Address", value: "Ålumvej 26, 7770 Vestervig, Denmark", computed: true },
  ],
  de: [
    { label: "Größe", value: "60 m²", computed: true },
    { label: "Schlafzimmer", value: "2 Schlafzimmer, 4 Schlafplätze", computed: true },
    { label: "Grundstück", value: "1.000 m² Naturgrundstück", computed: true },
    { label: "Entfernung zum Strand", value: "200 m", computed: true },
    { label: "Baujahr / Renovierung", value: "Gebaut 1900, renoviert 2000", computed: true },
    { label: "Heizung", value: "Holzofen und Wärmepumpe", computed: true },
    { label: "Haustiere", value: "Ein Hund erlaubt", computed: true },
    { label: "Internet", value: "WLAN und Chromecast", computed: true },
    { label: "Küche", value: "Spülmaschine und Waschmaschine", computed: true },
    { label: "Adresse", value: "Ålumvej 26, 7770 Vestervig, Dänemark", computed: true },
  ],
};

/** Answers restate facts already on the site — none of them are invented. */
export const HOUSE_FAQ: Record<Lang, FaqItem[]> = {
  da: [
    {
      question: "Hvor mange kan der sove i huset?",
      answer:
        "Huset har 2 soverum med i alt 4 sovepladser. Det er på 60 m² og ligger på en naturgrund på 1.000 m².",
    },
    {
      question: "Må man tage hund med?",
      answer: "Ja, der må medbringes én hund.",
    },
    {
      question: "Hvor langt er der til Vesterhavet?",
      answer:
        "Der er 200 meter til stranden. Huset ligger i Agger på kanten af Nationalpark Thy, så både klitheden og havet er inden for gåafstand.",
    },
    {
      question: "Er der WiFi i huset?",
      answer: "Ja, der er WiFi og Chromecast. Køkkenet har opvaskemaskine, og der er vaskemaskine i huset.",
    },
    {
      question: "Hvordan booker man huset?",
      answer:
        "Huset udlejes via Agger Feriehuse. Aktuelle priser og ledige uger findes på deres bookingside, hvor reservationen også gennemføres.",
    },
  ],
  en: [
    {
      question: "How many people can sleep in the house?",
      answer:
        "The house has 2 bedrooms sleeping 4 in total. It is 60 m² and sits on a 1,000 m² natural garden plot.",
    },
    {
      question: "Are dogs allowed?",
      answer: "Yes, one dog may come along.",
    },
    {
      question: "How far is it to the North Sea?",
      answer:
        "The beach is 200 metres away. The house is in Agger on the edge of Thy National Park, so both the dune heath and the sea are within walking distance.",
    },
    {
      question: "Is there WiFi?",
      answer:
        "Yes, there is WiFi and Chromecast. The kitchen has a dishwasher, and there is a washing machine in the house.",
    },
    {
      question: "How do I book the house?",
      answer:
        "The house is let through Agger Feriehuse. Current prices and available weeks are on their booking page, where the reservation is completed.",
    },
  ],
  de: [
    {
      question: "Wie viele Personen können im Haus schlafen?",
      answer:
        "Das Haus hat 2 Schlafzimmer mit insgesamt 4 Schlafplätzen. Es ist 60 m² groß und liegt auf einem 1.000 m² großen Naturgrundstück.",
    },
    {
      question: "Sind Hunde erlaubt?",
      answer: "Ja, ein Hund darf mitgebracht werden.",
    },
    {
      question: "Wie weit ist es zur Nordsee?",
      answer:
        "Zum Strand sind es 200 Meter. Das Haus liegt in Agger am Rand des Nationalparks Thy, sodass Dünenheide und Meer zu Fuß erreichbar sind.",
    },
    {
      question: "Gibt es WLAN im Haus?",
      answer:
        "Ja, es gibt WLAN und Chromecast. Die Küche hat eine Spülmaschine, und im Haus steht eine Waschmaschine.",
    },
    {
      question: "Wie bucht man das Haus?",
      answer:
        "Das Haus wird über Agger Feriehuse vermietet. Aktuelle Preise und freie Wochen finden sich auf deren Buchungsseite, wo die Reservierung abgeschlossen wird.",
    },
  ],
};

export const HOUSE_INTRO: Record<Lang, string> = {
  da: "Et ældre, stråtækt feriehus på 60 m² i Agger — 200 meter fra Vesterhavet og med Nationalpark Thy som nabo. Nænsomt restaureret i gammel stil med moderne komfort: brændeovn, varmepumpe, WiFi og en østvendt, lukket gårdhave på en naturgrund på 1.000 m². Der er plads til fire.",
  en: "A 60 m² thatched holiday cottage in Agger — 200 metres from the North Sea with Thy National Park as its neighbour. Carefully restored in the old style with modern comfort: wood-burning stove, heat pump, WiFi and a sheltered east-facing courtyard on a 1,000 m² natural plot. It sleeps four.",
  de: "Ein 60 m² großes, reetgedecktes Ferienhaus in Agger — 200 Meter von der Nordsee und direkt am Nationalpark Thy. Behutsam im alten Stil restauriert, mit modernem Komfort: Holzofen, Wärmepumpe, WLAN und ein geschützter, nach Osten gerichteter Innenhof auf 1.000 m² Naturgrundstück. Platz für vier Personen.",
};
