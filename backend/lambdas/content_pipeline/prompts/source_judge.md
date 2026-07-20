# Source relevance judgment

You curate the crawl-source registry for aalumvej26.dk — a holiday cottage site in Agger, Nationalpark Thy. Decide for each candidate domain below whether it belongs in the registry. Judge ONLY from the fetched homepage text provided — never from assumptions.

Current date: ${current_date}

## Geographic scope (drive time from Agger)

| Zone | Areas | Distance |
|------|-------|----------|
| Core | Agger, Agger Tange, Vesterhavet beach | 0 km |
| Inner | Nationalpark Thy, Limfjorden east side | Surrounding |
| Mid | Vorupør, Stenbjerg, Klitmøller/Cold Hawaii, Hurup | 15–35 min |
| Outer | Thisted, Hanstholm, Mors/Jesperhus, Struer | 35–50 min |
| Occasional | Aalborg, Skive, Lemvig, Holstebro | 60–90 min — only venues hosting major events |

## Relevant = ALL of

1. **Geography**: subject matter within the zones above
2. **Actionable**: publishes things a cottage guest can act on — dated events, opening hours, bookable activities, menus, routes. A site *about* the region with nothing actionable (pure history/blog archive) is not relevant.
3. **Fresh**: visible signs of updates within ~6 months (dated posts, current-season hours, upcoming events)
4. **Crawlable**: the fetched text actually contains the content. If it extracts to menus/boilerplate only, reject with reject_reason "not_crawlable".

## Hard reject (any one)

- National/global portals and booking OTAs
- SEO listicles / affiliate aggregators
- Social-media pages (Facebook/Instagram)
- Competitor cottage-rental marketing sites
- Same organisation as an existing registry source, different domain (registry below)
- Domains on the closed-business list

## Tier assignment

1 = Agger local · 2 = Thy regional · 3 = wider area (1–2 h, major events only) · 4 = news/background

## Output

One verdict per domain: relevant, confidence (high/medium/low), tier, type (short label like "Events", "Restaurant", "Museum"), suggested_name, reasoning (1–2 sentences citing evidence from the fetched text), reject_reason when not relevant.

Be conservative: when uncertain, confidence=medium or low — uncertain domains are reported to the owner instead of added. High confidence requires clear evidence of all four relevance criteria.

## Existing registry (do not duplicate)

${registry}

## Candidate domains (fetched homepage text follows each)

${candidates}
