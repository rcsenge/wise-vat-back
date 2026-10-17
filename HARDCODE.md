# HARDCODE.md

This file records the hardcoded mock JSON payload work for the SIGINT frontend.
It documents the changes, the experiments, the test commands, and the results.

Date: 2026-10-17
Branch: `feat/hardcoded-mock-payload`
Signer: Magyari Ákos's agent

## Goal

The frontend needs to send a hardcoded mock invoice JSON to the backend.
The frontend must not depend on the AI reading a PDF or a photo.
The demo builds the mock database and starts the backend in mock mode.

The user test command was:

```sh
cd ~/sigint-monorepo/backend && make dev-mock
```

The repository actually lives at `/Users/magyariakos/Scratch/sigint-monorepo`.
The test command used a `~` path that does not exist on this machine.
The same command works from the real backend path.

## Step 1: Delete the uncommitted changes

The repository had uncommitted changes on `main` before the work started.

```sh
git reset --hard HEAD
```

The reset removed the staged `MESSAGES.md` change.
It removed the unstaged changes in three frontend pages.
The working tree became clean. The reset did not remove untracked files,
because `git clean -nd` reported none.

## Step 2: Pull the latest main

The pull fast-forwarded the branch from `2b34026` to `fb60f0e`.
The pull brought a new feature: the demo invoice reader.
The demo reader replaces Ollama for the live demo.
Every upload returns the Berlin hotel invoice.

The mock database now adds an unclaimed card transaction for that invoice.
This is what made the hardcoded JSON approach possible.

## Step 3: Find the payload that the mock backend approves

The mock database transaction list has one unclaimed transaction for the
Berlin hotel invoice:

- transaction id 2
- merchant: Hotel Spreeufer Berlin GmbH
- gross: 292.50 EUR
- country: DE
- date: 2026-10-14

The mock backend approves the Berlin hotel invoice JSON.
I tested every sample invoice in `backend/seed/sample_invoices/`.
None matched the mock database transactions. So I used the Berlin invoice.

The payload lives in `backend/seed/documents/pass_de_hotel_berlin.expected.json`.
It is the same invoice that the demo reader returns.

## Step 4: Clean up the test server

The first test run started a server by hand.

```sh
pkill -f "uvicorn app.main:app"
```

## Step 5: Create a feature branch

Per `AGENTS.md`, no work happens on `main`.

```sh
git checkout -b feat/hardcoded-mock-payload main
```

## Step 6: Hardcode the payload in the frontend

### File: `frontend/www/api.js`

Added one constant and one method to the shared client.

- `MOCK_INVOICE` holds the Berlin hotel invoice JSON.
- `window.vatbackApi.mockInvoice` exposes the constant.
- `window.vatbackApi.submitInvoiceJson(payload)` posts a complete invoice
  JSON to the backend. It uses the `POST /invoices` endpoint.
  It defaults to `MOCK_INVOICE` when the caller passes no payload.

The `submitInvoiceJson` method posts JSON. It does not use the file upload.
The backend processes the payload with the same invoice flow that the file
upload uses. The flow returns an approved result for the Berlin invoice.

### File: `frontend/www/employee/index.html`

Changed the upload dialog submit handler.
The handler now calls `api.submitInvoiceJson(api.mockInvoice)`.
The handler no longer calls `api.uploadInvoice(...)`.

The submit flow works after the user selects a PDF or takes a photo.
The dialog requires a document before the submit button is enabled.
The button text changed from "The AI reads the invoice..." to
"Sending the invoice...".

The page still uses `window.vatbackApi` and `window.vatbackReceipts`.
No other frontend page changed.

## Step 7: Test the mock mode

### Build the mock database and start the server

```sh
cd /Users/magyariakos/Scratch/sigint-monorepo/backend
DATABASE_URL=sqlite:///./mock.db uv run python -m seed.mock_db
DATABASE_URL=sqlite:///./mock.db WISE_MODE=mock INVOICE_READER=demo \
  nohup uv run uvicorn app.main:app --port 8000 > /tmp/sigint-e2e.log 2>&1 &
```

The `make dev-mock` target runs the same two steps via the Makefile.

### Submit the mock invoice JSON

```sh
curl -s -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -d @backend/seed/documents/pass_de_hotel_berlin.expected.json
```

Result: `status` is `approved`. The matched transaction id is 2.
The refundable VAT total is 22.50 EUR. Two line outcomes are eligible.

### Verify the stored receipt

```sh
curl -s http://localhost:8000/receipts
```

The newest receipt is the Berlin hotel invoice. It is approved.
Its tax amount is 22.50 EUR.

### Verify the claims summary

The DE refund period shows the Berlin invoice's transaction id 2.
The DE refundable VAT total includes the Berlin amount.

## Step 8: Test the backend test suite

```sh
cd /Users/magyariakos/Scratch/sigint-monorepo/backend
uv run pytest -q
```

Result: 209 tests passed in about 2.2 seconds.

## Step 9: Check the frontend formatting

The pre-commit hook runs Prettier with the Tailwind plugin.
The committed `frontend/www/employee/index.html` was not Prettier-clean.
The plugin reorders Tailwind class names.
I ran Prettier to format the file so the hook passes.

```sh
cd /Users/magyariakos/Scratch/sigint-monorepo/frontend
pnpm exec prettier --check www/api.js www/employee/index.html
```

Result: all matched files use Prettier code style.

The `employee/index.html` diff includes Prettier class reordering.
The reordering is unrelated to the feature. It is required because the
pre-commit hook blocks a commit that is not Prettier-clean.

## Step 10: Check the JavaScript syntax

```sh
node --check frontend/www/api.js
```

The inline script in the employee page also passes `node --check`.

## Commits

Two atomic commits on the feature branch.

1. `feat(frontend): send a hardcoded mock invoice JSON to the backend`
   - Added `MOCK_INVOICE`, `mockInvoice`, and `submitInvoiceJson`.
   - Commit 638b922.

2. `feat(frontend): submit the mock invoice JSON from the upload flow`
   - Changed the employee upload dialog submit handler.
   - Commit e541bb3.

## Experiment notes

- The 42 sample invoices in `backend/seed/sample_invoices/` are for the
  demo `seed.db`, not the mock `mock.db`. They do not get approved.
- The Berlin hotel invoice is the only payload that a fresh mock database
  approves. The mock database adds its unclaimed transaction on purpose.
- The demo reader returns the same Berlin invoice. The hardcoded JSON
  path and the demo reader path produce the same approved result.
- Posting the same invoice twice after approval fails on the second post,
  because the matching transaction is already claimed.
