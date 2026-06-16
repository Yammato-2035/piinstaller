# Development Control Center Start Failure Analysis

Datum: 2026-06-02  
Modus: strict static/debug, kein Deploy/Restart

## Snapshot

- HEAD: `5bb72c8`
- Branch: `main`
- Runtime-Gate: `check-runtime-deploy-gate: LEGACY_GATE_NON_PROFILE_AWARE` (Profil `release`, `/api/dev-dashboard/status` erwartbar 404)
- Service-Status:
  - `setuphelfer-backend.service`: `active`
  - `setuphelfer.service`: `active`

## HTTP-Status

- `GET /api/version` -> `HTTP 200`
- `GET /api/dev-dashboard/status` -> `HTTP 404 PROFILE_ROUTE_BLOCKED` (Release-Profil)
- `GET /openapi.json` -> `HTTP 200`

## Befunde zu Startfehlern

- Backend-Service läuft und antwortet.
- Kein Runtime-Traceback aus `journalctl` belegbar (`-- No entries --`, lokale Journal-Sicht eingeschränkt).
- Workspace-Importtest (`python3` ohne Projekt-Dependencies) zeigt:
  - `ModuleNotFoundError: fastapi`
  - `ModuleNotFoundError: pydantic`
  - Das ist ein lokales Test-Environment-Problem, **nicht** automatisch ein Runtime-Service-Crash.
- Frontend:
  - `npm run build` -> OK
  - `npm test -- --run` -> OK (13 Dateien / 54 Tests)

## Erste Fehlerklassifikation

`deploy_drift`

Begründung: Laufende Runtime ist gesund (`/api/version` 200), Workspace-Check ohne Backend-Dependencies schlägt erwartbar fehl, und `/api/dev-dashboard/status` ist in `release` absichtlich blockiert. Ein reproduzierbarer neuer Code-Crash durch Rescue-Agent-Stub wurde in diesem Lauf nicht nachgewiesen.

## Betroffene/prüf-relevante Dateien

- `backend/app.py`
- `backend/core/install_profile.py`
- `backend/rescue_agent/routers.py`
- `frontend/src/components/dev-dashboard/LabSessionsPanel.tsx`
- `frontend/src/components/dev-dashboard/RescueAgentPanel.tsx`
