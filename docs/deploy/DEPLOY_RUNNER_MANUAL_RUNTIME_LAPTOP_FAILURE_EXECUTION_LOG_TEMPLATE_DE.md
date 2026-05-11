# Manual Runtime Laptop Failure Execution Log Template

Read-only Generator eines leeren manuellen Ausfuehrungsprotokolls aus `laptop_failure_operator_runorder.json`. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json` (atomisch `.tmp` -> Replace, max. 512 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-execution-log-template`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_execution_log_template.py`
