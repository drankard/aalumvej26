import type { APIRoute } from "astro";
import { getContent } from "../lib/content";
import { LANGS, loc } from "../lib/i18n";
import { publishableFacts } from "../lib/facts";
import { stripMarkdown } from "../lib/markdown";
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
    if (p.event_start) {
      lines.push(`- dates: ${p.event_start}${p.event_end ? ` .. ${p.event_end}` : ""}`);
    }
    for (const lang of LANGS) {
      const tr = (p.translations[lang] ?? p.translations["da"] ?? {}) as PostTranslation;
      const tags = loc(lang).tags as Record<string, string>;
      lines.push(`- [${lang}] ${tr.title ?? ""} — ${tags[p.tag_key] ?? p.tag_key} — ${tr.tldr || tr.excerpt || ""}`);
    }
    // Facts and long copy only in Danish: the depth is identical across locales
    // and tripling it would bloat the dump without adding information.
    const da = (p.translations["da"] ?? {}) as PostTranslation;
    for (const f of publishableFacts(da.facts)) lines.push(`- fact: ${f.label}: ${f.value}`);
    if (da.body) lines.push(``, stripMarkdown(da.body));
    for (const q of da.faq ?? []) lines.push(`- Q: ${q.question} A: ${q.answer}`);
    if (da.from_house) lines.push(`- from the house: ${da.from_house}`);
    if (p.url) lines.push(`- source: ${p.url}`);
    lines.push(`- updated: ${p.updated_at.slice(0, 10)}`);
  }

  lines.push(``, `## Area`);
  for (const a of areas) {
    lines.push(``, `### ${SITE}/omraadet/${areaSlugs.get(a.id)}/`);
    for (const lang of LANGS) {
      const tr = (a.translations[lang] ?? a.translations["da"] ?? {}) as AreaTranslation;
      lines.push(`- [${lang}] ${tr.name ?? ""}${tr.dist ? ` (${tr.dist})` : ""} — ${tr.desc ?? ""}`);
    }
    const da = (a.translations["da"] ?? {}) as AreaTranslation;
    for (const f of publishableFacts(da.facts)) lines.push(`- fact: ${f.label}: ${f.value}`);
    if (da.body) lines.push(``, stripMarkdown(da.body));
    for (const q of da.faq ?? []) lines.push(`- Q: ${q.question} A: ${q.answer}`);
    if (a.url) lines.push(`- source: ${a.url}`);
    lines.push(`- updated: ${a.updated_at.slice(0, 10)}`);
  }

  return new Response(lines.join("\n") + "\n", {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
};
