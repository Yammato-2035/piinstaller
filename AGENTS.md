# AGENTS.md

## Cursor Cloud specific instructions

### Overview

PI-Installer is a Raspberry Pi configuration assistant with a FastAPI backend (port 8000) and a React/Vite frontend (port 3001). No database is needed. See `README.md` for the full feature list.

### Services

| Service | Port | Start command |
|---------|------|---------------|
| Backend (FastAPI/Uvicorn) | 8000 | `cd backend && source venv/bin/activate && python3 -m uvicorn app:app --host 0.0.0.0 --port 8000` |
| Frontend (Vite dev server) | 3001 | `cd frontend && npm run dev` |

The Vite dev server automatically proxies `/api` requests to the backend at `http://127.0.0.1:8000` (configured in `frontend/vite.config.ts`).

### Gotchas

- The system Python on Ubuntu 24.04 requires `python3.12-venv` to be installed (`sudo apt-get install -y python3.12-venv`) before creating the backend virtual environment.
- The `npm run lint` script is defined in `frontend/package.json` but ESLint is **not** installed as a dependency and no `.eslintrc` config exists. Running lint will fail with `eslint: not found`.
- TypeScript strict checking (`npx tsc --noEmit`) reports pre-existing type errors in the codebase; however `npm run build` (Vite) succeeds because it does not run `tsc --noEmit`.
- Backend `app.py` is a large monolithic file (~11k lines). Expect slow initial import.
- For development with hot-reload, set `PI_INSTALLER_DEV=1` before starting the backend; this adds `--reload` to uvicorn.

### Testing

- **Backend health check:** `curl http://localhost:8000/health` → `{"status":"ok"}`
- **Backend version:** `curl http://localhost:8000/api/version`
- **Frontend build:** `cd frontend && npm run build`
- No automated test suite (no `pytest`, no `jest`/`vitest` tests) exists in this repository.
