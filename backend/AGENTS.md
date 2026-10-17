# AI Agent System Directives

You are an AI coding agent operating in the backend project of the SIGINT monorepo. The root `AGENTS.md` holds the project-wide rules. Read the root `AGENTS.md` first. Apply these project rules for all backend work.

Claude-specific operating notes live here: @CLAUDE.md

## 1. Project Configuration
- **Language:** Python (3.11 or newer)
- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Data Access:** SQLModel (SQLite by default, PostgreSQL optional)
- **Validation:** Pydantic v2 and Pydantic Settings
- **External HTTP:** httpx
- **AI Integration:** Local Ollama vision model reads invoice PDFs and photos (`integrations/ollama_reader.py`). Tests use a fake Ollama.
- **Test Runner:** Pytest
- **Linting:** Ruff
- **Type Checking:** mypy
- **Python Tooling:** uv (lockfile at `backend/uv.lock`)
- **Configuration:** environment variables and `.env` files
- **OpenAPI Contract:** `/openapi.json` drives the frontend project
- **Demo Goal:** A demoable backend that connects to the frontend

## 2. Backend Coding Standards
We optimize for safety, predictability, and simplicity. Apply these rules to all Python code.

### 2.1. Execution and Safety
- **Explicit Limits:** Bind all loops, retries, and page sizes. Give every external HTTP call a timeout.
- **Fail Early:** Validate all inputs at the API boundary with Pydantic schemas. Reject bad data immediately.
- **Responsive Loop:** Keep the event loop responsive. Never block it with synchronous external calls or heavy CPU work.

### 2.2. Complexity
- **Simplify Structure:** Keep the control flow strictly sequential. Minimize branches and nesting at the point of use.
- **Zero Technical Debt:** Write the optimal, final version on the first attempt. Do not leave `TODO: fix later` comments.

### 2.3. Naming and Structure
- **Casing:** Use `snake_case` for functions and variables. Use `PascalCase` for classes and type aliases. Use `UPPER_SNAKE_CASE` for constants.
- **Type Hints:** Annotate every function signature with full types. Use `app.domain.rules.Decision` and friends rather than bare `dict[str, Any]` where a type exists.
- **No Abbreviations:** Do not abbreviate names. Use the exact number of characters needed for absolute clarity.

### 2.4. Money and Domain Purity
- **Money Is Decimal:** Money is always `Decimal`, never `float`. Use `app.domain.money.Money` for all amounts.
- **Pure Domain:** The `domain/` module stays pure. It performs no I/O, no persistence, and no external calls.
- **Readable Decisions:** Every `Decision` carries a human-readable `reason`. The UI and the pitch display this reason.

### 2.5. Integrations and Configuration
- **Factory Only:** Never call Wise or other services directly. Use `app.integrations.factory.get_wise_client()`.
- **Mock Default:** Keep `WISE_MODE=mock` as the default for local development and tests.
- **Central Settings:** Read all configuration through `app.config.settings`. Never read environment variables at the point of use.

### 2.6. API Contracts and Testing
- **Pydantic Contracts:** Define every request and response body with Pydantic v2 schemas in `app/schemas/`.
- **OpenAPI as Truth:** The frontend derives its types from `/openapi.json`. Keep the contract stable and the responses serializable.
- **Pytest Coverage:** Add a unit test for every domain rule and Money operation. Run the suite with `make test`. Tests must not touch the network or real credentials.
- **Response Models:** Give every route a typed Pydantic `response_model`.
- **API Tests:** Test the app through the test client with a test database.
- **No Direct Dependency:** Never call FastAPI routers from tests. Test the domain directly or through the app test client.

### 2.7. Mock First
- Mock every component you can. Hardcode data where possible.
- Keep the mock output realistic. Return the same shapes as the real service.
- Use `WISE_MODE=mock` for the demo.
- The goal is a demoable backend that connects to the frontend.

## 3. Make Targets
Prefer the Makefile for repeatable steps. It keeps the commands identical for every contributor. All Python commands run through uv.

- `make install`: Create the backend venv and install dependencies with uv.
- `make dev-backend`: Start Uvicorn with reload on port 8000 via uv.
- `make seed`: Create the database tables via uv.
- `make test`: Run the pytest suite via uv.
- `make demo-reset`: Reset the simulator state.
