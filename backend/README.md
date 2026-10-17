# Wise VAT Back

Hackathon project: the Wise Business card automatically recovers the VAT paid on foreign business trips. This repo is the FastAPI backend: Wise behind an interface with a mock, a pure rules engine and a demo simulator. The frontend lives in a separate repository.

## Quick start

```bash
cp .env.example .env
make install        # backend venv via uv
make dev-backend    # http://localhost:8000  (docs at /docs)
```

Other targets: `make seed`, `make test`, `make demo-reset`. Run `make` to list them.

## Layout

```
backend/app/
  api/           thin routers (health, accounts, rates, simulate, events/SSE)
  domain/        PURE rules engine: (state, event) -> Decision(action, reason). No I/O. Unit-tested.
  integrations/  WiseClient protocol + mock + real (httpx), factory by WISE_MODE; Claude helper
  models/        SQLModel tables (SQLite by default)
  schemas/       API contracts (Pydantic), e.g. ExtractedInvoice from image processing
  simulator/     fake events behind /simulate/* (also stands in for webhooks)
backend/schemas/ ExtractedInvoice JSON Schema for the image-processing side
backend/seed/    seed script, cached fallback rates, example invoices
```

## Conventions

- **Money is `Decimal`, never float.** Use `domain.money.Money`.
- **Domain stays pure.** Routers/simulator load state, call the engine, and persist/publish the result.
- **Never call Wise directly.** Use `integrations.factory.get_wise_client()`. `WISE_MODE=mock` is the default, and the real rates endpoint is the first thing to wire up.
- Every `Decision` carries a human-readable `reason`, for the UI and the pitch.

## First steps once the challenge is known

1. Fix the API contract (routers + Pydantic schemas); the frontend generates its types from `/openapi.json`.
2. Implement the domain rules + tests, the mock data, and the simulator.
3. Deploy once early (Fly.io/Render/Railway, or a Cloudflare Tunnel) and record a backup demo video.
