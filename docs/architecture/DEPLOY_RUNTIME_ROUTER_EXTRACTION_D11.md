# Deploy Runtime Router Extraction (D.11)

**Phase:** D.11 · **Module-Reuse:** `runner_api_facade.build_plan_only_response`

## Ziel

Read-only / Status-Runtime-Routen aus `routes.py` nach `routes_runtime.py` — keine Runtime-Änderung, kein Restart, kein Execute.

## Lieferung

| Datei | Rolle |
|-------|-------|
| `backend/deploy/routes_runtime.py` | 8 POST plan-only/status via Facade |
| `backend/deploy/routes.py` | Orchestrator, −8 Handler, −8 Runner-Imports |

## Tests

`test_deploy_routes_runtime_v1` — 132 Deploy-Tests grün.

## Nächster Schritt

**E.1** — `app.py` Router-Slice
