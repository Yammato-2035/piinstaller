# Manual Runtime Laptop Failure Run Selection

Read-only Auswahl manueller Laptop-Testläufe aus `failure_test_readiness.json`, `failure_test_sessions.json` und `failure_operator_checklists.json`. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json` (atomisch `.tmp` → Replace, max. 256 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-run-selection`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_READY`, `…_REVIEW_REQUIRED`, `…_BLOCKED`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_run_selector.py`
