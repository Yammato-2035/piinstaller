# App-Decomposition — Phase-0-Status

**Stand:** 2026-06-02  
**Auftrag:** STRICT MODE — App.py Decomposition (kein Deploy, kein Restart, kein ISO)

## Git / Workspace

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `5bb72c8` |
| Uncommitted | Ja (Bootstrap + Rescue-Agent + Evidence) |

## Runtime

| Feld | Wert |
|------|------|
| `setuphelfer-backend.service` | active |
| `install_profile` (API) | `release` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| Runtime-Python | `/opt/setuphelfer/backend/venv/bin/python3` |

## Gates

| Gate | Ergebnis |
|------|----------|
| `check-runtime-deploy-gate.sh` | non-zero (legacy: `/api/dev-dashboard/status` HTTP 404 im Profil `release`) |
| `check-runtime-profile-deploy-gate.sh` | Exit 0 (profilbewusst) |
| Deploy-Drift | **rot/gelb** — Workspace enthält `app_bootstrap/`, `rescue_agent/`, geänderte `app.py`; `/opt` noch ohne diese Module |

## HTTP-Kernendpunkte (Port 8000)

| Endpoint | Ergebnis |
|----------|----------|
| `GET /api/version` | HTTP 200 |
| `GET /openapi.json` | HTTP 200 (bekannt) |
| `GET /api/dev-dashboard/status` | HTTP 404 `PROFILE_ROUTE_BLOCKED` (release erwartbar) |

## Erlaubte Tests in diesem Lauf

- Workspace-Import, `py_compile`, pytest mit `PYTHONPATH=backend:.` und `backend/venv/bin/pytest`
- Frontend build/test (unverändert grün)
- **Keine** Live-Abnahme als „grün“ für neue Router-Diagnosefelder (`rescue_agent_router_*` live noch `<missing>` wegen Deploy-Drift)

## Operator-Sync

Deploy/Restart **nicht** ausgeführt — Status: `ready_for_operator_deploy_sync`.
