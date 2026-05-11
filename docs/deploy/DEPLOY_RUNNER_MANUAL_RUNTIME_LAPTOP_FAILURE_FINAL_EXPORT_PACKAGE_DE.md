# Manual Runtime Laptop Failure Final Export Package

Read-only Exportpaket fuer den finalen Laptop-Failure-Teststand aus Final-Report, Summary, Validation und Execution-Log. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json` (atomisch `.tmp` -> Replace, max. 512 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-export-package`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_final_export_package.py`
