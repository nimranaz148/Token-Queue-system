# Multi-stage Dockerfile for FastAPI backend
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY apps/api/pyproject.toml apps/api/uv.lock* ./

RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY apps/api /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
