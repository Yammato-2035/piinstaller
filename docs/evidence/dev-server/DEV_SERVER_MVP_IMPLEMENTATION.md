# Development Server MVP — Implementation Evidence

**Date:** 2026-05-30
**HEAD (start):** 0f8aae4
**Branch:** main
**Runtime gate:** FAILED (check-runtime-deploy-gate exit 14) — `runtime_gate_blocked_static_and_unit_only`

## Implemented

| Component | Path |
|-----------|------|
| Config | `backend/devserver/config.py` |
| Models/Schemas | `backend/devserver/models.py`, `schemas.py` |
| Storage | `backend/devserver/storage.py` |
| Redaction | `backend/devserver/redaction.py` |
| Ingest | `backend/devserver/ingest.py` |
| SSH read-only | `backend/devserver/ssh_readonly.py` |
| Actions | `backend/devserver/actions.py` |
| Prompt stub | `backend/devserver/prompt_candidates.py` |
| Router | `backend/devserver/routers.py` |
| App registration | `backend/app.py` (include_router) |
| Frontend API | `frontend/src/api/devServerApi.ts` |
| Dashboard panel | `frontend/src/components/devserver/DevelopmentServerPanel.tsx` |
| Cockpit integration | `frontend/src/pages/ExternalDevelopmentControlCenter.tsx` |
| Example env | `.env.example.devserver` |

## API routes (code)

- `/api/dev-server/health`
- `/api/dev-server/nodes`, `/nodes/{id}`
- `/api/dev-server/reports`, `/reports/{id}`
- `/api/dev-server/ingest/report`
- `/api/dev-server/actions`, `/actions/{id}`
- `/api/dev-server/summary`
- `/api/dev-server/nodes/{id}/ssh/*` (4 profiles)
- `/api/dev-server/prompt-candidates/from-reports`

## Runtime smoke

**Not performed** — runtime gate red. Live OpenAPI on port 8000 may not include new routes until deploy/restart: `runtime_deploy_or_restart_required`.

## Security defaults verified in code/tests

- `SETUPHELFER_DEV_SERVER_ENABLED=false` default
- `SETUPHELFER_DEV_SERVER_ACCEPT_PUBLIC_UPLOADS=false` default
- `SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=false` default
- No backup/restore/repair/write routes
- SSH allowlist + forbidden token validation

## Tests

```bash
cd backend && PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_devserver_*' -v
# Ergebnis: 44 tests OK (7 skipped — FastAPI/TestClient lokal nicht installiert)

cd frontend && npm test -- --run DevelopmentServerPanel
# Ergebnis: 3 tests passed
```

## Foreign uncommitted changes (pre-existing)

Rescue ISO build, ckb-next, lab acceptance evidence, VERSION, unrelated frontend panels — not part of this MVP diff intent.
