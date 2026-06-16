# Development Control Center Startability Fix Result

Datum: 2026-06-02  
Ergebnis: `static_startability_restored_with_runtime_constraints`

## Ursache

- Kein harter Crash durch Rescue-Agent-Code reproduzierbar.
- Hauptsignal war Profil-/Runtime-Kontext:
  - `release` blockiert `/api/dev-dashboard/status` absichtlich.
  - Workspace-Importtests ohne installierte Backend-Dependencies (`fastapi`, `pydantic`) liefern Fehlalarme.

## Minimaler Fix

- `backend/app.py` gehärtet:
  - Startup-Diagnostikfelder eingeführt:
    - `rescue_agent_router_status = ok|disabled_by_profile|import_failed|unknown`
    - `rescue_agent_router_error` (gekürzte, nicht-sensitive Meldung)
  - Router-Registration bleibt defensiv in `try/except`; Backend startet weiter bei Importfehlern.
  - Felder werden in `/api/version` ausgegeben.

## Verifikation

- Python `py_compile` auf geänderten Backend-Dateien: OK
- Frontend `npm run build`: OK
- Frontend `npm test -- --run`: OK
- Shell-Syntaxchecks: OK
- Runtime-Python ermittelt:
  - Service läuft mit `/opt/setuphelfer/backend/venv/bin/python3`
  - `fastapi`/`pydantic` in dieser Runtime vorhanden (`0.135.1` / `2.12.5`)
- Backend-Importtest mit Runtime-Python (`sys.path` auf Workspace):
  - `IMPORT_OK` für Fleet/Rescue-Agent-Module
  - `APP_IMPORT_OK`
- `/api/version` live enthält neue Routerdiagnosefelder noch **nicht** (`<missing>`), konsistent mit belegtem Deploy-Drift.

## Rescue-Agent-Status

- Router: `disabled_by_profile` in `release`, `ok`/`import_failed` in aktivem Lab-Profil
- Panel: `enabled` (kein temporäres Abschalten nötig)
- E2EE: `contract_stub_only`
- nftables: `preview_only_apply_false`

## Offene Punkte

- Ohne Operator-Freigabe kein Runtime-Sync/Restart.
- Relevante Drift zwischen Workspace und `/opt` bleibt bestehen (`operator_runtime_sync_required`).
- pytest ist lokal verfügbar, aber für neue Tests war `PYTHONPATH=backend:.` erforderlich.
