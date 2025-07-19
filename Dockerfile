# ---- Builder stage ----
FROM python:alpine3.22 AS builder

WORKDIR /app

ENV PATH="/root/.local/bin:/app/.venv/bin:$PATH"

# Copy dependency files and install dependencies with uv.lock
COPY pyproject.toml uv.lock ./

# Install curl, bash, build-base, install uv
RUN apk add --no-cache bash build-base curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    uv venv .venv && \
    . .venv/bin/activate && \
    uv sync --locked
    
# RUN uv venv .venv && \
#     . .venv/bin/activate && \
#     uv sync --locked

# Copy app source code
COPY app.py ./

# ---- Final stage ----
FROM python:alpine3.22

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app.py ./

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
