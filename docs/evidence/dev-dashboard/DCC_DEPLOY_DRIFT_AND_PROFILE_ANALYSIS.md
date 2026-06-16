# DCC Deploy Drift and Profile Analysis

Datum: 2026-06-02

## Basisstatus

- HEAD: `5bb72c8`
- Branch: `main`
- Service-Status:
  - `setuphelfer-backend.service`: `active`
  - `setuphelfer.service`: `active`
- Runtime-Gate:
  - `check-runtime-deploy-gate: LEGACY_GATE_NON_PROFILE_AWARE`
  - Profil-Gate separat: `check-runtime-profile-deploy-gate.sh` -> `OK` (informational legacy exit)

## Runtime-Profil und Pfad

- `GET /api/version`: `HTTP 200`
- `install_profile`: `release`
- `backend_runtime_path`: `/opt/setuphelfer/backend`
- `GET /openapi.json`: `HTTP 200`
- `GET /api/dev-dashboard/status`: `HTTP 404` mit `PROFILE_ROUTE_BLOCKED`

## Bewertung PROFILE_ROUTE_BLOCKED

- Im aktiven `release`-Profil ist `PROFILE_ROUTE_BLOCKED` für `/api/dev-dashboard/status` erwartbar.
- Das ist **kein** Nachweis für einen Backend-Absturz des Development Control Center.

## Deploy-Drift

- Relevante Workspace-Dateien sind gegenüber `/opt/setuphelfer` teilweise `deploy_drift` oder `workspace_only`.
- Besonders wichtig:
  - `backend/app.py` -> `deploy_drift`
  - `backend/rescue_agent/*.py` -> `workspace_only` (in `/opt` nicht vorhanden)
- Folge:
  - Neue Workspace-Felder wie `rescue_agent_router_status` können live noch nicht sichtbar sein.
  - Restart ohne Runtime-Sync reicht hier nicht aus.

## DCC-Klassifikation

`running_profile_blocked` + `deploy_drift`

- Runtime läuft.
- DCC-Statusroute ist im Profil geblockt.
- Workspace-Änderungen sind nicht vollständig in der aktiven Runtime.
