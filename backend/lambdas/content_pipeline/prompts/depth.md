# Add depth to existing posts

These posts are already published on aalumvej26.dk with a title and a short
excerpt. You are adding the depth block — the part a reader and an answer engine
actually use. You are NOT rewriting the title or the excerpt.

Current date: ${current_date} · Season: ${season}

## Task

For EVERY post below, return `title_ref` (the post's Danish title copied EXACTLY
as given) and `translations` for **da, en, de**, each containing `tldr`, `body`,
`facts` and `faq`.

Write Danish first, then translate. German matters — many guests are German, so
write natural German, not machine translation.

## How much to write

Depends on whether the post survives the season. Spend the words where they last.

**Evergreen places** (no date, or a date like "Året rundt"):

- `tldr`: 30–50 words. A direct, standalone answer to the question the title
  implies — it has to read correctly with no surrounding page, because it is
  frequently the only part that gets quoted. Lead with the answer.
- `body`: 200–300 words of markdown in two or three `##` sections. What it is,
  what you actually do there, when to go, what to know before setting off. No
  closing paragraph restating the intro, and no sentence that exists only to
  reach a word count — this block is collapsed behind a "read more" control on
  the page, so padding buys nothing and costs trust.
- `faq`: 3–5 real questions someone would type into a search box ("Kan man komme
  op i fyret?", "Er der toilet?", "Hvor lang tid tager turen?"). Answers 20–50
  words, each complete on its own.

**Dated events**:

- `tldr`: 30–40 words.
- `body`: empty string. Do not write an essay about a weekend that will be over
  before most readers see it.
- `faq`: 0–2 entries, only where the source answers something non-obvious.

## Facts — provenance is mandatory

Every fact row is a claim about somebody else's business: their opening hours,
their prices, their age limits. Publishing a wrong one in three languages is
worse than publishing nothing at all.

Each row is `{label, value, source_url, computed}`:

- `source_url` — the post's own source URL, and ONLY if the source text below
  actually states the fact. Copy the value; do not reconstruct it.
- `computed: true` — reserved for facts the site derives itself (distance and
  drive time from Ålumvej 26). Set `source_url` to null for these.
- **If the source text does not state it, omit the row.** Do not estimate, do not
  fall back on general knowledge, do not infer a price from a similar
  attraction, do not write "typisk 30–50 kr." or "ca. 2 timer". A short honest
  table beats a full invented one.

Rows with neither a `source_url` nor `computed: true` are discarded before
publication, so a guessed row is wasted output rather than a shortcut. Up to 10
rows. Label them in the target language ("Afstand" / "Distance" / "Entfernung")
and keep values short enough to read in a table cell.

If the source text is thin or missing, return an empty `facts` list and a `tldr`
built only from the title and excerpt. That is a correct answer, not a failure.

## Posts

${posts}
