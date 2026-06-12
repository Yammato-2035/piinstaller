# Deploy Runtime Router Slice (D.11)

**Ergebnis:** **8 Routen** extrahiert nach `routes_runtime.py`  
**facade_decoupling_d11:** true  
**allowed_to_execute:** false

## Gewählter Slice (8)

| # | Route | Methode | runner_id |
|---|-------|---------|-----------|
| 1 | `/runner/release/readiness` | POST | runner_release_readiness |
| 2 | `/runner/lab-readiness/unblock-plan` | POST | runner_lab_readiness_plan |
| 3 | `/runner/lab-readiness/status` | POST | runner_lab_readiness_status |
| 4 | `/runner/runtime-runbook/bundle` | POST | runner_runtime_runbook_bundle |
| 5 | `/runner/runtime-runbook/export` | POST | runner_runtime_runbook_export |
| 6 | `/runner/runtime-results/validate` | POST | runner_runtime_result_validator |
| 7 | `/runner/lab-readiness/acceptance` | POST | runner_lab_acceptance_aggregator |
| 8 | `/runner/lab-phase/consolidation` | POST | runner_lab_phase_consolidation |

## In routes.py verbleibend (runtime)

- `/runner/lab-readiness/acceptance/export`
- test-plan Routen (diagnostics)
- manual-runtime Ketten
- core `/plan`, `/execute`, `/write/*`

## Import-Reduktion

- Runner-Imports: 89 → **81** (−8)
