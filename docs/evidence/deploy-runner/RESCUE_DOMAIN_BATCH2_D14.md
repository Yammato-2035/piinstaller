# Deploy Rescue Batch 2 D.14

**Kampagne:** A.4 · **Version:** 1.7.15.0

## Routen

| | Anzahl |
|---|--------|
| Vorher in `routes.py` (Rescue gesamt) | ~105 |
| Extrahiert Batch 2 | **21** |
| Bereits D.13 (`routes_rescue_readonly`) | 4 |
| Nachher `routes.py` Zeilen | 3704 |

## Neues Modul

`backend/deploy/routes_rescue_plan.py` — Tags `deploy-rescue-plan`

Routen: debian-live (7), dry-build (7), build-sandbox (7 inkl. final-gate)

## Verbleibend in routes.py

Execute-Routen (iso-build-execute, vm-test-execute, sandbox-copy execute, USB write, …)

## Registrierung

`router.include_router(deploy_rescue_plan_router)` in `deploy/routes.py`
