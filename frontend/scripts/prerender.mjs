// Post-build static prerender / SEO generator.
//
// Runs after `vite build` (see package.json). The built SPA ships an empty
// <div id="root">, which AI crawlers/indexers (GPTBot, ClaudeBot, PerplexityBot,
// OAI-SearchBot, …) cannot see because they do not execute JavaScript. This
// script bakes the real content into static HTML so those crawlers — and classic
// search engines — can discover and cite it, without touching the live SPA UX:
//
//   • injects a hidden, crawlable content block + ItemList JSON-LD into dist/index.html
//   • emits real per-experience / per-area landing pages (da + /en/ + /de/)
//   • emits section index pages (/oplevelser/, /omraadet/)
//   • rewrites dist/sitemap.xml with every URL + hreflang alternates
//   • writes /llms.txt (concise) and /llms-full.txt (full dump) for LLM ingestion
//
// Content source (in order): PRERENDER_CONTENT_FILE → the live RPC API
// (VITE_API_URL). If neither is reachable the build still succeeds — it just
// emits the shell + house content rather than failing the deploy.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const DIST = join(ROOT, "dist");
const LOCALES = join(ROOT, "src", "i18n", "locales");

const SITE = (process.env.PRERENDER_SITE_URL || "https://www.aalumvej26.dk").replace(/\/+$/, "");
const API_URL = (process.env.VITE_API_URL || "").replace(/\/+$/, "");
const CONTENT_FILE = process.env.PRERENDER_CONTENT_FILE || "";
const LANGS = ["da", "en", "de"];
const DEFAULT_LANG = "da";
const OG_LOCALE = { da: "da_DK", en: "en_GB", de: "de_DE" };
const OG_IMAGE = `${SITE}/images/house/01-exterior.jpg`;
const BOOKING = "https://www.aggerferiehuse.dk/dk/agger/lille-feriehus-med-sjael-og-charme";

const log = (...a) => console.log("[prerender]", ...a);

// ---------------------------------------------------------------- locale copy
function loadLocale(lang) {
  try {
    return JSON.parse(readFileSync(join(LOCALES, `${lang}.json`), "utf8"));
  } catch {
    return {};
  }
}
const L = Object.fromEntries(LANGS.map((l) => [l, loadLocale(l)]));

// UI strings per language, with da fallbacks so a missing key never breaks a page.
const UI = {
  da: {
    experiences: "Oplevelser", area: "Området", house: "Huset", book: "Book huset",
    backHome: "Til forsiden", allExperiences: "Alle oplevelser", allAreas: "Hele området",
    readMore: "Læs mere hos kilden", relatedSource: "Kilder", distance: "Afstand",
    nearby: "Feriehus i nærheden", intro: "Din guide til Nationalpark Thy og Vestkysten.",
    otherLangs: "Andre sprog",
  },
  en: {
    experiences: "Experiences", area: "The area", house: "The house", book: "Book the house",
    backHome: "Back to home", allExperiences: "All experiences", allAreas: "The whole area",
    readMore: "Read more at the source", relatedSource: "Sources", distance: "Distance",
    nearby: "Holiday house nearby", intro: "Your guide to Nationalpark Thy and the west coast.",
    otherLangs: "Other languages",
  },
  de: {
    experiences: "Erlebnisse", area: "Die Umgebung", house: "Das Haus", book: "Haus buchen",
    backHome: "Zur Startseite", allExperiences: "Alle Erlebnisse", allAreas: "Die ganze Umgebung",
    readMore: "Mehr bei der Quelle", relatedSource: "Quellen", distance: "Entfernung",
    nearby: "Ferienhaus in der Nähe", intro: "Dein Guide für den Nationalpark Thy und die Westküste.",
    otherLangs: "Andere Sprachen",
  },
};
const ui = (lang, key) => (UI[lang] && UI[lang][key]) || UI.da[key] || key;

// ---------------------------------------------------------------- helpers
function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function slugify(s) {
  const out = String(s ?? "")
    .toLowerCase()
    .replace(/æ/g, "ae").replace(/ø/g, "oe").replace(/å/g, "aa")
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
  return out.replace(/-+$/, "");
}
function pickTr(translations, lang) {
  if (!translations || typeof translations !== "object") return {};
  return translations[lang] || translations[DEFAULT_LANG] || Object.values(translations)[0] || {};
}
const langPrefix = (lang) => (lang === DEFAULT_LANG ? "" : `/${lang}`);
const abs = (path) => `${SITE}${path}`;

function writePage(relDir, html) {
  const dir = join(DIST, relDir);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), html, "utf8");
}

// ---------------------------------------------------------------- content load
async function loadContent() {
  if (CONTENT_FILE && existsSync(CONTENT_FILE)) {
    try {
      const data = JSON.parse(readFileSync(CONTENT_FILE, "utf8"));
      log("content: PRERENDER_CONTENT_FILE", CONTENT_FILE);
      return data;
    } catch (e) {
      log("content file unreadable:", e.message);
    }
  }
  if (API_URL) {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 15000);
      const res = await fetch(`${API_URL}/rpc`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list_content", payload: {} }),
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      const json = await res.json();
      if (json && json.success && json.data) {
        log("content: fetched from API", API_URL);
        return json.data;
      }
      log("content: API returned no data:", (json && json.error) || "unknown");
    } catch (e) {
      log("content: API fetch failed:", e.message);
    }
  }
  log("content: no source reachable — emitting shell + house only");
  return { posts: [], areas: [], categories: [] };
}

// ---------------------------------------------------------------- slug maps
function buildSlugMap(items) {
  const map = new Map(); // id -> slug
  const used = new Set();
  for (const it of items) {
    const base = slugify(pickTr(it.translations, DEFAULT_LANG).title || pickTr(it.translations, DEFAULT_LANG).name) || `id-${String(it.id).slice(0, 8)}`;
    let slug = base;
    let n = 2;
    while (used.has(slug)) slug = `${base}-${n++}`;
    used.add(slug);
    map.set(it.id, slug);
  }
  return map;
}

// ---------------------------------------------------------------- page shell
function renderShell({ lang, title, description, canonicalPath, alternates, jsonLd, breadcrumbHtml, bodyHtml, robots }) {
  const altLinks = (alternates || [])
    .map((a) => `    <link rel="alternate" hreflang="${a.lang}" href="${escapeHtml(a.href)}" />`)
    .concat(alternates && alternates.length ? [`    <link rel="alternate" hreflang="x-default" href="${escapeHtml(alternates.find((a) => a.lang === DEFAULT_LANG)?.href || abs(canonicalPath))}" />`] : [])
    .join("\n");
  const ld = (jsonLd || [])
    .map((obj) => `    <script type="application/ld+json">\n${JSON.stringify(obj, null, 2)}\n    </script>`)
    .join("\n");
  return `<!DOCTYPE html>
<html lang="${lang}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(title)}</title>
    <meta name="description" content="${escapeHtml(description)}" />
    <meta name="robots" content="${robots || "index, follow, max-image-preview:large"}" />
    <link rel="canonical" href="${escapeHtml(abs(canonicalPath))}" />
${altLinks}
    <meta property="og:type" content="article" />
    <meta property="og:title" content="${escapeHtml(title)}" />
    <meta property="og:description" content="${escapeHtml(description)}" />
    <meta property="og:url" content="${escapeHtml(abs(canonicalPath))}" />
    <meta property="og:image" content="${OG_IMAGE}" />
    <meta property="og:locale" content="${OG_LOCALE[lang] || "da_DK"}" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <style>
      :root { --foam:#F5F0E8; --deep:#2C3E50; --storm:#3D4F5F; --rust:#B8624C; --sea:#5A7A8A; --driftwood:#8B7355; --cloud:#E8E2D6; }
      * { margin:0; padding:0; box-sizing:border-box; }
      body { background:var(--foam); color:var(--storm); font-family:'DM Sans',system-ui,-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.65; }
      a { color:var(--rust); }
      header.site { background:var(--deep); padding:14px 22px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
      header.site .brand { color:var(--foam); font-family:'Playfair Display',Georgia,serif; letter-spacing:0.08em; font-size:17px; text-decoration:none; }
      header.site .book { background:var(--rust); color:var(--foam); padding:8px 16px; border-radius:6px; text-decoration:none; font-size:13px; font-weight:600; }
      main { max-width:820px; margin:0 auto; padding:32px 22px 64px; }
      nav.crumbs { font-size:13px; color:var(--driftwood); margin-bottom:22px; }
      nav.crumbs a { color:var(--driftwood); }
      h1 { font-family:'Playfair Display',Georgia,serif; font-weight:500; color:var(--deep); font-size:clamp(26px,4vw,40px); line-height:1.15; margin-bottom:14px; }
      h2 { font-family:'Playfair Display',Georgia,serif; font-weight:500; color:var(--deep); font-size:24px; margin:32px 0 12px; }
      .meta { font-size:12px; letter-spacing:0.06em; text-transform:uppercase; color:var(--rust); margin-bottom:18px; }
      .tag { display:inline-block; background:var(--sea); color:#fff; padding:2px 10px; border-radius:4px; font-size:11px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; }
      p { margin:0 0 16px; }
      ul.cards { list-style:none; display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:16px; margin:24px 0; }
      ul.cards li { background:#fff; border:1px solid rgba(212,197,169,0.4); border-radius:12px; padding:18px 20px; }
      ul.cards h3 { font-family:'Playfair Display',Georgia,serif; font-weight:500; color:var(--deep); font-size:18px; margin-bottom:6px; }
      ul.cards h3 a { color:var(--deep); text-decoration:none; }
      ul.cards p { font-size:13px; opacity:0.8; margin:0; }
      .cta { display:inline-block; background:var(--deep); color:var(--foam); padding:12px 22px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px; margin-top:8px; }
      .langs { font-size:12px; color:var(--driftwood); margin-top:36px; }
      .langs a { margin-right:12px; }
      footer.site { background:var(--deep); color:rgba(245,240,232,0.6); font-size:12px; padding:28px 22px; text-align:center; }
      footer.site a { color:var(--foam); }
    </style>
${ld}
  </head>
  <body>
    <header class="site">
      <a class="brand" href="${langPrefix(lang) || "/"}">ÅLUMVEJ 26</a>
      <a class="book" href="${BOOKING}" target="_blank" rel="noopener">${escapeHtml(ui(lang, "book"))}</a>
    </header>
    <main>
${breadcrumbHtml || ""}
${bodyHtml}
    </main>
    <footer class="site">
      <p>Ålumvej 26 · 7770 Vestervig · Agger, Nationalpark Thy — <a href="${SITE}/">aalumvej26.dk</a></p>
    </footer>
  </body>
</html>
`;
}

function crumbs(lang, trail) {
  const parts = [`<a href="${langPrefix(lang) || "/"}">${escapeHtml(ui(lang, "backHome"))}</a>`]
    .concat(trail.map((t) => (t.href ? `<a href="${escapeHtml(t.href)}">${escapeHtml(t.label)}</a>` : escapeHtml(t.label))));
  return `      <nav class="crumbs">${parts.join(" › ")}</nav>`;
}

// ---------------------------------------------------------------- main
async function main() {
  if (!existsSync(join(DIST, "index.html"))) {
    log("dist/index.html missing — run `vite build` first. Skipping.");
    return;
  }
  const content = await loadContent();
  const posts = (content.posts || []).filter((p) => (p.status || "published") === "published");
  const areas = (content.areas || []).filter((a) => (a.status || "published") === "published");
  const categories = content.categories || [];

  const postSlugs = buildSlugMap(posts);
  const areaSlugs = buildSlugMap(areas);
  const catLabel = (id, lang) => {
    const c = categories.find((c) => c.id === id);
    return c ? (pickTr(c.translations, lang).label || id) : id;
  };
  const tagLabel = (key, lang) => (L[lang]?.tags?.[key] || L.da?.tags?.[key] || key);

  const sitemap = []; // { path, alternates:[{lang,href}] }
  const addSitemap = (basePathFor) => {
    const alternates = LANGS.map((lang) => ({ lang, href: abs(basePathFor(lang)) }));
    for (const lang of LANGS) sitemap.push({ path: basePathFor(lang), alternates });
  };

  // ---- experience detail + index pages
  for (const lang of LANGS) {
    for (const post of posts) {
      const tr = pickTr(post.translations, lang);
      const slug = postSlugs.get(post.id);
      const path = `${langPrefix(lang)}/oplevelser/${slug}/`;
      const title = `${tr.title || slug} — ${ui(lang, "experiences")} · Nationalpark Thy`;
      const description = (tr.excerpt || tr.title || "").slice(0, 300);
      const sources = [post.url, ...(post.source_urls || [])].filter(Boolean);
      const sourceLinks = sources.length
        ? `<h2>${escapeHtml(ui(lang, "relatedSource"))}</h2>\n<ul>${[...new Set(sources)].map((u) => `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener nofollow">${escapeHtml(u)}</a></li>`).join("")}</ul>`
        : "";
      const body = `      <p class="meta">${escapeHtml(ui(lang, "experiences"))}${tr.date ? " · " + escapeHtml(tr.date) : ""}</p>
      <span class="tag">${escapeHtml(tagLabel(post.tag_key, lang))}</span>
      <h1>${escapeHtml(post.emoji ? post.emoji + " " : "")}${escapeHtml(tr.title || slug)}</h1>
      <p>${escapeHtml(tr.excerpt || "")}</p>
      ${post.url ? `<p><a class="cta" href="${escapeHtml(post.url)}" target="_blank" rel="noopener nofollow">${escapeHtml(ui(lang, "readMore"))} →</a></p>` : ""}
      ${sourceLinks}
      <h2>${escapeHtml(ui(lang, "nearby"))}</h2>
      <p>${escapeHtml(L[lang]?.house?.description || L.da.house.description || "")}</p>
      <p><a class="cta" href="${BOOKING}" target="_blank" rel="noopener">${escapeHtml(ui(lang, "book"))} →</a></p>
      <p class="langs">${escapeHtml(ui(lang, "otherLangs"))}: ${LANGS.filter((x) => x !== lang).map((x) => `<a href="${langPrefix(x)}/oplevelser/${slug}/">${x.toUpperCase()}</a>`).join(" ")}</p>`;
      const jsonLd = [{
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        name: tr.title || slug,
        description: tr.excerpt || "",
        url: abs(path),
        image: OG_IMAGE,
        isAccessibleForFree: true,
        touristType: catLabel(post.category, lang),
        containedInPlace: { "@type": "Place", name: "Nationalpark Thy" },
      }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: ui(lang, "backHome"), item: abs(`${langPrefix(lang)}/`) },
          { "@type": "ListItem", position: 2, name: ui(lang, "experiences"), item: abs(`${langPrefix(lang)}/oplevelser/`) },
          { "@type": "ListItem", position: 3, name: tr.title || slug, item: abs(path) },
        ],
      }];
      writePage(path, renderShell({
        lang, title, description, canonicalPath: path,
        alternates: LANGS.map((x) => ({ lang: x, href: abs(`${langPrefix(x)}/oplevelser/${slug}/`) })),
        jsonLd,
        breadcrumbHtml: crumbs(lang, [{ label: ui(lang, "experiences"), href: `${langPrefix(lang)}/oplevelser/` }, { label: tr.title || slug }]),
        bodyHtml: body,
      }));
    }

    // experiences index
    const idxPath = `${langPrefix(lang)}/oplevelser/`;
    const cards = posts.map((post) => {
      const tr = pickTr(post.translations, lang);
      const slug = postSlugs.get(post.id);
      return `        <li><span class="tag">${escapeHtml(tagLabel(post.tag_key, lang))}</span>
          <h3><a href="${langPrefix(lang)}/oplevelser/${slug}/">${escapeHtml(post.emoji ? post.emoji + " " : "")}${escapeHtml(tr.title || slug)}</a></h3>
          <p>${escapeHtml((tr.excerpt || "").slice(0, 160))}</p></li>`;
    }).join("\n");
    const idxBody = `      <h1>${escapeHtml(ui(lang, "allExperiences"))}</h1>
      <p>${escapeHtml(ui(lang, "intro"))}</p>
      <ul class="cards">
${cards || "        <li><p>—</p></li>"}
      </ul>`;
    writePage(idxPath, renderShell({
      lang,
      title: `${ui(lang, "allExperiences")} — Ålumvej 26, Agger · Nationalpark Thy`,
      description: `${ui(lang, "allExperiences")}: ${ui(lang, "intro")}`,
      canonicalPath: idxPath,
      alternates: LANGS.map((x) => ({ lang: x, href: abs(`${langPrefix(x)}/oplevelser/`) })),
      jsonLd: [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: ui(lang, "allExperiences"),
        itemListElement: posts.map((post, i) => ({
          "@type": "ListItem", position: i + 1,
          name: pickTr(post.translations, lang).title || postSlugs.get(post.id),
          url: abs(`${langPrefix(lang)}/oplevelser/${postSlugs.get(post.id)}/`),
        })),
      }],
      breadcrumbHtml: crumbs(lang, [{ label: ui(lang, "experiences") }]),
      bodyHtml: idxBody,
    }));

    // ---- area detail pages
    for (const area of areas) {
      const tr = pickTr(area.translations, lang);
      const slug = areaSlugs.get(area.id);
      const path = `${langPrefix(lang)}/omraadet/${slug}/`;
      const title = `${tr.name || slug} — ${ui(lang, "area")} · Agger, Thy`;
      const description = (tr.desc || tr.name || "").slice(0, 300);
      const body = `      <p class="meta">${escapeHtml(ui(lang, "area"))}${tr.dist ? " · " + escapeHtml(ui(lang, "distance")) + ": " + escapeHtml(tr.dist) : ""}</p>
      <h1>${escapeHtml(tr.name || slug)}</h1>
      <p>${escapeHtml(tr.desc || "")}</p>
      ${area.url ? `<p><a class="cta" href="${escapeHtml(area.url)}" target="_blank" rel="noopener nofollow">${escapeHtml(ui(lang, "readMore"))} →</a></p>` : ""}
      <h2>${escapeHtml(ui(lang, "nearby"))}</h2>
      <p>${escapeHtml(L[lang]?.house?.description || L.da.house.description || "")}</p>
      <p><a class="cta" href="${BOOKING}" target="_blank" rel="noopener">${escapeHtml(ui(lang, "book"))} →</a></p>
      <p class="langs">${escapeHtml(ui(lang, "otherLangs"))}: ${LANGS.filter((x) => x !== lang).map((x) => `<a href="${langPrefix(x)}/omraadet/${slug}/">${x.toUpperCase()}</a>`).join(" ")}</p>`;
      const jsonLd = [{
        "@context": "https://schema.org",
        "@type": "TouristAttraction",
        name: tr.name || slug,
        description: tr.desc || "",
        url: abs(path),
        image: OG_IMAGE,
        containedInPlace: { "@type": "Place", name: "Nationalpark Thy" },
      }];
      writePage(path, renderShell({
        lang, title, description, canonicalPath: path,
        alternates: LANGS.map((x) => ({ lang: x, href: abs(`${langPrefix(x)}/omraadet/${slug}/`) })),
        jsonLd,
        breadcrumbHtml: crumbs(lang, [{ label: ui(lang, "area"), href: `${langPrefix(lang)}/omraadet/` }, { label: tr.name || slug }]),
        bodyHtml: body,
      }));
    }

    // area index
    const areaIdxPath = `${langPrefix(lang)}/omraadet/`;
    const areaCards = areas.map((area) => {
      const tr = pickTr(area.translations, lang);
      const slug = areaSlugs.get(area.id);
      return `        <li>${tr.dist ? `<span class="tag">${escapeHtml(tr.dist)}</span>` : ""}
          <h3><a href="${langPrefix(lang)}/omraadet/${slug}/">${escapeHtml(tr.name || slug)}</a></h3>
          <p>${escapeHtml((tr.desc || "").slice(0, 160))}</p></li>`;
    }).join("\n");
    writePage(areaIdxPath, renderShell({
      lang,
      title: `${ui(lang, "allAreas")} — Ålumvej 26, Agger · Nationalpark Thy`,
      description: `${ui(lang, "allAreas")}: ${ui(lang, "intro")}`,
      canonicalPath: areaIdxPath,
      alternates: LANGS.map((x) => ({ lang: x, href: abs(`${langPrefix(x)}/omraadet/`) })),
      jsonLd: [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: ui(lang, "allAreas"),
        itemListElement: areas.map((area, i) => ({
          "@type": "ListItem", position: i + 1,
          name: pickTr(area.translations, lang).name || areaSlugs.get(area.id),
          url: abs(`${langPrefix(lang)}/omraadet/${areaSlugs.get(area.id)}/`),
        })),
      }],
      breadcrumbHtml: crumbs(lang, [{ label: ui(lang, "area") }]),
      bodyHtml: `      <h1>${escapeHtml(ui(lang, "allAreas"))}</h1>
      <p>${escapeHtml(ui(lang, "intro"))}</p>
      <ul class="cards">
${areaCards || "        <li><p>—</p></li>"}
      </ul>`,
    }));
  }

  // ---- sitemap entries
  addSitemap((lang) => `${langPrefix(lang)}/oplevelser/`);
  addSitemap((lang) => `${langPrefix(lang)}/omraadet/`);
  for (const post of posts) addSitemap((lang) => `${langPrefix(lang)}/oplevelser/${postSlugs.get(post.id)}/`);
  for (const area of areas) addSitemap((lang) => `${langPrefix(lang)}/omraadet/${areaSlugs.get(area.id)}/`);

  // ---- inject crawlable block + ItemList JSON-LD into the home shell
  injectHome({ posts, areas, postSlugs, areaSlugs, tagLabel });

  // ---- sitemap.xml (home keeps the existing ?lang= alternate scheme)
  writeSitemap(sitemap);

  // ---- llms.txt / llms-full.txt
  writeLlms({ posts, areas, postSlugs, areaSlugs, tagLabel, catLabel });

  log(`done: ${posts.length} experiences, ${areas.length} areas, ${sitemap.length + 1} sitemap urls`);
}

// ---------------------------------------------------------------- home inject
function injectHome({ posts, areas, postSlugs, areaSlugs, tagLabel }) {
  const file = join(DIST, "index.html");
  let html = readFileSync(file, "utf8");
  if (html.includes('id="seo-index"')) return; // idempotent

  const houseD = L.da.house || {};
  const expItems = posts.map((post) => {
    const tr = pickTr(post.translations, "da");
    const slug = postSlugs.get(post.id);
    return `        <li><a href="/oplevelser/${slug}/">${escapeHtml(tr.title || slug)}</a> — <span>${escapeHtml(tagLabel(post.tag_key, "da"))}${tr.date ? " · " + escapeHtml(tr.date) : ""}</span>. ${escapeHtml((tr.excerpt || "").slice(0, 200))}</li>`;
  }).join("\n");
  const areaItems = areas.map((area) => {
    const tr = pickTr(area.translations, "da");
    const slug = areaSlugs.get(area.id);
    return `        <li><a href="/omraadet/${slug}/">${escapeHtml(tr.name || slug)}</a>${tr.dist ? " (" + escapeHtml(tr.dist) + ")" : ""} — ${escapeHtml((tr.desc || "").slice(0, 200))}</li>`;
  }).join("\n");

  const block = `    <div id="seo-index" hidden aria-hidden="true">
      <h1>Ålumvej 26 — stråtækt feriehus i Agger, Nationalpark Thy</h1>
      <p>${escapeHtml(houseD.description || "")}</p>
      <p>${escapeHtml((L.da.features || []).join(" · "))}</p>
      <h2>Oplevelser i Thy &amp; omegn</h2>
      <ul>
${expItems || "        <li>—</li>"}
      </ul>
      <h2>Området omkring feriehuset</h2>
      <ul>
${areaItems || "        <li>—</li>"}
      </ul>
      <p><a href="/oplevelser/">Alle oplevelser</a> · <a href="/omraadet/">Hele området</a> · <a href="/llms.txt">llms.txt</a></p>
    </div>
  </body>`;
  html = html.replace("</body>", block);

  // ItemList JSON-LD so indexers see the full content list on the home URL too.
  const itemList = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Oplevelser & område — Ålumvej 26",
    itemListElement: [
      ...posts.map((post, i) => ({
        "@type": "ListItem", position: i + 1,
        name: pickTr(post.translations, "da").title || postSlugs.get(post.id),
        url: abs(`/oplevelser/${postSlugs.get(post.id)}/`),
      })),
      ...areas.map((area, i) => ({
        "@type": "ListItem", position: posts.length + i + 1,
        name: pickTr(area.translations, "da").name || areaSlugs.get(area.id),
        url: abs(`/omraadet/${areaSlugs.get(area.id)}/`),
      })),
    ],
  };
  html = html.replace("</head>", `    <script type="application/ld+json">\n${JSON.stringify(itemList, null, 2)}\n    </script>\n  </head>`);

  writeFileSync(file, html, "utf8");
  log("home: injected crawlable block + ItemList JSON-LD");
}

// ---------------------------------------------------------------- sitemap
function writeSitemap(entries) {
  const homeAlt = [
    `    <xhtml:link rel="alternate" hreflang="da" href="${SITE}/" />`,
    `    <xhtml:link rel="alternate" hreflang="en" href="${SITE}/?lang=en" />`,
    `    <xhtml:link rel="alternate" hreflang="de" href="${SITE}/?lang=de" />`,
    `    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE}/" />`,
  ].join("\n");
  const urls = [
    `  <url>\n    <loc>${SITE}/</loc>\n${homeAlt}\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>`,
  ];
  for (const e of entries) {
    const alt = e.alternates
      .map((a) => `    <xhtml:link rel="alternate" hreflang="${a.lang}" href="${escapeHtml(a.href)}" />`)
      .concat([`    <xhtml:link rel="alternate" hreflang="x-default" href="${escapeHtml(e.alternates.find((a) => a.lang === DEFAULT_LANG)?.href || abs(e.path))}" />`])
      .join("\n");
    urls.push(`  <url>\n    <loc>${escapeHtml(abs(e.path))}</loc>\n${alt}\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>`);
  }
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join("\n")}
</urlset>
`;
  writeFileSync(join(DIST, "sitemap.xml"), xml, "utf8");
  log(`sitemap: ${urls.length} urls`);
}

// ---------------------------------------------------------------- llms.txt
function writeLlms({ posts, areas, postSlugs, areaSlugs, tagLabel, catLabel }) {
  const head = `# Ålumvej 26

> Charmerende stråtækt feriehus 200 m fra Vesterhavet i Agger, Nationalpark Thy, Danmark. Trilingual (da/en/de) guide to experiences and the surrounding area on the Danish west coast, plus booking of the holiday house.

- Location: Ålumvej 26, 7770 Vestervig · Agger · Nationalpark Thy · Denmark
- Booking: ${BOOKING}
- Canonical site: ${SITE}/

## Oplevelser (experiences)
${posts.map((p) => {
    const tr = pickTr(p.translations, "da");
    return `- [${tr.title || postSlugs.get(p.id)}](${abs(`/oplevelser/${postSlugs.get(p.id)}/`)}): ${tagLabel(p.tag_key, "da")}${tr.date ? " · " + tr.date : ""} — ${(tr.excerpt || "").slice(0, 160)}`;
  }).join("\n")}

## Området (the area)
${areas.map((a) => {
    const tr = pickTr(a.translations, "da");
    return `- [${tr.name || areaSlugs.get(a.id)}](${abs(`/omraadet/${areaSlugs.get(a.id)}/`)}): ${tr.dist ? tr.dist + " — " : ""}${(tr.desc || "").slice(0, 160)}`;
  }).join("\n")}
`;
  writeFileSync(join(DIST, "llms.txt"), head, "utf8");

  // Full dump: every translation, for ingestion.
  const full = [`# Ålumvej 26 — full content (da/en/de)\n\nSource: ${SITE}/\nBooking: ${BOOKING}\n`];
  full.push(`\n## House\n`);
  for (const lang of LANGS) {
    const h = L[lang]?.house || {};
    full.push(`\n### [${lang}] ${h.heading1 || ""} ${h.heading2 || ""}\n${h.description || ""}\nFeatures: ${(L[lang]?.features || []).join(", ")}\n`);
  }
  full.push(`\n## Experiences\n`);
  for (const p of posts) {
    full.push(`\n### ${abs(`/oplevelser/${postSlugs.get(p.id)}/`)}`);
    for (const lang of LANGS) {
      const tr = pickTr(p.translations, lang);
      full.push(`- [${lang}] ${tr.title || ""} — ${tagLabel(p.tag_key, lang)} — ${tr.excerpt || ""}`);
    }
    if (p.url) full.push(`- source: ${p.url}`);
  }
  full.push(`\n## Area\n`);
  for (const a of areas) {
    full.push(`\n### ${abs(`/omraadet/${areaSlugs.get(a.id)}/`)}`);
    for (const lang of LANGS) {
      const tr = pickTr(a.translations, lang);
      full.push(`- [${lang}] ${tr.name || ""}${tr.dist ? " (" + tr.dist + ")" : ""} — ${tr.desc || ""}`);
    }
    if (a.url) full.push(`- source: ${a.url}`);
  }
  writeFileSync(join(DIST, "llms-full.txt"), full.join("\n") + "\n", "utf8");
  log("llms: wrote llms.txt + llms-full.txt");
}

main().catch((e) => {
  // Never fail the build over SEO generation.
  console.error("[prerender] non-fatal error:", e);
  process.exit(0);
});
