# Manual Runtime Laptop Failure Finalized Export Package

Read-only finalized export package from acceptance, snapshot, timeline, export, report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_finalized_export_package.json` (atomic `.tmp` -> replace, max 512 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-finalized-export-package`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_finalized_export_package.py`
