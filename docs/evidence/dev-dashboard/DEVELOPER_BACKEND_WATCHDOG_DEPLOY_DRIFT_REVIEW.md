# Developer Backend Watchdog — Deploy Drift Review

**Datum:** 2026-06-03  
**HEAD:** `8fba260`

## Workspace

| Artefakt | Vorhanden |
|----------|-----------|
| `scripts/dev-dashboard/check-backend-health.sh` | **yes** |
| `backend/core/dev_dashboard_backend_health.py` | **yes** |
| `GET /api/dev-dashboard/backend-health` in `backend/app.py` | **yes** |
| `frontend/.../BackendHealthPanel.tsx` | **yes** |
| Workspace `frontend/dist` (nach build) | `backend-health`, `failure_classification` in Bundle |

## `/opt/setuphelfer`

| Artefakt | Vorhanden |
|----------|-----------|
| Healthcheck-Skript | **no** |
| Backend Loader | **no** |
| `backend-health` Route in `app.py` | **no** (grep) |
| Frontend dist Watchdog-Strings | **no** (`opt_dist_no_watchdog_strings`) |

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Workspace Watchdog-Skript | **yes** |
| Workspace Backend API/Loader | **yes** |
| Workspace Frontend Panel | **yes** |
| `/opt` Watchdog-Skript | **no** |
| `/opt` Backend API/Loader | **no** |
| `/opt` Frontend Panel/Bundle | **no** |
| Deploy erforderlich | **yes** |
| **Status** | **deploy_required** |
