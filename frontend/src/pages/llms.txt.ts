import type { APIRoute } from "astro";
import { getContent } from "../lib/content";
import { pickTr } from "../lib/i18n";
import { BOOKING, SITE } from "../lib/site";
import type { AreaTranslation, PostTranslation } from "../lib/types";
import daLocale from "../i18n/locales/da.json";

export const GET: APIRoute = async () => {
  const { posts, areas, postSlugs, areaSlugs } = await getContent();
  const tags = daLocale.tags as Record<string, string>;

  const body = `# Ålumvej 26

> Charmerende stråtækt feriehus 200 m fra Vesterhavet i Agger, Nationalpark Thy, Danmark. Trilingual (da/en/de) guide to experiences and the surrounding area on the Danish west coast, plus booking of the holiday house.

- Location: Ålumvej 26, 7770 Vestervig · Agger · Nationalpark Thy · Denmark
- Booking: ${BOOKING}
- Canonical site: ${SITE}/
- Full content dump: ${SITE}/llms-full.txt

## Oplevelser (experiences)
${posts
  .map((p) => {
    const tr = pickTr<PostTranslation>(p.translations, "da");
    const tag = tags[p.tag_key] ?? p.tag_key;
    return `- [${tr.title}](${SITE}/oplevelser/${postSlugs.get(p.id)}/): ${tag}${tr.date ? " · " + tr.date : ""} — ${(tr.excerpt || "").slice(0, 160)}`;
  })
  .join("\n")}

## Området (the area)
${areas
  .map((a) => {
    const tr = pickTr<AreaTranslation>(a.translations, "da");
    return `- [${tr.name}](${SITE}/omraadet/${areaSlugs.get(a.id)}/): ${tr.dist ? tr.dist + " — " : ""}${(tr.desc || "").slice(0, 160)}`;
  })
  .join("\n")}
`;

  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
