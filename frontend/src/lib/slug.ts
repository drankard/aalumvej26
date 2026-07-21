// URL slug generation.
//
// PARITY-CRITICAL: this algorithm must stay byte-identical to the original
// generator that produced the live URLs (scripts/prerender.mjs in the first
// SEO release). Changing it moves every published content URL and churns
// search indexing. Covered by the assertions in scripts/slug-parity.mjs.

export function slugify(s: unknown): string {
  const out = String(s ?? "")
    .toLowerCase()
    .replace(/æ/g, "ae")
    .replace(/ø/g, "oe")
    .replace(/å/g, "aa")
    .replace(/ä/g, "ae")
    .replace(/ö/g, "oe")
    .replace(/ü/g, "ue")
    .replace(/ß/g, "ss")
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
  return out.replace(/-+$/, "");
}

interface Sluggable {
  id: string;
  translations: Record<string, { title?: string; name?: string }>;
}

export function buildSlugMap(items: Sluggable[]): Map<string, string> {
  const map = new Map<string, string>();
  const used = new Set<string>();
  for (const it of items) {
    const da = it.translations["da"] ?? Object.values(it.translations)[0] ?? {};
    const base = slugify(da.title || da.name) || `id-${String(it.id).slice(0, 8)}`;
    let slug = base;
    let n = 2;
    while (used.has(slug)) slug = `${base}-${n++}`;
    used.add(slug);
    map.set(it.id, slug);
  }
  return map;
}
