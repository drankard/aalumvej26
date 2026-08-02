// Drop image assets the build emits but nothing links to.
//
// site.ts imports each house photo so <Picture> and getImage() can derive
// sized variants from it. Vite treats every one of those imports as a static
// asset and copies the untouched master into _astro/ as well, even though the
// derived variants are what the HTML actually references. That put ~5.6 MB of
// 2400px originals on the CDN that no page, sitemap or JSON-LD ever names.
//
// There is no Astro flag for "emit the derivatives, not the source", so the
// originals are removed after the fact, by reference rather than by pattern: a
// candidate is deleted only when its filename appears in none of the build's
// text output. Anything reachable from HTML, CSS, JS, JSON-LD, the sitemap or
// llms.txt therefore survives by construction.
//
// The one thing this cannot see is a URL a script assembles at runtime from
// fragments. Nothing here does that — the carousel toggles a class on markup
// the build already emitted — but a future feature that builds image paths
// dynamically would need an exemption.

import { readdir, readFile, stat, unlink } from "node:fs/promises";
import { extname, join, basename, relative } from "node:path";
import { fileURLToPath } from "node:url";

const TEXT_EXT = new Set([".html", ".css", ".js", ".mjs", ".xml", ".txt", ".json", ".svg"]);
const IMAGE_EXT = new Set([".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"]);

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(path)));
    else out.push(path);
  }
  return out;
}

/** @param {{ assetsDir?: string }} [options] */
export default function pruneUnreferencedAssets({ assetsDir = "_astro" } = {}) {
  return {
    name: "prune-unreferenced-assets",
    hooks: {
      "astro:build:done": async ({ dir, logger }) => {
        const root = fileURLToPath(dir);
        const files = await walk(root);

        const candidates = files.filter(
          (f) =>
            IMAGE_EXT.has(extname(f).toLowerCase()) &&
            relative(root, f).split(/[\\/]/)[0] === assetsDir
        );
        if (candidates.length === 0) return;

        // Every filename mentioned anywhere in the build's text output.
        const haystack = (
          await Promise.all(
            files
              .filter((f) => TEXT_EXT.has(extname(f).toLowerCase()))
              .map((f) => readFile(f, "utf8"))
          )
        ).join("\n");

        const unreferenced = candidates.filter((f) => !haystack.includes(basename(f)));
        if (unreferenced.length === 0) {
          logger.info(`${candidates.length} image assets, all referenced`);
          return;
        }

        let freed = 0;
        for (const file of unreferenced) {
          freed += (await stat(file)).size;
          await unlink(file);
        }

        logger.info(
          `pruned ${unreferenced.length}/${candidates.length} unreferenced image assets ` +
            `(${(freed / 1048576).toFixed(2)} MB)`
        );
      },
    },
  };
}
