# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Setuphelfer (repo: piinstaller) is a configuration assistant with a FastAPI backend (port 8000) and a React/Vite frontend (port 3001). No database is required for basic API smoke tests. See `README.md` for the full feature list.

Cloud Agent bootstrap lives in `.cursor/environment.json`:

- `install` — Python venv + backend deps + `frontend` `npm ci`
- `start` — starts the backend on `127.0.0.1:8000` if it is not already healthy

### Services

| Service | Port | Start command |
|---------|------|---------------|
| Backend (FastAPI/Uvicorn) | 8000 | `cd backend && ./venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000` |
| Frontend (Vite dev server) | 3001 | `cd frontend && npm run dev` |

Vite proxies `/api` to `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).

### Gotchas

- Ubuntu needs `python3.12-venv` before creating `backend/venv`.
- Prefer workspace/unit tests with mocks for most agent work. Live `/opt/setuphelfer` runtime tests require Phase 0 gates (`docs/dev-dashboard/PHASE0_RUNTIME_GATE.md`).
- `npm run lint` may fail if ESLint is not installed; prefer `npm run build` for frontend smoke.
- Backend import can be slow on first start (`backend/app.py` is large).

### Smoke checks

- `curl -sf http://127.0.0.1:8000/health`
- `curl -sf http://127.0.0.1:8000/api/version`
- `cd frontend && npm run build`
- `cd backend && ./venv/bin/python -m pytest tests/ -q --tb=line -x` (subset OK for quick checks)
