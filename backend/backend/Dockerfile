# The Python backend image for the SIGINT service.
# It runs FastAPI behind Uvicorn on port 8000.
# Ollama runs on the host machine. The container reaches it through host.docker.internal.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install the locked dependencies before the source. The layer stays cached.
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.11.7 \
    && uv sync --frozen --no-dev --no-install-project

# Copy the application source. Then link the editable project into the venv.
COPY app ./app
COPY seed ./seed
COPY schemas ./schemas
RUN uv sync --frozen --no-dev

COPY docker/entrypoint.sh /usr/local/bin/container-entrypoint.sh
RUN chmod +x /usr/local/bin/container-entrypoint.sh

EXPOSE 8000

CMD ["/usr/local/bin/container-entrypoint.sh"]
