# Repository Findings

This file records the dead code and the discrepancies found in a full repository review.
An AI agent wrote the review on 2026-10-17.
The review read every tracked file and ran the test suite.
The suite passed 186 tests.

The whole repository was built in about 12 hours (154 commits, 5 agents).
Most findings below come from that fast development pace.

## Context

The repository is a "SIGINT / Wise VAT Back" demo.
An employee scans a receipt.
A local Ollama AI reads the PDF or the photo.
The backend validates the invoice, matches a card transaction, and applies per-country VAT rules.
The employer page shows the total claimable refund.

The review scope covers the root files, `backend/`, and `frontend/`.

## Dead code

### Backend stubs (never called)

The backend exposes a subsystem of stub routes.
The frontend calls none of them.

| Route | File | State |
| --- | --- | --- |
| `/accounts`, `/accounts/{id}/transactions` | `backend/app/api/accounts.py` | Returns empty lists with a TODO. |
| `/rates` | `backend/app/api/rates.py` | Always returns `rate: null`. |
| `/events/stream` | `backend/app/api/events.py` | Emits a heartbeat every 15 seconds. No client connects. |
| `/simulate/card-swipe`, `/skip-time`, `/reset` | `backend/app/api/simulate.py` | Returns `{"todo": ...}` stubs. |
| `/simulate/reset` | `backend/app/simulator/events.py` | Does nothing. `make demo-reset` calls it. |

The Makefile target `demo-reset` curls `/simulate/reset`.
The endpoint returns a stub and resets nothing.
A human or an agent runs the target and believes the reset worked.

### Backend integration layer (unused)

- `backend/app/integrations/factory.py` defines `get_wise_client()`.
  Nothing calls it.
- `backend/app/integrations/wise_client.py`, `wise_mock.py`, `wise_real.py`
  have every method `raise NotImplementedError`.
  A TODO comment is the only reference.
- `backend/app/integrations/ai.py` defines `explain_decision()` and `parse_rule()`.
  No file imports the module.
- `backend/app/integrations/vies.py` is a mock.
  It rejects only the hardcoded string `XX12345678`.
- `backend/seed/rates_cache.json` holds only `null` rates.
  A TODO comment is the only reference.

### Backend unused settings and dependencies

- Settings never read: `anthropic_api_key`, `anthropic_model`,
  `wise_api_token`, `wise_sandbox_url`, `wise_real_url`.
- The `anthropic` dependency is in `uv.lock` but never imported.
- The default `anthropic_model` value `claude-sonnet-5-5` does not exist.
- `backend/.gitignore` whitelists `!/config/**`.
  No `config/` directory exists in either project.

### Backend unused domain code

- `backend/app/domain/money.py` defines the `Money` class,
  plus `convert()`, `rounded()`, and `zero()`.
  Only the tests use them.
  The app code uses raw `Decimal` with `quantize` everywhere.
  This contradicts `backend/AGENTS.md` section 2.4.
  Two parallel money patterns exist.

### Frontend generated files

- `frontend/www/style.css` is the minified Tailwind build output.
  It is committed.
- `frontend/www/vendor/neptune/` is a copy of the Neptune package.
  The `copy:neptune` script generates it.
  It is committed.
- The Docker frontend serves these files without a build step.
  The commit is intentional, but the CSS has two sources of truth.

### Stale ignore rules

- The root `.gitignore` re-ignores `fonts/inter/`, `noto-sans-kr/`,
  and other font paths.
  None of these paths exist anymore.
  The `copy:neptune` script now copies eight fonts flat into `fonts/`.

## Discrepancies

### Nested stale tree

- `backend/backend/` holds about 89 MB of leftovers.
  It contains `.venv`, `.pytest_cache`, `vatback.db`,
  `vatback_backend.egg-info`, and empty `app/ seed/ tests/` skeletons.
- Commit `e23b5a5` "flattened" the backend project.
  It moved the sources up but left this carcass behind.
- Nothing there is tracked.
  Still, `find`, editors, and glob searches trip over the files.

### Branding split

- Commit `12650e0` renamed the page headers to "SIGINT".
- The `<title>` tags still say "vatback".
  This affects `employer.html` and `countdown.html`.
- The employee page still says "vatback - Employee Scanner".
- Two favicons exist: `favicon.svg` and `favicon-employer.svg`.
- `index.html` has no favicon.

### Marketing page in the product

- `/countdown` shows "money the world loses in five minutes".
  The constant `LOSS_PER_YEAR_EUR` equals 20 billion.
- This page is a pitch gimmick.
  It is merged into the real navigation.
- A later commit re-themed it instead of removing it.

### Docs describe features that do not exist

- `frontend/AGENTS.md` and `frontend/DESIGN.md` claim a Capacitor mobile app.
  No Capacitor code, configuration, or dependency exists.
- `backend/DESIGN.md` says only Austria and Germany are supported.
  It says another team handles uploads.
  Reality: the backend supports nine countries and uses local Ollama.
- These stale specs mislead an agent that trusts them.

### Docs contradict the code standards

- `backend/AGENTS.md` and `frontend/AGENTS.md` say
  "do not leave TODO comments".
- The app contains 25 TODO and NotImplementedError markers.
- An agent that trusts the docs over the code gets surprised.

### Configuration residue

- `backend/app/config.py` default CORS origins include port 5173.
  That is the Vite dev-server port.
  No Vite server exists anymore.
- `backend/tests/test_cors.py` asserts on that origin.

### Silent no-op make target

- `make demo-reset` curls the stub `/simulate/reset`.
  The endpoint does nothing.

## Counterbalance

The core flow is in good shape.

- 186 tests pass in about 1.3 seconds.
- A golden corpus test suite covers over 40 cases.
- The mock database is deterministic.
- The tests freeze the reference date for the claim deadline.
- The claim deadline rule is isolated and well tested.
- A sync test keeps the Pydantic contract equal to the JSON Schema.

The reliable test loop offsets much of the mess above.

## Estimated agent velocity gain

This estimate is a judgment, not a measurement.
Four effects drive it: stub misdirection, extra reading,
risk of building on a stub, and navigation noise.
The live test suite pulls the number down because failure is cheap to detect.

Estimated velocity gain after a cleanup:

| Task type | Gain |
| --- | --- |
| Integration, Wise, rates, simulate, events | 30 to 40 percent |
| General feature work | 10 to 15 percent |
| Pure domain work (rules, money, seed) | 0 to 5 percent |
| Average across all tasks | 15 to 25 percent |

About half the gain comes from one action.
Either implement the Wise, simulate, and events subsystem,
or remove the dead parts and update `README.md`.
The next half comes from deleting the nested tree
and aligning the stale docs.

## Recommended cleanup order

1. Delete the `backend/backend/` leftover tree.
2. Remove or clearly mark the never-called integration and simulator stubs.
3. Fix the misleading docs (the Capacitor claim, `DESIGN.md`, the model default).
4. Reconcile the `Money` type with the raw `Decimal` code.
5. Unify the branding and the `<title>` residue.
6. Remove the stale ignore rules and the CORS port 5173 entry.
