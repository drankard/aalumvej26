// Single definition of "is this fact publishable".
//
// The pipeline enforces the same rule at write time (drop_unsourced_facts in
// content_pipeline/schemas.py), but that only covers newly generated copy.
// Anything already stored, or edited by hand, still reaches the site — so every
// output surface filters through here rather than trusting the data. Keep this
// the only place the rule is expressed: it previously lived in the facts table
// component alone, and llms-full.txt happily published what the page had dropped.

import type { Fact } from "./types";

export const isSourced = (f: Fact): boolean =>
  Boolean(f?.computed) || /^https?:\/\//.test((f?.source_url || "").trim());

/** Facts safe to publish: non-empty and traceable to a source or to the site. */
export const publishableFacts = (facts: Fact[] | undefined): Fact[] =>
  (facts || []).filter((f) => f?.label?.trim() && f?.value?.trim() && isSourced(f));

/**
 * Display hostname, or "" if the URL won't parse. Never throws: a malformed
 * source URL in the data must not take the whole static build down.
 */
export function hostname(url: string | null | undefined): string {
  try {
    return new URL(String(url)).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

/** Domains already credited beside the facts table, so the page needn't repeat them. */
export const creditedDomains = (facts: Fact[] | undefined): Set<string> =>
  new Set(publishableFacts(facts).map((f) => hostname(f.source_url)).filter(Boolean));
