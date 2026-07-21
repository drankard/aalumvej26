import type { APIRoute } from "astro";
import { getContent } from "../lib/content";
import { LANGS, loc } from "../lib/i18n";
import { BOOKING, SITE } from "../lib/site";
import type { AreaTranslation, PostTranslation } from "../lib/types";

export const GET: APIRoute = async () => {
  const { posts, areas, postSlugs, areaSlugs } = await getContent();

  const lines: string[] = [
    `# Ålumvej 26 — full content (da/en/de)`,
    ``,
    `Source: ${SITE}/`,
    `Booking: ${BOOKING}`,
    ``,
    `## House`,
  ];

  for (const lang of LANGS) {
    const L = loc(lang);
    lines.push(
      ``,
      `### [${lang}] ${L.house.heading1} ${L.house.heading2}`,
      L.house.description,
      `Features: ${L.features.join(", ")}`
    );
  }

  lines.push(``, `## Experiences`);
  for (const p of posts) {
    lines.push(``, `### ${SITE}/oplevelser/${postSlugs.get(p.id)}/`);
    for (const lang of LANGS) {
      const tr = (p.translations[lang] ?? p.translations["da"] ?? {}) as PostTranslation;
      const tags = loc(lang).tags as Record<string, string>;
      lines.push(`- [${lang}] ${tr.title ?? ""} — ${tags[p.tag_key] ?? p.tag_key} — ${tr.excerpt ?? ""}`);
    }
    if (p.url) lines.push(`- source: ${p.url}`);
  }

  lines.push(``, `## Area`);
  for (const a of areas) {
    lines.push(``, `### ${SITE}/omraadet/${areaSlugs.get(a.id)}/`);
    for (const lang of LANGS) {
      const tr = (a.translations[lang] ?? a.translations["da"] ?? {}) as AreaTranslation;
      lines.push(`- [${lang}] ${tr.name ?? ""}${tr.dist ? ` (${tr.dist})` : ""} — ${tr.desc ?? ""}`);
    }
    if (a.url) lines.push(`- source: ${a.url}`);
  }

  return new Response(lines.join("\n") + "\n", {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
};
