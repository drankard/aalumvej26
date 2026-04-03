# Pipeline: Oplevelser (Events & Activities)

## Schedule & Scope

- **Runs:** Weekly (Sunday 00:00 UTC)
- **Target:** 3–8 new posts per run
- **Content type:** Time-bound events, seasonal activities, new openings, changing conditions

## Runtime Context

```
${current_date}        — Today's date
${season}              — spring|summer|autumn|winter
${published_last_30d}  — JSON array of recently published posts [{id, title, category, date}]
${category_counts}     — Posts per category over last 30 days
```

## Execution

### Step 1: Check What Exists & Archive Expired

Call **list_published_posts()** first. Review every published post:

1. **Archive expired content.** If a post's date has clearly passed (e.g., an event from last month), call **archive_post(post_id)**. Check the Danish date field against today's date (${current_date}). Evergreen content (guides, year-round activities) should NOT be archived.

2. **Note what's still live** to understand:
   - What topics are already covered (avoid duplicates)
   - Which categories are underrepresented (check ${category_counts})
   - What gaps the expired posts leave that could be filled with fresh content

### Step 2: Search for New Content

Run 8–12 searches across three modes. Prioritize Tier 1 and Tier 2 sources.

**Mode A — Time-scoped event discovery**

Search for events in the next 2–6 weeks:
```
"events Thy maj 2026"
"koncert Thisted juni 2026"
"Cold Hawaii 2026 program"
"hvad sker der Agger forår"
```

**Mode B — Source crawl**

Use fetch_content on 4–6 source pages, starting with Tier 1:
- aggerbooking.dk/oplevelser/det-sker/ (Tier 1)
- aggerdarling.dk (Tier 1)
- thy360.dk/kalender (Tier 2)
- nationalparkthy.dk/om-os/nyheder/ (Tier 2)
- visitthy.com/thy/experiences/events-thy (Tier 2)
- Additional sources as relevant to season

**Mode C — Interest-based discovery**

2–3 broader queries based on season and underrepresented categories:
```
Spring: "trækfugle Agger Tange forår", "påske aktiviteter Thy børn"
Summer: "surfkursus Klitmøller begynder", "fiskemarked Vorupør"
Autumn: "østerssafari Limfjorden 2026", "Cold Hawaii Games program"
Winter: "julemarked Thisted 2026", "vinterfiskeri Limfjorden"
```

### Step 3: Evaluate & Score

For each potential item, score on six criteria (1–5 each, max 30):

| Criterion | 5 (best) | 1 (worst) |
|-----------|----------|-----------|
| **Proximity** | Agger itself | 60+ min away |
| **Tourist relevance** | Exactly what a holidaymaker wants | Only locals would care |
| **Timeliness** | Happening in next 2–4 weeks | Already happened or 6+ months away |
| **Uniqueness** | Nothing similar in published posts | We already cover this |
| **Content quality** | Rich details, good source | Thin info, weak source |
| **Source tier** | Tier 1 source | Tier 3–4 source |

**Minimum score to publish: 18/30**

Also reject items that:
- Duplicate something in ${published_last_30d} (see dedup rules in BASE_SYSTEM)
- Have no verifiable source URL
- Are primarily advertising
- Fall outside the hard filtering rules (past events, >60 days out, >120 km, closed businesses)

### Step 4: Publish

For each item scoring 18+, in order of score (highest first):

1. Call **validate_url(url)** on the source URL
2. Call **create_post()** with:
   - **category**: one of natur, kultur, mad, surf, born
   - **tag_key**: one of event, guide, activity, openNow, seasonBest, kidFriendly, natureGem, localFavorite, culturalHistory, bigEvent
   - **url**: the verified source URL
   - **emoji**: pick an appropriate emoji (see BASE_SYSTEM)
   - **sort_order**: lower numbers appear first — put the highest-scoring items first
   - **translations**: all three languages (da, en, de) with title, excerpt, date

**Writing guidelines:**
- Titles should be news-like: "Danish Open Windsurf: Wave i Klitmøller" not "Windsurfing i Thy"
- Excerpts answer "why should I care?" with one concrete detail
- Include the per-category practical details (see BASE_SYSTEM)
- Dates are human-readable: "23–25. maj 2026" not ISO format

### Step 5: Save Run Summary

As your LAST action, call **save_run_summary()** with:

- **pipeline**: "oplevelser"
- **sources_searched**: total number of URLs you searched or fetched
- **sources_failed**: list of domains that returned errors (e.g. ["aggerbio.dk", "thy360.dk"])
- **candidates_found**: total items you evaluated in Step 3
- **published**: how many posts you created
- **archived**: how many posts you archived in Step 1
- **rejections**: breakdown by reason, e.g. `{"duplicate": 3, "low_score": 2, "dead_url": 1, "expired": 1}`
- **events_next_14d**: count of ALL published events (old + new) happening within 14 days of ${current_date}
- **notes**: anything unusual — sources that seem permanently down, content gaps, seasonal business status changes

## Guardrails

- **Max 8 posts per run.** Quality over quantity.
- **0 posts is fine.** Don't pad with weak content.
- **Max 3 fetches per domain** to avoid hammering sources.
- **Always validate URLs** before calling create_post.
- **Always call save_run_summary** as your last action, even if you published 0 items.
