// Build-time content loading.
//
// Sources, in order:
//   1. PRERENDER_CONTENT_FILE — a JSON snapshot ({posts, areas, categories,
//      archivedPosts?}) for offline/fixture builds and tests.
//   2. The backend RPC API at VITE_API_URL (list_content + list_archived_posts).
//   3. Empty content — the build must never fail because the API is down;
//      it degrades to the house-only site and logs loudly.
//
// The result is cached module-level: every page's getStaticPaths shares one
// fetch per build.

import { readFileSync, existsSync } from "node:fs";
import { buildSlugMap } from "./slug";
import type { Area, Category, Post, SiteContent } from "./types";

const API_URL = (
  process.env.VITE_API_URL ||
  import.meta.env.VITE_API_URL ||
  ""
).replace(/\/+$/, "");

async function rpc<T>(action: string): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 20000);
  try {
    const res = await fetch(`${API_URL}/rpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload: {} }),
      signal: ctrl.signal,
    });
    const json = (await res.json()) as { success: boolean; data: T; error: string | null };
    if (!json.success) throw new Error(json.error || "unknown RPC error");
    return json.data;
  } finally {
    clearTimeout(timer);
  }
}

interface RawContent {
  posts?: Post[];
  areas?: Area[];
  categories?: Category[];
  archivedPosts?: Post[];
}

async function load(): Promise<SiteContent> {
  let raw: RawContent = {};

  const fixture = process.env.PRERENDER_CONTENT_FILE;
  if (fixture && existsSync(fixture)) {
    raw = JSON.parse(readFileSync(fixture, "utf8")) as RawContent;
    console.log(`[content] loaded fixture ${fixture}`);
  } else if (API_URL) {
    try {
      raw = await rpc<RawContent>("list_content");
      console.log(`[content] loaded from API ${API_URL}`);
      try {
        raw.archivedPosts = await rpc<Post[]>("list_archived_posts");
      } catch (e) {
        console.warn(`[content] archive fetch failed (non-fatal): ${(e as Error).message}`);
      }
    } catch (e) {
      console.error(
        `[content] !!! API fetch failed (${(e as Error).message}) — building WITHOUT dynamic content`
      );
    }
  } else {
    console.warn("[content] no VITE_API_URL and no fixture — building WITHOUT dynamic content");
  }

  const published = (items: Post[] | Area[] | undefined) =>
    (items ?? []).filter((i) => (i.status || "published") === "published");

  const posts = (published(raw.posts) as Post[]).sort((a, b) => a.sort_order - b.sort_order);
  const areas = (published(raw.areas) as Area[]).sort((a, b) => a.sort_order - b.sort_order);
  const categories = (raw.categories ?? []).sort((a, b) => a.sort_order - b.sort_order);
  const archivedPosts = (raw.archivedPosts ?? []).filter((p) => p.status === "archived");

  return {
    posts,
    areas,
    categories,
    archivedPosts,
    postSlugs: buildSlugMap(posts),
    areaSlugs: buildSlugMap(areas),
  };
}

let cache: Promise<SiteContent> | undefined;

export function getContent(): Promise<SiteContent> {
  cache ??= load();
  return cache;
}
