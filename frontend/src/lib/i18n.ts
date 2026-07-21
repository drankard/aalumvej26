import da from "../i18n/locales/da.json";
import en from "../i18n/locales/en.json";
import de from "../i18n/locales/de.json";

export type Lang = "da" | "en" | "de";
export const LANGS: Lang[] = ["da", "en", "de"];
export const DEFAULT_LANG: Lang = "da";

export type Locale = typeof da;
const LOCALES: Record<Lang, Locale> = { da, en: en as Locale, de: de as Locale };

export const loc = (lang: Lang): Locale => LOCALES[lang];

export const langPrefix = (lang: Lang): string => (lang === DEFAULT_LANG ? "" : `/${lang}`);

export const OG_LOCALE: Record<Lang, string> = { da: "da_DK", en: "en_GB", de: "de_DE" };

export const HTML_LANG: Record<Lang, string> = { da: "da", en: "en", de: "de" };

/** Pick a translation record with da fallback. */
export function pickTr<T>(translations: Record<string, T> | undefined, lang: Lang): T {
  const t = translations ?? {};
  return (t[lang] ?? t[DEFAULT_LANG] ?? Object.values(t)[0] ?? {}) as T;
}

// Page-scaffold strings that don't exist in the SPA-era locale JSONs.
const UI = {
  da: {
    backHome: "Forside",
    allExperiences: "Alle oplevelser",
    allAreas: "Hele området",
    readMoreSource: "Læs mere hos kilden",
    sources: "Kilder",
    distance: "Afstand",
    nearbyHeading: "Bo lige i nærheden",
    intro: "Din guide til Nationalpark Thy og Vestkysten.",
    otherLangs: "Andre sprog",
    related: "Flere oplevelser",
    category: "Kategori",
    archiveIntro: "Tidligere events og oplevelser fra guiden — bevaret som arkiv.",
    notFoundTitle: "Siden blev ikke fundet",
    notFoundText: "Siden findes ikke — men huset og guiden gør. Fortsæt her:",
    updatedLabel: "Opdateret",
  },
  en: {
    backHome: "Home",
    allExperiences: "All experiences",
    allAreas: "The whole area",
    readMoreSource: "Read more at the source",
    sources: "Sources",
    distance: "Distance",
    nearbyHeading: "Stay right nearby",
    intro: "Your guide to Nationalpark Thy and the Danish west coast.",
    otherLangs: "Other languages",
    related: "More experiences",
    category: "Category",
    archiveIntro: "Past events and experiences from the guide — kept as an archive.",
    notFoundTitle: "Page not found",
    notFoundText: "That page doesn't exist — but the house and the guide do. Continue here:",
    updatedLabel: "Updated",
  },
  de: {
    backHome: "Startseite",
    allExperiences: "Alle Erlebnisse",
    allAreas: "Die ganze Umgebung",
    readMoreSource: "Mehr bei der Quelle",
    sources: "Quellen",
    distance: "Entfernung",
    nearbyHeading: "Übernachten gleich nebenan",
    intro: "Dein Guide für den Nationalpark Thy und die dänische Westküste.",
    otherLangs: "Andere Sprachen",
    related: "Weitere Erlebnisse",
    category: "Kategorie",
    archiveIntro: "Frühere Events und Erlebnisse aus dem Guide — als Archiv erhalten.",
    notFoundTitle: "Seite nicht gefunden",
    notFoundText: "Diese Seite gibt es nicht — aber das Haus und den Guide schon. Weiter geht's hier:",
    updatedLabel: "Aktualisiert",
  },
} as const;

export const ui = (lang: Lang) => UI[lang];
