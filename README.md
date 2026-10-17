# SIGINT · Wise VAT Back

Business travellers pay VAT abroad. Most companies never claim it back, because the paperwork is slow and the rules differ per country.

**Wise VAT Back** recovers that money automatically. An employee uploads a receipt. A local AI reads it. The backend checks the invoice, matches it to the Wise Business card transaction, and applies the VAT refund rules of the country. The employer sees the refundable VAT per country on one screen.

The AI runs on your own machine. It needs no API key, no account, and no internet connection. Invoice data never leaves the computer.

---

## Contents

- [How it works](#how-it-works)
- [Repository layout](#repository-layout)
- [Quick start with Docker](#quick-start-with-docker)
- [Local AI setup (Ollama)](#local-ai-setup-ollama)
- [Local development without Docker](#local-development-without-docker)
- [Try the demo](#try-the-demo)
- [Sample data](#sample-data)
- [VAT back rules](#vat-back-rules)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Tests and checks](#tests-and-checks)
- [Troubleshooting](#troubleshooting)
- [Team workflow](#team-workflow)
- [Limitations](#limitations)
- [Team](#team)

---

## How it works

```
 Employee page (/employee)
   │  PDF, photo or camera picture
   ▼
 POST /invoices/upload ──────────────► Ollama on the host (qwen3-vl:8b)
   │                                    PDF pages + text layer → JSON in the invoice schema
   ▼
 1. Validate     required fields present, schema valid
 2. VIES check   supplier VAT number is legitimate (mocked)
 3. Match        unclaimed card transaction with the same total and currency
 4. Rules        VAT back rule per country and expense category, line by line
 5. Store        approved or rejected, with human-readable reasons
   │
   ▼
 Employer page (/employer)   refundable VAT per country, approved receipts
```

Every decision carries a plain-English reason, for example *"The invoice has no supplier VAT number."* or *"Entertainment expenses are not refundable in Denmark."*

The upload accepts only a PDF or a photo. The employee can also take the photo from the upload dialog. A JSON invoice can go only to `POST /invoices`, for tests and development.

---

## Repository layout

```
sigint-monorepo/
├── AGENTS.md, CLAUDE.md        Rules for every contributor and AI agent
├── SKILLS.md                   Shared agent skills (for example wise-design)
├── PLAN.md                     Signed plan entries of every agent
├── init                        One-step launcher: Ollama, model, Docker Compose
├── docker-compose.yml          Backend and frontend containers
├── backend/                    Python project (FastAPI)
│   ├── Makefile                install, seed, dev-backend, test, golden, eval-ai
│   ├── .env.example            Settings template
│   ├── pyproject.toml, uv.lock Dependencies
│   ├── app/
│   │   ├── api/                Routers: invoices, receipts, claims, health, placeholders
│   │   ├── domain/             Pure VAT back rules and Money type. No I/O.
│   │   ├── integrations/       Ollama invoice reader, upload extraction, VIES mock, Wise client
│   │   ├── models/             SQLModel tables (SQLite)
│   │   ├── schemas/            API contracts, ExtractedInvoice
│   │   └── services/           Invoice flow: validate → VIES → match → rules → store
│   ├── schemas/                extracted_invoice.schema.json (the AI output contract)
│   ├── seed/                   Seed script, sample invoices, sample PDFs and their generator
│   ├── evaluation/             AI extraction accuracy script
│   ├── tests/                  Pytest suite
│   └── Dockerfile, docker/entrypoint.sh
└── frontend/                   Static site (HTML, Tailwind CSS v4, Wise Neptune CSS)
    ├── Caddyfile               Clean URLs: /, /employee, /employer
    ├── Dockerfile
    └── www/
        ├── index.html          Landing page
        ├── employee/index.html Employee app: upload and receipt history
        ├── employer.html       Employer review: claims per country
        ├── api.js              Backend client (port 8000 of the page host)
        └── receipts.js         Shared receipt list
```

---

## Quick start with Docker

This is the easiest way to run everything. Docker runs the backend and the frontend. Ollama runs directly on the host, because Docker on macOS cannot use the Apple GPU.

**Prerequisites:** Docker Desktop, Git, and Ollama. See [Local AI setup](#local-ai-setup-ollama).

```bash
git clone https://github.com/magyariakos/sigint-monorepo.git
cd sigint-monorepo
./init --build
```

The `init` launcher does every step for you (macOS and Linux):

1. It checks that Docker and Docker Compose exist.
2. It starts Ollama on the host when it does not run yet.
3. It downloads the model on the first run (several GB).
4. It starts `docker compose up`. The `--build` flag rebuilds the images. Leave it out on later runs.

Without the launcher, start Ollama yourself and run `docker compose up --build`.

Open:

| Page | URL |
| --- | --- |
| Landing page | http://localhost:8080 |
| Employee app | http://localhost:8080/employee |
| Employer review | http://localhost:8080/employer |
| API docs (Swagger) | http://localhost:8000/docs |

The backend container waits up to 120 seconds for Ollama. It then seeds the demo database and starts the API. If Ollama is not ready, the API still starts. PDF and photo uploads then return a clear error until Ollama runs.

- Stop the stack: `Ctrl+C`, then `docker compose down`.
- Rebuild after a code change: `./init --build` or `docker compose up --build`.
- The database lives in the `backend-data` volume. The seed resets it on every start. Set `SEED_ON_START=false` to keep the data.
- On Linux, make Ollama listen on every interface: `OLLAMA_HOST=0.0.0.0:11434 ollama serve`.

---

## Local AI setup (Ollama)

[Ollama](https://ollama.com) is open source. It runs AI models on your machine and serves them on `http://localhost:11434`. The project uses **Qwen3-VL 8B**, a vision model that reads documents. It is free and has no usage limit.

Do this once on the machine that runs the backend.

**macOS**

```bash
brew install ollama
brew services start ollama
ollama pull qwen3-vl:8b
```

**Windows and Linux:** install Ollama from https://ollama.com/download, then run:

```bash
ollama pull qwen3-vl:8b
```

**Check that it works.** The answer must list `qwen3-vl:8b`.

```bash
curl http://localhost:11434/api/tags
```

**Hardware notes**

- The 8B model is a 6.1 GB download and uses about 8 GB of memory. A MacBook Air M3 with 16 GB runs it well.
- On a smaller machine, use `qwen3-vl:4b` (3.3 GB). Set `OLLAMA_MODEL=qwen3-vl:4b`.
- The first upload after a start is slow, because Ollama loads the model. Later uploads take about 10–40 seconds per invoice on Apple silicon. This is an estimate, so measure it on your machine.

**How the backend uses the model**

1. A PDF becomes up to 3 page images. The backend also reads the PDF text layer and adds it to the prompt for exact numbers.
2. A photo is shrunk to at most 2000 px and sent as JPEG.
3. The request sends `backend/schemas/extracted_invoice.schema.json` in the Ollama `format` field. Ollama then forces the answer into that JSON shape.
4. Pydantic validates the answer again. A bad answer gives a readable error, never silent wrong data.

The code lives in `backend/app/integrations/ollama_reader.py`.

---

## Local development without Docker

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), Ollama, and [Caddy](https://caddyserver.com) (or Python's built-in server). On macOS: `brew install uv caddy`.

### Backend

```bash
cd backend
cp .env.example .env
make install       # create the venv, install dependencies
make seed          # reset the database, load demo transactions
make dev-backend   # http://localhost:8000, reloads on code changes
```

Without `make` (for example on Windows), run the same steps by hand from `backend`:

```bash
uv sync --extra dev
uv run python -m seed.seed
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
caddy run          # http://localhost:8080
```

Without Caddy, use Python. Run it from the `sigint-monorepo` folder. The clean URLs then need the file name, for example `/employer.html`.

```bash
python -m http.server 8080 --bind 0.0.0.0 --directory frontend/www
```

### Styles

The repository tracks the built `frontend/www/style.css`, so serving needs no install. After a Tailwind class change, rebuild it:

```bash
cd frontend
pnpm install
pnpm run build:css
```

### Phone access

Both servers listen on every interface. Find the computer's IP address (`ipconfig getifaddr en0` on macOS, `ipconfig` on Windows). Then open `http://<IP>:8080/employee` on a phone on the same Wi-Fi. The pages call the backend on port 8000 of the same host. CORS allows any host on port 8080.

---

## Try the demo

1. Open http://localhost:8080/employee.
2. Tap **Add New Document**.
3. Tap **Take photo** to photograph a receipt, or **PDF or photo** to select a file. A sample PDF is in `backend/seed/documents/`.
   - On a phone, **Take photo** opens the camera app.
   - On a laptop, **Take photo** shows a live camera in the dialog. Tap **Capture**. The live camera needs `localhost` or https. The browser asks for camera access once.
4. Wait for the result. The button shows *"The AI reads the invoice..."* while Ollama works.
5. Read the result: approved with the refundable VAT, or rejected with the reasons.
6. Open http://localhost:8080/employer. It shows the refundable VAT per country and the approved receipts. It refreshes every few seconds.

**Reset the demo.** A card transaction can back only one invoice. A second upload of the same invoice is rejected on purpose. To start again, stop the backend and run `make seed` (or `docker compose restart backend`, which seeds on start).

---

## Sample data

The seed creates one demo company, *Példa Tech Kft.*, with one account per currency (EUR, PLN, CZK, DKK, SEK). It also creates one card transaction for every sample below, except one. The results below come from a run of the real invoice flow.

### Sample PDFs (for the AI)

`backend/seed/documents/`

| File | Expected result |
| --- | --- |
| `pass_de_hotel_berlin.pdf` | Approved, €22.50 |
| `fail_at_restaurant_no_vat_number.pdf` | Rejected: *The invoice has no supplier VAT number.* |

Each PDF has an `.expected.json` file with the correct extraction. The tests use it in place of the AI. Regenerate the PDFs with:

```bash
cd backend
uv run --with reportlab python -m seed.make_documents
```

### Invoice JSON files (API and tests only)

`backend/seed/invoices/`. The upload does not accept JSON. Send these files to `POST /invoices`, for example in the Swagger UI.

| File | Expected result |
| --- | --- |
| `at_hotel_vienna.json` | Approved, €26.00 |
| `de_hotel_munich.json` | Approved, €10.50 |
| `de_taxi_receipt_no_vat_id.json` | Rejected: no supplier VAT number |
| `pl_restaurant_warsaw.json` | Rejected: Poland refunds no VAT on meals |

### Multi-country samples

`backend/seed/sample_invoices/` holds 42 invoices from 9 countries. They fill the employer view with realistic data. 37 are approved. Some approvals refund only part of the VAT, for example `fr_hotel_paris.json` (€3.60, France refunds no VAT on the hotel room) and `pl_fuel_orlen_poznan.json` (36.80 PLN, Poland refunds 50% on fuel). Five show a rejection:

| File | Rejection reason |
| --- | --- |
| `at_fuel_omv_linz.json` | No line is eligible: Austria refunds no VAT on car fuel |
| `dk_concert_tivoli.json` | No line is eligible: entertainment |
| `pl_hotel_krakow.json` | No line is eligible: Poland refunds no VAT on hotels |
| `fr_taxi_lyon_no_vat_number.json` | No supplier VAT number |
| `it_parking_roma_no_transaction.json` | No matching unclaimed card transaction |

### Invoice contract

Every path ends in the same contract: `backend/schemas/extracted_invoice.schema.json`, mirrored by the Pydantic model `ExtractedInvoice`. Amounts are decimal strings (`"188.80"`), never floats. A `null` value means "not on the document".

---

## VAT back rules

The rules live in `backend/app/domain/vat_rules.py`. They are pure functions with unit tests.

- **Supported countries:** Austria, Germany, France, Italy, the Netherlands, Poland, Czechia, Denmark, Sweden. The country of the card transaction decides the rules.
- **Categories:** the ten expense codes of Directive 2008/9/EC (fuel, vehicle hire, vehicle expenses, road toll, travel, accommodation, food and drink, fair admission, entertainment, other).
- **Refundable share:** Directive 2008/9/EC, Art. 5 refunds VAT only as far as the country of refund allows deduction. Each country rule gives a share between 0% and 100% per category, with the national source in the code. A category without a national restriction is fully refundable.
- **Decision per line:** each invoice line gets its refundable VAT and a reason. An invoice is approved when at least one line has a refundable share above zero.

National restrictions in the current rule set (every other category refunds 100%):

| Country | Restricted categories |
| --- | --- |
| Austria | Fuel, vehicle hire, vehicle expenses: 0%. Entertainment: 0% |
| Germany | Entertainment: 0% |
| France | Fuel: 80%. Vehicle hire, vehicle expenses, travel, accommodation, entertainment: 0% |
| Italy | Fuel, vehicle hire, vehicle expenses, road toll: 40%. Travel, entertainment: 0% |
| Netherlands | Food and drink, entertainment: 0% |
| Poland | Fuel, vehicle hire, vehicle expenses, road toll: 50%. Accommodation, food and drink, entertainment: 0% |
| Czechia | Entertainment: 0% |
| Denmark | Food and drink: 25%. Fuel, vehicle hire, vehicle expenses, entertainment: 0% |
| Sweden | Vehicle hire: 50%. Entertainment: 0% |
- **VIES check:** mocked. Every VAT number passes, except `XX12345678`, which shows the "invalid company" path.
- **Matching:** the invoice gross total and currency must match an unclaimed card transaction.
- **Money:** always `Decimal`, rounded to cents.

---

## API reference

Interactive docs: http://localhost:8000/docs. The OpenAPI contract: http://localhost:8000/openapi.json.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/invoices/upload` | **Frontend entry point.** Multipart form: `document` (PDF or photo), optional `image_data_url` thumbnail. |
| `POST` | `/invoices` | The same flow with an `ExtractedInvoice` JSON body. |
| `GET` | `/receipts` | Stored invoices in the frontend receipt shape, newest first. |
| `GET` | `/claims` | Refundable VAT per country and currency, plus every stored result. |
| `GET` | `/health` | Liveness check. |
| `GET` | `/accounts`, `/accounts/{id}/transactions`, `/rates`, `/events/stream` | Placeholders for the Wise integration. They return empty or fixed data. |
| `POST` | `/simulate/card-swipe`, `/simulate/skip-time`, `/simulate/reset` | Placeholders for the demo simulator. |

Upload errors return `{"detail": {"reasons": [...]}}` with a status code:

| Status | Meaning |
| --- | --- |
| `413` | The document is larger than 20 MB. |
| `415` | The file is not a PDF or an image. JSON is rejected too. |
| `422` | The AI output does not match the invoice schema. |
| `503` | Ollama is not running, or the model is missing. |
| `504` | Ollama did not answer in time. |

---

## Configuration

The backend reads settings from environment variables and from `backend/.env` (copy `backend/.env.example`). Docker Compose sets its own defaults in `docker-compose.yml`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_URL` | `http://localhost:11434` (Docker: `http://host.docker.internal:11434`) | Where the backend finds Ollama |
| `OLLAMA_MODEL` | `qwen3-vl:8b` | Vision model for PDFs and photos |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | Maximum wait for one extraction |
| `OLLAMA_READY_TIMEOUT_SECONDS` | `120` | Docker only: startup wait for Ollama |
| `SEED_ON_START` | `true` | Docker only: reset the demo data on start |
| `DATABASE_URL` | `sqlite:///./vatback.db` | Database connection |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Allowed browser origins |
| `CORS_ORIGIN_REGEX` | `^https?://[^/:]+:8080$` | Allows any host on port 8080 (phones on the LAN) |
| `WISE_MODE` | `mock` | Wise client mode: `mock`, `sandbox`, `real` |

---

## Tests and checks

```bash
cd backend
make test
```

Or, from `backend`: `uv run pytest`. The suite has 170 tests. It covers the VAT rules, the invoice schema, the full invoice flow, the upload endpoint, CORS, and the Ollama reader. The tests never touch the network. A fake Ollama (`httpx.MockTransport`) stands in for the model, and the sample PDFs run with their expected extractions.

Frontend formatting:

```bash
cd frontend
pnpm run lint
```

---

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| *"The local AI is not running at http://localhost:11434"* | Start Ollama: `brew services start ollama`, or open the Ollama app. |
| *"The model qwen3-vl:8b is missing"* | Run `ollama pull qwen3-vl:8b`. |
| *"The local AI did not answer in time"* | The first call loads the model. Try again, or raise `OLLAMA_TIMEOUT_SECONDS`. |
| *"The backend at http://…:8000 is not reachable"* | Start the backend. Check that port 8000 is free. |
| 404 on every page with the Python server | Start the server from the `sigint-monorepo` folder, or pass the full path to `--directory`. |
| `/employer` gives 404 with the Python server | Python has no clean URLs. Open `/employer.html`, or use Caddy. |
| An invoice that worked before is now rejected | Its card transaction is already claimed. Run `make seed` to reset. |
| The Docker backend cannot reach Ollama on Linux | Run Ollama with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`. |
| Port 8000 or 8080 is in use | Stop the other dev server, or the Docker stack. |

---

## Team workflow

Read `AGENTS.md` before you change anything. Each project folder (`backend/`, `frontend/`) has its own `AGENTS.md` and `CLAUDE.md`.

- **Pull first:** pull the latest `main` at the start of every session.
- **Branch:** work on a short-lived feature branch. Never commit on `main`.
- **Commits:** small, atomic, [Conventional Commits](https://www.conventionalcommits.org) (`feat:`, `fix:`, `docs:`, `chore:`), in English.
- **Merge:** merge the branch into `main` locally. Push `main`. Delete the branch.
- **Never** use `--no-verify` or `--force`.
- **Whitelist:** `.gitignore` ignores everything by default. Add a `!path` rule before you add a new kind of file.
- **Agent coordination:** an AI agent writes a signed entry in `PLAN.md` before work.
- **Docs style:** Simplified Technical English (ASD-STE100): short sentences, active voice, no semicolons.
- **Skills:** `SKILLS.md` stores shared agent skills. For example, `/wise-design` styles a page to the Wise visual language.

Enable the git hooks once after cloning:

```bash
git config core.hooksPath .githooks
```

---

## Limitations

This is a hackathon demo.

- **Wise:** the Wise client runs in mock mode. Card transactions come from the seed. The refund is not paid out to a Wise balance yet.
- **VIES:** VAT number validation is mocked.
- **Rules:** the per-country shares cover the main national restrictions. They do not cover every special case, threshold or VAT rate.
- **AI accuracy:** a local 8B model is good but not perfect. Every answer is validated, and the reasons show why an invoice fails.
- **No authentication.** No submission to tax authorities. One demo company.

---

## Team

Magyari Ákos · rcsenge · Török Zaránd Tamás · Vilmos Babó

Built for a Wise hackathon.
