# Aalumvej26

## Architecture

- **Frontend**: React + TypeScript + Vite, hosted on S3 static website
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
npm run build:frontend   # Vite production build
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

- Context-based state management (`AppContext`)
- RPC client (`api/client.ts`) handles all backend calls
- `VITE_API_URL` env var sets the API endpoint (defaults to `http://localhost:4000` for dev)

## Adding a New Feature

1. Define Pydantic models in `backend/models/`
2. Add repository methods in `backend/repositories/`
3. Register action in `backend/actions/` with `@register("action_name")`
4. Write tests for each layer
5. Add frontend components/context as needed
6. Handler wiring is automatic via the action registry

## Local Dev

- Backend runs on port 4000 (`backend/dev_server.py`), hits real DynamoDB via SSO
- Frontend runs on Vite dev server (port 5173+)
- Both start together with `npm run dev`
