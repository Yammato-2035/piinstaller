> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Execution Log Validator

alleen-lezen validation of a manually filled `laptop_failure_execution_log.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json` (atomic `.tmp` -> replace, max 512 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-execution-log-validation`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_{OK|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_execution_log_validator.py`
