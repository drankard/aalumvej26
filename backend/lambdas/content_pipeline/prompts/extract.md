# Extract candidate events

You extract candidate content for aalumvej26.dk — a thatched holiday cottage in Agger, on Denmark's west coast in Nationalpark Thy. Guests are Danish and German tourists staying in Agger.

Current date: ${current_date} · Season: ${season}

## Task

From the crawled page texts below, extract every distinct event, activity, opening, or seasonal experience a cottage guest in Agger could act on. One item per real-world thing — deduplicate within the pages yourself.

Per item:
- **title**: short, factual working title (Danish)
- **event_start / event_end**: ISO dates (YYYY-MM-DD, end inclusive) ONLY when the text states them; single-day events have start == end. Never guess dates.
- **evergreen**: true for recurring/always-available items (routes, year-round venues, annually recurring seasonal windows) — then both dates null.
- **location**: place name as stated
- **source_url**: the URL of the page the item came from (from the page header lines below)
- **source_domain**: its domain
- **category**: exactly one of
  - **natur** — hiking, cycling, wildlife, national park, beaches, birds, foraging
  - **kultur** — history, museums, churches, art, music, local traditions
  - **mad** — restaurants, cafés, fish, oysters, local produce, food events
  - **surf** — surfing, windsurfing, kite, SUP, Cold Hawaii, water sports
  - **born** — family activities, playgrounds, zoos, amusement parks
- **details**: 1–3 sentences of concrete facts FROM THE TEXT: times, prices, booking requirements, age ranges, distances. No invention, no filler.

## Hard skips (do not extract)

- Items that clearly ended before ${current_date}
- Pure advertising with no actionable information
- Locations obviously farther than ~120 km / 90 min from Agger
- Items already published (list below) — same event + same dates

## Already published — do NOT re-extract

${existing_posts}

## Crawled pages

${pages}
