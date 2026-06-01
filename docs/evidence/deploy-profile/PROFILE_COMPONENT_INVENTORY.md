# Profil-Komponenten-Inventar

**Stand:** 2026-05-31 · Inventar: `profile_file_inventory.txt` (5000 Pfade, gekürzt)

## Core / Release

- `backend/app.py` (Kern-API, Backup, Restore, …)
- `backend/core/*` (ohne reine Dev-Hilfsmodule)
- `frontend/src/pages/*` (Produkt-UI)
- `config/version.json`
- `packaging/`, `debian/`

## Development Control Center

- `backend/core/dev_dashboard.py`
- `backend/core/dev_control_center_summary.py`
- `frontend/` Dev-Dashboard-Routen (Cockpit)

## Development Server / Dev Dashboard API

- `backend/devserver/`
- `backend/devserver_agent/`
- `/api/dev-server`, `/api/dev-dashboard`

## Fleet Sessions

- `backend/fleet/routers.py`
- `backend/core/fleet_session_state.py`
- `/api/fleet/*`

## Dev Diagnostics

- `backend/core/dev_diagnostic_export.py`
- `/api/dev-diagnostics/*`

## Rescue Remote

- `backend/rescue_remote/`
- `scripts/rescue-live/setuphelfer-rescue-remote-agent.sh`
- `/api/rescue-remote/*`

## Rescue-Live / QEMU (Repo, nicht Release-Runtime)

- `scripts/rescue-live/*`
- `build/rescue/` (Artefakte, nicht ins Release-Bundle)

## Frontend Dev-UI

- `frontend/src/config/buildProfile.ts`
- Lab Sessions, Dev Diagnostics Copy, Rescue Remote Tab (nur Lab-Build)

## Evidence / Runtime-Logs

- `docs/evidence/runtime-results/**`
- `build/runtime/rescue-remote/` (JSONL Jobs)

## Potenzielle Public-Exposure-Stellen

- Backend-Bind `0.0.0.0` ohne Operator-Freigabe
- Öffentliche Dev-Control-Hosts (blockiert durch Profil + Gate)
- Push in **public** Repository (NDA-Risiko, blockiert)

## Im Release-Profil verboten (Runtime + API)

| Bereich | Pfade |
|---------|-------|
| Backend-Pakete | `backend/fleet/`, `backend/dev_diagnostics/`, `backend/rescue_remote/` |
| API | `/api/fleet`, `/api/dev-diagnostics`, `/api/rescue-remote`, `/api/dev-dashboard`, `/api/dev-server` |
| Evidence in Bundle | `docs/evidence/runtime-results/rescue-remote` |

## Im Local-Lab-Profil erlaubt

- Fleet, Dev Diagnostics, Dev Dashboard, Dev Server
- Rescue Remote **read-only** (`write_runbooks_enabled=false`)
- `public_exposure_allowed=false` (Pflicht)
