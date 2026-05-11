# Manual Runtime Laptop Failure Execution Log Validator

Read-only validation of a manually filled `laptop_failure_execution_log.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json` (atomic `.tmp` -> replace, max 512 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-execution-log-validation`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_execution_log_validator.py`
