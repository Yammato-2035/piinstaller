# Backend Runtime Restart — Precheck

Datum: 2026-05-28

## Vorher-Zustand

- Branch: `main`
- HEAD: `68016a5`
- Letzter Commit: `68016a5 Document backend runtime unavailable triage`
- `setuphelfer-backend.service`: `active (running)`
- Port `127.0.0.1:8000`: LISTEN
- Prozess: `uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1`
- `/api/version`: Timeout
- `/health`: Timeout
- Runtime-Gate: `/api/version HTTP 000000` (blocked)

## Freigabe

- Operator-Freigabe vorhanden: `BACKEND_RESTART_FREIGEGEBEN`
