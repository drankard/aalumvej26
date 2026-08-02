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
// To register one by hand: put the file in src/assets/steder/, `import` it at
// the top of this file, and add an entry below with alt text describing what is
// actually in the photo. Importing rather than referencing a public/ path is
// what routes it through astro:assets, so it is served responsively and as
// WebP/AVIF rather than at whatever size the photographer's camera produced.

import { SITE } from "./site";

export interface PageImage {
  /** An imported image — `import x from "../assets/steder/foo.jpg"`. */
  img: ImageMetadata;
  /** What is actually in the photo, in Danish. */
  alt: string;
}

/** Keyed by page slug — the last path segment of the URL. */
export const PAGE_IMAGES: Record<string, PageImage> = {
  // "lodbjerg-fyr-klatr-op-i-fyret-og-drik-kaffe-i-den-gamle-fyrm": {
  //   img: lodbjergFyr,
  //   alt: "Lodbjerg Fyr set fra klitheden en klar eftermiddag",
  // },
};

export const pageImage = (slug: string): PageImage | undefined => PAGE_IMAGES[slug];

/** Absolute URL for og:image / schema.org, which both require one. */
export const absoluteImage = (src: string): string => `${SITE}${src}`;

/**
 * Warn about entries whose slug matches no page, or that carry no alt text.
 *
 * Both fail silently otherwise: an orphaned entry means a page that should show
 * a photo quietly stops showing one. Warn rather than throw — a missing photo
 * must not fail a deploy. A missing *file* no longer needs checking here: the
 * entry is an `import`, so a bad path is a build error rather than a live <img>
 * pointing at a 404.
 */
export function warnBrokenImages(knownSlugs: Iterable<string>): string[] {
  const known = new Set(knownSlugs);
  const problems: string[] = [];

  for (const [slug, img] of Object.entries(PAGE_IMAGES)) {
    if (!known.has(slug)) {
      problems.push(`${slug}: matches no current page (slug probably changed)`);
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
