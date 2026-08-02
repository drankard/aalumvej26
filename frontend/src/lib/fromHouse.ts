// First-hand notes about reaching each place from Ålumvej 26.
//
// The notes themselves are plain markdown files in src/content/from-house/,
// named "<slug>.<lang>.md" — see the README in that folder.
//
// They are not held in this file on purpose. This is prose written by hand in a
// browser, and Danish is full of apostrophes and quotes; one unescaped character
// in a TypeScript string literal breaks the build, which means a typo in a note
// takes down the whole deploy rather than just that note. A markdown file has no
// syntax to get wrong. The same reasoning is why it is not JSON.
//
// Nor is it in DynamoDB, where it started: there is no CLI or console access
// here, so a field that can only be written through AWS is a field nobody can
// write. The stored value is still read as a fallback for anything already
// there, and the content pipeline preserves it across rewrites
// (PRESERVED_TRANSLATION_FIELDS in stages.py).

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { LANGS, type Lang } from "./i18n";

const NOTES_DIR = join(process.cwd(), "src", "content", "from-house");

export type FromHouseEntry = Partial<Record<Lang, string>>;

function loadNotes(): Record<string, FromHouseEntry> {
  if (!existsSync(NOTES_DIR)) return {};

  const notes: Record<string, FromHouseEntry> = {};
  const langs = new Set<string>(LANGS);

  for (const file of readdirSync(NOTES_DIR)) {
    if (!file.endsWith(".md") || file === "README.md") continue;

    // "<slug>.<lang>.md" — the slug itself contains dots rarely but hyphens
    // often, so split from the right rather than the left.
    const parts = file.slice(0, -3).split(".");
    const lang = parts.pop();
    const slug = parts.join(".");

    if (!lang || !langs.has(lang) || !slug) {
      console.warn(
        `[fromHouse] ignoring ${file} — expected "<slug>.<lang>.md" with lang one of ${[...langs].join(", ")}`
      );
      continue;
    }

    const text = readFileSync(join(NOTES_DIR, file), "utf8").trim();
    if (!text) continue;
    notes[slug] = { ...notes[slug], [lang as Lang]: text };
  }
  return notes;
}

/** Built once per build; the notes are static files read at build time. */
export const FROM_HOUSE: Record<string, FromHouseEntry> = loadNotes();

/**
 * Hand-written note for a slug, falling back to whatever the pipeline stored.
 * The file wins: it is the source anyone can actually edit.
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
 * Slugs derive from the Danish title, and the pipeline's area audit can rewrite
 * an area's name — which changes its slug and silently orphans the note written
 * for it. Without this the text just stops appearing, the kind of failure nobody
 * notices for months. It also catches a mistyped filename, which is the likeliest
 * mistake when copying a long slug out of a URL.
 *
 * Warn rather than throw: a misfiled note must never fail a deploy.
 */
export function warnOrphanedFromHouseKeys(knownSlugs: Iterable<string>): string[] {
  const known = new Set(knownSlugs);
  const orphaned = Object.keys(FROM_HOUSE).filter((slug) => !known.has(slug));

  if (orphaned.length) {
    console.warn(
      `[fromHouse] ${orphaned.length} note(s) match no current page — check the ` +
        `filename against the page's URL. These render nowhere:\n` +
        orphaned.map((s) => `  - ${s}`).join("\n")
    );
  }
  return orphaned;
}
