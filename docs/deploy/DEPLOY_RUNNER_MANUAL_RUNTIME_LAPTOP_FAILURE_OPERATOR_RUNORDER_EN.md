# Manual Runtime Laptop Failure Operator Runorder

Read-only operator run order from `laptop_failure_run_selection.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_operator_runorder.json` (atomic `.tmp` → replace, max 256 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-operator-runorder`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_{READY|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_operator_runorder.py`
