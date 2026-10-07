# syntax=docker/dockerfile:1

# ---- Stage 1: build the static Next.js frontend ----
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty API URL => the app calls relative URLs on whatever host serves it
# (FastAPI serves the export at the same origin, so cookies flow same-site).
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# ---- Stage 2: Python runtime with the FastAPI backend ----
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies from the uv lockfile first for layer caching.
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev

# Application code + legal templates + statically exported frontend.
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY catalog.json ./catalog.json
COPY --from=frontend-build /app/frontend/out ./frontend/out

ENV PATH="/app/backend/.venv/bin:$PATH" \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8000

EXPOSE 8000

# Delete any database left from a previous container filesystem, so SQLite
# is always created from scratch when the container is brought up.
CMD ["sh", "-c", "rm -f /app/prelegal.db && exec uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
