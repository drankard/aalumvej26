// First-hand notes about reaching each place from Ålumvej 26.
//
// ─── HOW TO FILL THESE IN ────────────────────────────────────────────────────
// Edit this file directly on github.com (open it, press the pencil icon) and
// commit to a branch — no checkout, no AWS access needed. The next deploy to
// main publishes it.
//
// Write 40–80 words. What the drive is actually like, where to park when it is
// busy, which season you go, what to combine it with, what you would tell a
// friend. Concrete beats lyrical: "20 minutter ad Vesterhavsvej, sidste stykke
// er grusvej" is worth more than "en skøn oplevelse".
//
// This is the one block on the site that no other page in the world can
// reproduce, which is exactly why it is worth citing rather than the source it
// summarises. Everything else here is assembled from other people's pages.
//
// Danish first. `en` and `de` are optional — a language you omit simply renders
// nothing there, which is better than showing Danish text to a German reader.
// Leave a slug out entirely if you have nothing real to say about it; an empty
// block is better than filler.
//
// Keys are the page slug, i.e. the last path segment of the URL:
//   https://www.aalumvej26.dk/oplevelser/lodbjerg-fyr-klatr-.../  ->  "lodbjerg-fyr-klatr-..."
//
// Slugs are seeded below for the evergreen places — the ones still worth
// reading next year. Dated events are deliberately absent: a personal note on a
// weekend that has already happened is wasted writing. Add any slug you like.
// ─────────────────────────────────────────────────────────────────────────────

import type { Lang } from "./i18n";

export type FromHouseEntry = Partial<Record<Lang, string>>;

export const FROM_HOUSE: Record<string, FromHouseEntry> = {
  // ── Området ────────────────────────────────────────────────────────────────
  "nationalpark-thy": {},
  "cold-hawaii-klitmoeller": {},
  limfjorden: {},
  thisted: {},
  "mors-jesperhus": {},
  hanstholm: {},

  // ── Oplevelser (evergreen) ─────────────────────────────────────────────────
  "lodbjerg-fyr-klatr-op-i-fyret-og-drik-kaffe-i-den-gamle-fyrm": {},
  "thy-whisky-besoeg-danmarks-nordligste-distilleri-og-smag-pri": {},
  "nationalparkcenter-thy-ny-saeson": {},
  "vesterhavshytten-grillbar-med-klitudsigt-i-agger": {},
  "restaurant-signalmasten-aabent-hele-aaret-i-agger": {},
  "stenbjerg-landingsplads": {},
  "vestkyststi-agger-til-bulbjerg": {},
  "agger-tange-fuglenes-paradis": {},
  "ny-vandresti-i-agger-agger-taabel-stien-6-km": {},
  "vandring-paa-diget-rundt-om-agger-4-km-med-udsigt-over-hav-o": {},
  "makrelfiskeri-fra-molerne-i-agger-bedste-bid-i-juli-og-augus": {},
  "klitheden-blomstrer-foraarsflora-i-nationalpark-thy": {},
  "nr-vorupoer-fisk-fra-kutteren": {},
  "bunkermuseum-hanstholm-olsen-banden-i-thy-ny-saerudstilling": {},
  "sea-war-museum-jutland-i-thyboroen-jyllandsslaget-og-nordsoe": {},
  "smk-thy-nationalkunst-i-verdensklasse-ved-limfjorden": {},
  "laer-at-surfe-cold-hawaii-surf-camp": {},
  "delfin-og-saelsafari-med-rib-baad-fra-agger": {},
};

/**
 * Hand-written note for a slug, falling back to whatever the content pipeline
 * stored. The repo file wins: it is the editable-without-AWS source, and the
 * pipeline never authors this field anyway (see PRESERVED_TRANSLATION_FIELDS).
 */
export function fromHouse(
  slug: string,
  lang: Lang,
  stored?: string
): string | undefined {
  const written = FROM_HOUSE[slug]?.[lang]?.trim();
  return written || stored?.trim() || undefined;
}

/**
 * Warn about notes that no longer match any page.
 *
 * Slugs derive from the Danish title, so renaming an area (the pipeline's area
 * audit can rewrite names) changes its slug and silently orphans the note
 * written for it. Without this the text just stops appearing, which is the kind
 * of failure nobody notices for months. Warn rather than throw — an orphaned
 * note must never fail the build.
 */
export function warnOrphanedFromHouseKeys(knownSlugs: Iterable<string>): string[] {
  const known = new Set(knownSlugs);
  const orphaned = Object.entries(FROM_HOUSE)
    .filter(([slug, entry]) => Object.values(entry).some((v) => v?.trim()) && !known.has(slug))
    .map(([slug]) => slug);

  if (orphaned.length) {
    console.warn(
      `[fromHouse] ${orphaned.length} hand-written note(s) match no current page — ` +
        `the slug probably changed with a title. These render nowhere:\n` +
        orphaned.map((s) => `  - ${s}`).join("\n")
    );
  }
  return orphaned;
}
