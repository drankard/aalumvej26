# Pipeline: Området (Area Reference Content)

## Schedule & Scope

- **Runs:** Monthly (1st Monday of each month)
- **Target:** 0–3 updated or new area items per run
- **Content type:** Semi-static reference content about places, attractions, and permanent features near Agger

## Runtime Context

```
${current_date}           — Today's date
${season}                 — spring|summer|autumn|winter
${current_areas}          — JSON array of current area cards [{id, name, dist, url, last_updated}]
${oplevelser_last_90d}    — Recent posts, useful for spotting areas that deserve their own card
```

## Purpose

The Området section is a curated, stable set of reference cards about places near Agger. Unlike Oplevelser, these don't expire — but they need periodic maintenance:

- Opening hours change seasonally
- New attractions open
- Existing places close, renovate, or rebrand
- A place mentioned repeatedly in Oplevelser posts might deserve its own card

This pipeline is an **audit and update** process, not high-volume content generation.

## Execution

### Step 1: Load Current State

Call **list_published_areas()** to get the current area cards. Review each one.

### Step 2: Audit Existing Cards

For each area card in the current set:

1. Call **web_fetch(url)** on the linked URL. Is it still live? Has the content changed?
2. Run a quick **web_search("{area_name} nyt 2026")** to check for major news.
3. Flag each card as:
   - **unchanged** — No updates needed
   - **minor_update** — Small factual change (hours, new detail)
   - **major_update** — Significant change (new attraction, closure, rebranding)
   - **broken_link** — URL no longer works

### Step 3: Discover New Area Candidates

Check if any place deserves a new area card:

1. **Frequency in posts.** If ${oplevelser_last_90d} contains 3+ posts referencing a place that doesn't have its own card, it's a candidate. Example: if Vorupør keeps appearing, it might deserve its own card.

2. **Search for new attractions:**
   ```
   "ny attraktion Thy 2026"
   "åbner Thisted Mors Agger 2026"
   ```

**New card criteria:**
- Within geographic scope (max ~60 min from Agger)
- Permanent or long-running (not a one-off event — those go in Oplevelser)
- Has a stable source URL
- Enough substance for a meaningful description

### Step 4: Apply Updates

For cards flagged as minor_update or major_update:
1. Call **validate_url()** on the existing or new URL
2. Call **update_area(area_id, url, translations)** with corrected information
3. All translations (da, en, de) must be updated together

For new area candidates:
- New cards are created by the site owner, not auto-published. Report your recommendations in the summary.

### Step 5: Verify Distances

For any updated area card, verify driving distances. Known verified distances:

| Destination | Distance | Drive time |
|-------------|----------|------------|
| Vorupør | ~20 km | ~20 min |
| Klitmøller | 39 km | ~35 min |
| Thisted | 38 km | ~35 min |
| Hanstholm | 51 km | ~45 min |
| Nykøbing Mors (Jesperhus) | ~55 km | ~45 min |

Never round driving times down. "~35 min" not "nearby".

### Step 6: Summary

Report:
- Audit results for each existing card (unchanged/updated/broken)
- What was updated and why
- Any new area card recommendations (with reasoning)
- Any broken links found

**Writing guidelines for area cards:**
- Descriptions should be evergreen. Don't reference specific dates or events.
- Be opinionated: "Perfekt familiedagstur" is better than "Kan besøges med familien."
- Include the practical hook: what makes someone actually go there?
- All three languages (da, en, de) must be included.

## Guardrails

- **Max 12 area cards total.** The section should be scannable, not exhaustive.
- **No auto-creating area cards.** Only update existing ones and recommend new ones.
- **Don't update the same card twice in a month** unless something significant changed.
- **Distance accuracy.** Never round down. Use "~35 min (39 km)" format.
- **Prefer stable URLs.** Homepage links over deep links unless the deep link is stable.
