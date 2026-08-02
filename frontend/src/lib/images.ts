// Per-page photography — CURRENTLY UNUSED, and that is the intended state.
//
// PAGE_IMAGES is empty, so no page emits a hero image or a schema.org `image`.
// That is correct rather than a gap: asserting an image in structured data is a
// claim that the picture depicts that subject, and we hold no photographs of
// these places. Every experience page used to declare the cottage's exterior as
// its image, which was simply false; that claim was removed, not replaced.
//
// Images are NOT discovered by the content pipeline, deliberately. The pipeline
// crawls tourism boards, museums and restaurants — their photographs are theirs.
// Copying or hotlinking them, and then declaring one as this site's `image`,
// would automate a copyright infringement. An og:image tag lets other sites show
// a link preview; it is not a licence to republish.
//
// The mechanism below is kept because it is correct and costs nothing while
// empty. If images are ever wanted, the legitimate automatable source is
// Wikimedia Commons — CC/public-domain, queryable by name and coordinates,
// republishable with visible attribution. Coverage would reach the evergreen
// landmarks and miss events and small businesses, which is the right split
// anyway.
//
// To register one by hand: upload to public/images/steder/ and add an entry
// below with alt text describing what is actually in the photo.

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
