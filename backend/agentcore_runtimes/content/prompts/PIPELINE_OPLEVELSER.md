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

1. Call **get_sources()** to get the source registry.
2. Run 3–5 web searches for time-scoped events (next 2–6 weeks).
3. Use **fetch_content** on 5–8 Tier 1 and Tier 2 source URLs directly.
4. Optionally run 1–2 broader searches for underrepresented categories.

Prioritize fetch_content on known source URLs over search queries.

### Step 3: Evaluate (Pass/Fail Checklist)

For each candidate, check ALL of the following. Reject if any check fails:

- [ ] **Not a duplicate** — no existing published post covers the same event/topic
- [ ] **Within range** — located within 60 min drive of Agger (or 120 km max)
- [ ] **Timely** — happening within the next 60 days (or evergreen)
- [ ] **Tourist-relevant** — a holidaymaker would actually do this
- [ ] **Has concrete details** — dates, location, or opening hours from a fetched source
- [ ] **Has a working URL** — validate_url returns valid
- [ ] **Not on the closed list** — not a known closed/inactive business
- [ ] **From Tier 1 or 2 source** — Tier 3 only for major events

Publish all items that pass. Reject the rest with a brief reason.

### Step 4: Publish

For each passing item, best candidates first:

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
