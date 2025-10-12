# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install

COPY src ./src
COPY config ./config
COPY main.py README.md ./
RUN uv sync --frozen

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/config /app/config
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/README.md /app/README.md

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "main.py"]
