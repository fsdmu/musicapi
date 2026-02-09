# ---------- Stage 1: Builder (Debian-based) ----------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy lockfiles
COPY pyproject.toml uv.lock ./

# Install dependencies into .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---------- Stage 2: Runtime (Debian-based) ----------
FROM python:3.12-slim

WORKDIR /app

# Copy the venv from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY ./src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Ensure logs dir exists
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

EXPOSE 8080

CMD ["python", "src/__main__.py"]