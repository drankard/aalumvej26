import type { APIRoute } from "astro";
import { getContent } from "../lib/content";
import { LANGS, langPrefix } from "../lib/i18n";
import { SITE } from "../lib/site";

interface Entry {
  basePath: string;
  priority: string;
  lastmod?: string;
}

function urlBlock(e: Entry): string {
  return LANGS.map((lang) => {
    const loc = `${SITE}${langPrefix(lang)}${e.basePath}`;
    const alternates = LANGS.map(
      (l) =>
        `    <xhtml:link rel="alternate" hreflang="${l}" href="${SITE}${langPrefix(l)}${e.basePath}" />`
    )
      .concat([
        `    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE}${e.basePath}" />`,
      ])
      .join("\n");
    const lastmod = e.lastmod ? `\n    <lastmod>${e.lastmod.slice(0, 10)}</lastmod>` : "";
    return `  <url>\n    <loc>${loc}</loc>\n${alternates}${lastmod}\n    <changefreq>weekly</changefreq>\n    <priority>${e.priority}</priority>\n  </url>`;
  }).join("\n");
}

export const GET: APIRoute = async () => {
  const { posts, areas, categories, postSlugs, areaSlugs } = await getContent();

  const entries: Entry[] = [
    { basePath: "/", priority: "1.0" },
    { basePath: "/oplevelser/", priority: "0.8" },
    { basePath: "/omraadet/", priority: "0.8" },
    { basePath: "/oplevelser/arkiv/", priority: "0.4" },
    ...categories
      .filter((c) => posts.some((p) => p.category === c.id))
      .map((c) => ({ basePath: `/oplevelser/kategori/${c.id}/`, priority: "0.6" })),
    ...posts.map((p) => ({
      basePath: `/oplevelser/${postSlugs.get(p.id)}/`,
      priority: "0.7",
      lastmod: p.updated_at,
    })),
    ...areas.map((a) => ({
      basePath: `/omraadet/${areaSlugs.get(a.id)}/`,
      priority: "0.7",
      lastmod: a.updated_at,
    })),
  ];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${entries.map(urlBlock).join("\n")}
</urlset>
`;

  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
};
