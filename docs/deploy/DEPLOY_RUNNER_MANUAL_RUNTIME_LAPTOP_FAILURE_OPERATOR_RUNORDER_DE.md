# Manual Runtime Laptop Failure Operator Runorder

Read-only Operator-Reihenfolge aus `laptop_failure_run_selection.json`. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_operator_runorder.json` (atomisch `.tmp` → Replace, max. 256 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-operator-runorder`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_{READY|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_operator_runorder.py`
