# Manual Runtime Laptop Failure Final Export Package

Read-only export package for final laptop failure test state from final report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json` (atomic `.tmp` -> replace, max 512 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-export-package`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_final_export_package.py`
