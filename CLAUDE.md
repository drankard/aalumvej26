# Aalumvej26

## Architecture

- **Frontend**: Astro (static site generation) + TypeScript, hosted on S3 static website. The build fetches content from the backend RPC API and renders every page as static HTML — da at the root, `/en/` and `/de/` path-prefixed — so all content is crawlable by search engines and AI indexers without JavaScript.
- **Backend**: Single Python Lambda, RPC-style (not REST) via API Gateway v2 HTTP API
- **Database**: DynamoDB single-table design (pk/sk pattern)
- **IaC**: Native CloudFormation via AWS SAM (`template.yaml`)
- **CI/CD**: GitHub Actions with OIDC auth (`.github/workflows/deploy.yml`)
- **AWS Profile**: `graveyard-master` (eu-west-1)
- **Stack name**: `aalumvej26`

## Commands

```
npm run dev              # Start backend + frontend locally
npm test                 # Run backend pytest suite
npm run build            # SAM build (backend)
npm run build:frontend   # Astro production build (astro check && astro build)
npm run deploy           # SAM deploy (backend infra)
npm run deploy:frontend  # Build + sync frontend to S3
npm run deploy:all       # Deploy backend then frontend
```

## Backend Design

- **RPC pattern**: Single `POST /rpc` endpoint. Request: `{"action": "name", "payload": {}}`. Response: `{"success": bool, "data": any, "error": str|null}`.
- **Pydantic everywhere**: All models use Pydantic v2 with strict typing. No raw dicts crossing layer boundaries.
- **Repository pattern**: `DynamoDBAdapter` wraps boto3 table operations. Repositories return Pydantic models, not dicts.
- **Action registry**: Decorated functions registered via `@register("action_name")`. Dispatch injects repository dependencies.
- **Layer separation**: `handler.py` -> `actions/` -> `repositories/` -> `DynamoDBAdapter`. Each layer only talks to the one below.

## Testing

- Mock at the edges only — input and output boundaries
- Repository tests: mock `DynamoDBAdapter`
- Action tests: mock repositories
- Handler tests: mock `boto3`
- Tests are deterministic, no real AWS calls
- Run: `npm test` or `cd backend && python -m pytest tests/ -v`

## Frontend Design

- **Astro static site**: content is fetched once per build (`src/lib/content.ts`, RPC `list_content` + `list_archived_posts`) and rendered to static HTML. No client-side data fetching; small vanilla-JS islands handle the carousel/nav/sticky-bar interactivity.
- **Content refresh is event-driven, no cron on the GitHub side**: the content pipeline Lambda triggers the `aalumvej26-content-rebuild-{stage}` CodeBuild project after every successful run (and `backfill --apply`); CodeBuild clones `main` and runs `scripts/deploy-frontend.sh` (build → S3 sync → CloudFront invalidation) — the same script `deploy.yml` and the manual `rebuild-frontend.yml` workflow use. EventBridge is the only scheduler in the system. Rebuild failures alert via the `ContentSummaryTopic` SNS email.
- **URL contract** (parity-critical, see `src/lib/slug.ts` + `scripts/slug-parity.mjs`): `/oplevelser/{slug}/`, `/omraadet/{slug}/`, category hubs `/oplevelser/kategori/{id}/`, archive `/oplevelser/arkiv/`, locales as path prefixes (`/en/`, `/de/`; da at root). Slugs derive from the Danish title — never change the slug algorithm without a redirect plan.
- **Page structure**: routes in `src/pages/` (da root + `[lang]` tree) are thin wrappers around shared implementations in `src/pageviews/`. SEO endpoints: `sitemap.xml.ts`, `llms.txt.ts`, `llms-full.txt.ts`.
- `VITE_API_URL` env var sets the API endpoint used at build/dev time (defaults to `http://localhost:4000` for dev); `PRERENDER_CONTENT_FILE` points at a JSON snapshot for offline builds.
- Build never fails on API outage — it degrades to house-only pages and logs loudly.

## Adding a New Feature

1. Define Pydantic models in `backend/models/`
2. Add repository methods in `backend/repositories/`
3. Register action in `backend/actions/` with `@register("action_name")`
4. Write tests for each layer
5. Add frontend components/pages as needed (`src/components/`, `src/pageviews/`, `src/pages/`)
6. Handler wiring is automatic via the action registry

## Local Dev

- Backend runs on port 4000 (`backend/dev_server.py`), hits real DynamoDB via SSO
- Frontend runs on Astro dev server (port 4321+)
- Both start together with `npm run dev`
