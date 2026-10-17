# The mock mode uses its own database file. The demo database stays untouched.
MOCK_DATABASE_URL := sqlite:///./mock.db

.PHONY: help install dev-backend dev-mock mock-db seed test eval-ai golden demo-reset demo-process

help:
	@echo "make install      Create the backend venv. Install the dependencies with uv."
	@echo "make dev-backend  Start Uvicorn with reload on port 8000 on every interface."
	@echo "make dev-mock     Build the mock database. Start Uvicorn on it in mock mode."
	@echo "make mock-db      Build the mock database with data for every country."
	@echo "make seed         Create the database tables and load demo data."
	@echo "make test         Run the pytest suite. Includes the golden corpus."
	@echo "make eval-ai      Measure the AI extraction accuracy over the sample PDFs."
	@echo "make golden       Regenerate the golden outcome sidecars."
	@echo "make demo-process Seed, process every invoice, print the claims."
	@echo "make demo-reset   Reset the simulator state. The backend must run."

install:
	uv sync --extra dev

dev-backend:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-mock: mock-db
	DATABASE_URL=$(MOCK_DATABASE_URL) WISE_MODE=mock uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

mock-db:
	DATABASE_URL=$(MOCK_DATABASE_URL) uv run python -m seed.mock_db

seed:
	uv run python -m seed.seed

test:
	uv run pytest

eval-ai:
	uv run python -m evaluation.evaluate_extraction

golden:
	uv run python -m seed.generate_golden

demo-process:
	uv run python -m seed.process_demo

demo-reset:
	curl -X POST http://localhost:8000/simulate/reset
