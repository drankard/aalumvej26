// Per-page photography.
//
// ─── HOW TO ADD AN IMAGE ─────────────────────────────────────────────────────
// 1. Upload the file on github.com to frontend/public/images/steder/ — use
//    "Add file > Upload files" in that folder. Name it after the slug.
// 2. Add an entry below with a real alt text describing what is in the photo.
// 3. Commit. The next deploy to main publishes it.
//
// Alt text is not decoration: it is the only description a screen reader or an
// image crawler gets. "Lodbjerg Fyr set fra klitheden en klar eftermiddag" is
// useful; "billede" and "Lodbjerg Fyr" are not.
//
// ─── WHY ENTRIES ARE NOT AUTO-DISCOVERED ─────────────────────────────────────
// Only add a photo that genuinely shows the place. Where an entry exists it is
// published as schema.org `image` — a factual claim that this picture depicts
// this subject. Every experience page previously advertised the house exterior
// as its image, which was simply untrue, and that markup was removed rather
// than left lying. A page with no entry gets no `image` in its structured data
// at all; the house photo is still used for the social-sharing preview, which
// is presentation rather than an assertion about the subject.
// ─────────────────────────────────────────────────────────────────────────────

import { existsSync } from "node:fs";
import { join } from "node:path";
import { SITE } from "./site";

export interface PageImage {
  /** Absolute site path, e.g. "/images/steder/lodbjerg-fyr.jpg". */
  src: string;
  /** What is actually in the photo, in Danish. */
  alt: string;
}

/** Keyed by page slug — the last path segment of the URL. */
export const PAGE_IMAGES: Record<string, PageImage> = {
  // "lodbjerg-fyr-klatr-op-i-fyret-og-drik-kaffe-i-den-gamle-fyrm": {
  //   src: "/images/steder/lodbjerg-fyr.jpg",
  //   alt: "Lodbjerg Fyr set fra klitheden en klar eftermiddag",
  // },
};

export const pageImage = (slug: string): PageImage | undefined => PAGE_IMAGES[slug];

/** Absolute URL for og:image / schema.org, which both require one. */
export const absoluteImage = (src: string): string => `${SITE}${src}`;

/**
 * Warn about entries whose file is missing or whose slug matches no page.
 *
 * Both fail silently otherwise: a typo'd path yields a broken <img> and an
 * `image` in structured data pointing at a 404, which is worse than having no
 * image at all. Warn rather than throw — a missing photo must not fail a deploy.
 */
export function warnBrokenImages(knownSlugs: Iterable<string>): string[] {
  const known = new Set(knownSlugs);
  const problems: string[] = [];

  for (const [slug, img] of Object.entries(PAGE_IMAGES)) {
    if (!known.has(slug)) {
      problems.push(`${slug}: matches no current page (slug probably changed)`);
    }
    if (!existsSync(join(process.cwd(), "public", img.src.replace(/^\//, "")))) {
      problems.push(`${slug}: file not found at public${img.src}`);
    }
    if (!img.alt?.trim()) {
      problems.push(`${slug}: missing alt text`);
    }
  }

  if (problems.length) {
    console.warn(
      `[images] ${problems.length} problem(s) — these publish a broken image or a ` +
        `structured-data reference to a 404:\n` +
        problems.map((p) => `  - ${p}`).join("\n")
    );
  }
  return problems;
}
