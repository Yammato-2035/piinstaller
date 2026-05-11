# Manual Runtime Laptop Failure Run Selection

Read-only selection of manual laptop test runs from `failure_test_readiness.json`, `failure_test_sessions.json`, and `failure_operator_checklists.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json` (atomic `.tmp` → replace, max 256 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-run-selection`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_READY`, `…_REVIEW_REQUIRED`, `…_BLOCKED`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_run_selector.py`
