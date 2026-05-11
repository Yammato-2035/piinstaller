# Manual Runtime Laptop Failure Execution Log Validator

Read-only Validierung eines manuell ausgefuellten `laptop_failure_execution_log.json`. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json` (atomisch `.tmp` -> Replace, max. 512 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-execution-log-validation`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_execution_log_validator.py`
