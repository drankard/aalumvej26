// Locale guard for the fixed site text (src/i18n/locales/{da,en,de}.json).
//
// These three files are written by hand and nothing translates them, so a slip
// stays live until someone notices: "Naturgrundstueck" and a magnet emoji on the
// German pages from March to November 2026 (ASG-317). Runs before every build;
// a failure stops the deploy and the content rebuild alike.
//
//   1. the three files have the same keys, and lists the same length
//   2. every string carries the same emoji in every language
//   3. German has no ASCII spelling of an umlaut (ae, oe, ue) outside ALLOWED
//
// Usage: node scripts/locale-check.mjs

import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "i18n", "locales");
const LANGS = ["da", "en", "de"];
// real German words spelt with ae/oe/ue; add one here when the check is wrong
const ALLOWED = new Set(["aktuelle", "aktuell", "neue", "neuen", "neues", "neuer", "feuer", "abenteuer", "steuer", "treue", "poesie", "duett", "quelle"]);

const files = Object.fromEntries(LANGS.map((l) => [l, JSON.parse(readFileSync(join(DIR, `${l}.json`), "utf8"))]));
const errors = [];

function flatten(v, path = "", out = {}) {
  if (Array.isArray(v)) {
    out[`${path}.length`] = v.length;
    v.forEach((x, i) => flatten(x, `${path}[${i}]`, out));
  } else if (v && typeof v === "object") {
    for (const [k, x] of Object.entries(v)) flatten(x, path ? `${path}.${k}` : k, out);
  } else out[path] = v;
  return out;
}

const flat = Object.fromEntries(LANGS.map((l) => [l, flatten(files[l])]));
const emoji = (s) => (typeof s === "string" ? s.match(/\p{Extended_Pictographic}/gu) || [] : []).join("");

for (const l of LANGS.slice(1)) {
  for (const k of Object.keys(flat.da)) {
    if (!(k in flat[l])) errors.push(`${l}: missing ${k}`);
    else if (k.endsWith(".length") && flat[l][k] !== flat.da[k]) errors.push(`${l}: ${k} is ${flat[l][k]}, da has ${flat.da[k]}`);
    else if (emoji(flat[l][k]) !== emoji(flat.da[k])) errors.push(`${l}: ${k} has "${emoji(flat[l][k])}", da has "${emoji(flat.da[k])}"`);
  }
  for (const k of Object.keys(flat[l])) if (!(k in flat.da)) errors.push(`${l}: ${k} is not in da`);
}

for (const [k, v] of Object.entries(flat.de)) {
  if (typeof v !== "string") continue;
  for (const w of v.match(/\p{L}+/gu) || []) {
    if (/ae|oe|ue/i.test(w) && !ALLOWED.has(w.toLowerCase())) errors.push(`de: ${k}: "${w}" looks like an umlaut spelt in ASCII`);
  }
}

if (errors.length) {
  console.error(`locale-check: ${errors.length} problem(s)\n  ` + errors.join("\n  "));
  process.exit(1);
}
console.log(`locale-check: ${LANGS.join(", ")} agree (${Object.keys(flat.da).length} entries)`);
