# Wise VAT Back

Hackathon project: the Wise Business card automatically recovers the VAT paid on foreign business trips. This repo is the FastAPI backend: Wise behind an interface with a mock, a pure rules engine and a demo simulator. The frontend lives in a separate repository.

## Quick start

```bash
cp .env.example .env
make install        # backend venv via uv
make dev-backend    # http://localhost:8000  (docs at /docs)
```

Other targets: `make seed`, `make test`, `make demo-reset`. Run `make` to list them.

## Docker Compose

The compose stack runs the Python backend and the Caddy frontend in Docker. Ollama runs on the host machine. The backend container reaches it through `host.docker.internal:11434`.

1. Start Ollama on the host. Pull the model once. Run `ollama pull qwen3-vl:8b`.
2. Stop any local dev server on ports 8000 and 8080.
3. Run `docker compose up` at the repo root. Rebuild after code changes. Run `docker compose up --build`.
4. Open the frontend at `http://localhost:8080`. The API docs live at `http://localhost:8000/docs`.

On Linux, bind Ollama to every interface. Run `OLLAMA_HOST=0.0.0.0:11434 ollama serve`.
The seed reloads the demo data on every start. Set `SEED_ON_START=false` to disable it.
The SQLite database persists in the `backend-data` Docker volume.

## Local AI invoice reader

`POST /invoices/upload` takes a PDF, a photo or an invoice JSON file. A local Ollama vision model reads PDFs and photos. It needs no API key, no account and has no usage limit.

Set up the machine that runs the backend once:

1. Install Ollama from https://ollama.com, or run `brew install ollama` on macOS.
2. Download the model (6.1 GB): `ollama pull qwen3-vl:8b`.
3. Keep the Ollama app open. Check it with `curl http://localhost:11434/api/tags`.

The backend renders up to 3 PDF pages as images. It also sends the PDF text layer. Ollama returns JSON in the shape of `backend/schemas/extracted_invoice.schema.json`. The backend validates the JSON and runs the VAT back rules.

Settings in `.env`: `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS`. A smaller machine can use `qwen3-vl:4b`.

Sample PDFs live in `backend/seed/documents/`:

| File | Expected result |
| --- | --- |
| `pass_de_hotel_berlin.pdf` | approved, €22.50 |
| `fail_at_restaurant_no_vat_number.pdf` | rejected, no supplier VAT number |

Each PDF has an `.expected.json` file with the correct extraction. The tests use it in place of the AI. Regenerate the PDFs with `cd backend && uv run --with reportlab python -m seed.make_documents`.

## Layout

```
backend/app/
  api/           thin routers (health, accounts, rates, simulate, events/SSE)
  domain/        PURE VAT back rules: country + category -> line decision with a reason. No I/O. Unit-tested.
  integrations/  WiseClient protocol + mock + real (httpx), factory by WISE_MODE; Ollama invoice reader
  models/        SQLModel tables (SQLite by default)
  schemas/       API contracts (Pydantic), e.g. ExtractedInvoice from image processing
  simulator/     fake events behind /simulate/* (also stands in for webhooks)
backend/schemas/ ExtractedInvoice JSON Schema for the image-processing side
backend/seed/    seed script, cached fallback rates, example invoices, sample invoices, sample invoice PDFs
```

## Conventions

- **Money is `Decimal`, never float.** Use `domain.money.Money`.
- **Domain stays pure.** Routers/simulator load state, call the engine, and persist/publish the result.
- **Never call Wise directly.** Use `integrations.factory.get_wise_client()`. `WISE_MODE=mock` is the default, and the real rates endpoint is the first thing to wire up.
- Every line decision carries a human-readable `reason`, for the UI and the pitch.

## First steps once the challenge is known

1. Fix the API contract (routers + Pydantic schemas); the frontend generates its types from `/openapi.json`.
2. Implement the domain rules + tests, the mock data, and the simulator.
3. Deploy once early (Fly.io/Render/Railway, or a Cloudflare Tunnel) and record a backup demo video.
