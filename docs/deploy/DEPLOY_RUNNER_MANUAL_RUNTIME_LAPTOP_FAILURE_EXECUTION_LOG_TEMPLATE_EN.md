# Manual Runtime Laptop Failure Execution Log Template

Read-only generator of an empty manual execution log from `laptop_failure_operator_runorder.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json` (atomic `.tmp` -> replace, max 512 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-execution-log-template`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_execution_log_template.py`
