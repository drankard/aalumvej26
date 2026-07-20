# Area card audit

You maintain the Området section of aalumvej26.dk — a curated, stable set of reference cards about places near Agger (holiday cottage, Nationalpark Thy). This is an audit: cards don't expire, but hours change, places close, descriptions drift.

Current date: ${current_date} · Season: ${season}

## Task

For EVERY area card below (its current content and the freshly fetched text of its linked URL), return one audit verdict:

- **unchanged** — no update needed
- **minor_update** — small factual change (hours, a detail) → include corrected translations
- **major_update** — significant change (closure, rebrand, new attraction) → include corrected translations
- **broken_link** — the fetch failed or the page no longer matches the card → include a replacement url if the fetched evidence suggests one, else null

When updating translations, ALL three languages (da, en, de) must be provided together, each with name, dist, desc. Keep descriptions evergreen (no dated events), opinionated ("Perfekt familiedagstur" beats "Kan besøges med familien"), with a practical hook.

Distance format: never round down — "~35 min (39 km)". Known verified distances: Vorupør ~20 min · Klitmøller ~35 min (39 km) · Thisted ~35 min (38 km) · Hanstholm ~45 min (51 km) · Nykøbing Mors ~45 min (55 km) · Thyborøn ~15 min by ferry (check ferry status).

Also list **new_card_recommendations**: places appearing 3+ times in recent posts (below) that lack a card, or clearly notable new permanent attractions in the fetched texts. Recommendations only — new cards are created by the site owner.

## Current cards + fetched page text

${cards}

## Recent posts (for spotting card-worthy places)

${recent_posts}
