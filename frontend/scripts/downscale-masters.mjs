// One-off-ish maintenance script: bring photo masters down to a sane size.
//
// The house photos came straight off a phone at 4032x3024 (~39 MB for fifteen
// files). Nothing on the site displays them wider than ~820 CSS px, so the
// extra pixels were only ever cost: repo weight, and sharp re-decoding 12 MP
// JPEGs on every content-triggered CodeBuild rebuild.
//
// MAX_WIDTH is deliberately well above any display size — astro:assets derives
// the actual responsive widths from these, and a master should keep enough
// headroom for a future layout without being an unedited camera dump.
//
// Run from frontend/:  node scripts/downscale-masters.mjs [--apply]
// Without --apply it reports what it would do and writes nothing.

import { readdir, stat, rename, unlink } from "node:fs/promises";
import { join } from "node:path";
import sharp from "sharp";

const DIR = "src/assets/house";
const MAX_WIDTH = 2400;
const QUALITY = 82;

const apply = process.argv.includes("--apply");
const files = (await readdir(DIR)).filter((f) => /\.jpe?g$/i.test(f)).sort();

let before = 0;
let after = 0;

for (const name of files) {
  const path = join(DIR, name);
  const size = (await stat(path)).size;
  const { width, height } = await sharp(path).metadata();
  before += size;

  if (width <= MAX_WIDTH) {
    after += size;
    console.log(`  skip   ${name} — already ${width}x${height}`);
    continue;
  }

  const tmp = `${path}.tmp`;
  await sharp(path)
    .resize({ width: MAX_WIDTH, withoutEnlargement: true })
    .jpeg({ quality: QUALITY, mozjpeg: true })
    .toFile(tmp);

  const newSize = (await stat(tmp)).size;
  after += newSize;

  const pct = ((1 - newSize / size) * 100).toFixed(0);
  console.log(
    `  ${apply ? "resize" : "would"} ${name} — ${width}x${height} ${mb(size)} -> ${MAX_WIDTH}px ${mb(newSize)} (-${pct}%)`
  );

  if (apply) await rename(tmp, path);
  else await unlink(tmp);
}

console.log(
  `\n${files.length} files: ${mb(before)} -> ${mb(after)}` + (apply ? "" : "  (dry run — pass --apply)")
);

function mb(bytes) {
  return `${(bytes / 1048576).toFixed(2)} MB`;
}
