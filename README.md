# Prelegal

A platform for drafting common legal agreements

## Status

⚠️ **Project in Progress** - This project is currently under active development and will be completed in approximately 1 week.

## Overview

Prelegal is a platform designed to help users draft common legal agreements quickly and easily. The platform provides templates and guidance for creating various types of legal documents.

Documents are currently created through an **AI chat**: the assistant asks about the required fields conversationally, fills a live preview as you answer, and unlocks the PDF download once the document is complete (powered by LiteLLM via OpenRouter — see `backend/.env.example` for the required `OPENROUTER_API_KEY`; without it the app still runs and chat requests return 503).

## Quick start (Docker)

The whole app (FastAPI backend + statically built Next.js frontend + SQLite) runs in one container, available at **http://localhost:8000**.

```bash
# Mac
scripts/start-mac.sh      # Start
scripts/stop-mac.sh       # Stop

# Linux
scripts/start-linux.sh
scripts/stop-linux.sh
```

```powershell
# Windows
scripts\start-windows.ps1
scripts\stop-windows.ps1
```

The SQLite database is created from scratch each time the container starts.

AI chat needs an `OPENROUTER_API_KEY` in a repo-root `.env` (compose passes it into the container; see `backend/.env.example`). The app works without it — chat turns return 503 until a key is provided.

## Development

### Backend (FastAPI, uv project)

```bash
cd backend
uv sync            # or: pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload   # run from the repo root
```

API docs: http://localhost:8000/docs

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 (API on :8000 via .env.local)
npm run build      # static export to frontend/out, served by FastAPI
```

### Tests

```bash
python -m pytest   # unit + integration tests (backend/tests/)
```
