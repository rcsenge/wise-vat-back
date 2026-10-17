.PHONY: help install dev-backend seed test demo-reset demo-process

help:
	@echo "make install      Create the backend venv. Install the dependencies with uv."
	@echo "make dev-backend  Start Uvicorn with reload on port 8000."
	@echo "make seed         Create the database tables and load demo data."
	@echo "make test         Run the pytest suite."
	@echo "make demo-process Seed, process every invoice, print the claims."
	@echo "make demo-reset   Reset the simulator state. The backend must run."

install:
	cd backend && uv sync --extra dev

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

seed:
	cd backend && uv run python -m seed.seed

test:
	cd backend && uv run pytest

demo-process:
	cd backend && uv run python -m seed.process_demo

demo-reset:
	curl -X POST http://localhost:8000/simulate/reset
