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

Run 8–12 searches across three modes:

**Mode A — Time-scoped event discovery**

Search for events in the next 2–6 weeks:
```
"events Thy maj 2026"
"koncert Thisted juni 2026"
"Cold Hawaii 2026 program"
"hvad sker der Agger forår"
```

**Mode B — Source crawl**

Use web_fetch on 4–6 source pages to scan for new content:
- visit-nordvestkysten.com (events section)
- nationalparkthy.dk (activities)
- jesperhus.dk (seasonal news)
- coldhawaiisurfcamp.com
- gladzoo.dk

**Mode C — Interest-based discovery**

2–3 broader queries based on season and underrepresented categories:
```
Spring: "trækfugle Agger Tange forår", "påske aktiviteter Thy børn"
Summer: "surfkursus Klitmøller begynder", "fiskemarked Vorupør"
Autumn: "østerssafari Limfjorden 2026", "Cold Hawaii Games program"
Winter: "julemarked Thisted 2026", "vinterfiskeri Limfjorden"
```

### Step 3: Evaluate

For each potential item, score on five criteria (1–5 each):

| Criterion | 5 (best) | 1 (worst) |
|-----------|----------|-----------|
| **Proximity** | Agger itself | 60+ min away |
| **Tourist relevance** | Exactly what a holidaymaker wants | Only locals would care |
| **Timeliness** | Happening in next 2–4 weeks | Already happened or 6+ months away |
| **Uniqueness** | Nothing similar in published posts | We already cover this |
| **Content quality** | Rich details, good source | Thin info, weak source |

**Minimum score to publish: 15/25**

Also reject items that:
- Duplicate something in ${published_last_30d}
- Have no verifiable source URL
- Are primarily advertising

### Step 4: Publish

For each item scoring 15+:

1. Call **validate_url(url)** on the source URL
2. Call **create_post()** with:
   - **category**: one of natur, kultur, mad, surf, born
   - **tag_key**: one of event, guide, activity, openNow, seasonBest, kidFriendly, natureGem, localFavorite, culturalHistory, bigEvent
   - **url**: the verified source URL
   - **emoji**: pick an appropriate emoji (see BASE_SYSTEM)
   - **sort_order**: lower numbers appear first — put the most compelling items first
   - **translations**: all three languages (da, en, de) with title, excerpt, date

**Writing guidelines:**
- Titles should be news-like: "Danish Open Windsurf: Wave i Klitmøller" not "Windsurfing i Thy"
- Excerpts answer "why should I care?" with one concrete detail
- Dates are human-readable: "23–25. maj 2026" not ISO format

### Step 5: Summary

After publishing, report what you did:
- How many searches you ran
- How many candidates you found and evaluated
- How many posts you published (with titles)
- Any notable sources that were down or had no new content

## Guardrails

- **Max 8 posts per run.** Quality over quantity.
- **0 posts is fine.** Don't pad with weak content.
- **Max 3 fetches per domain** to avoid hammering sources.
- **Always validate URLs** before calling create_post.
