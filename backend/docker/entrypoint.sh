#!/usr/bin/env sh
# Container entrypoint for the SIGINT backend.
# It waits for Ollama on the host, seeds the demo database, then starts Uvicorn.
# The demo invoice reader needs no Ollama. The script then skips the wait.
set -eu

OLLAMA_URL="${OLLAMA_URL:-http://host.docker.internal:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5vl:7b}"
READY_TIMEOUT="${OLLAMA_READY_TIMEOUT_SECONDS:-120}"

if [ "${INVOICE_READER:-demo}" = "demo" ]; then
    echo "[entrypoint] The demo invoice reader is active. The backend does not wait for Ollama."
else
echo "[entrypoint] The backend waits for Ollama at ${OLLAMA_URL}."

OLLAMA_URL="$OLLAMA_URL" OLLAMA_MODEL="$OLLAMA_MODEL" READY_TIMEOUT="$READY_TIMEOUT" python3 - <<'PY'
import json
import os
import time
import urllib.request

base_url = os.environ["OLLAMA_URL"].rstrip("/")
model = os.environ["OLLAMA_MODEL"]
deadline = time.monotonic() + float(os.environ["READY_TIMEOUT"])
last_status = "Ollama was not contacted yet."

while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(base_url + "/api/tags", timeout=5) as response:
            data = json.load(response)
            names = [item.get("name", "") for item in data.get("models", [])]
            if model in names or any(name.startswith(model) for name in names):
                print(f"[entrypoint] Ollama model '{model}' is ready.")
                raise SystemExit(0)
            last_status = f"the server runs but the model '{model}' is missing."
    except Exception as error:
        last_status = str(error)
    time.sleep(3)

print(f"[entrypoint] Ollama is not ready within the timeout. Last status: {last_status}.")
print("[entrypoint] The API starts anyway. Uploads return a clear 503 error until Ollama is ready.")
raise SystemExit(0)
PY
fi

if [ "${MOCK_DB:-false}" = "true" ]; then
    echo "[entrypoint] The mock database replaces the demo database."
    /app/.venv/bin/python -m seed.mock_db
elif [ "${SEED_ON_START:-true}" = "true" ]; then
    echo "[entrypoint] The seed refreshes the demo database."
    /app/.venv/bin/python -m seed.seed
fi

echo "[entrypoint] Uvicorn starts on port 8000."
exec /app/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
