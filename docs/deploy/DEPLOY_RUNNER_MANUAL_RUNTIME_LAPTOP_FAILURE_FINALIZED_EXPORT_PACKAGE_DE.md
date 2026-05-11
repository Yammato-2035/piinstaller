# Manual Runtime Laptop Failure Finalized Export Package

Read-only finalisiertes Exportpaket aus Acceptance, Snapshot, Timeline, Export, Report, Summary, Validation und Execution-Log. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_finalized_export_package.json` (atomisch `.tmp` -> Replace, max. 512 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-finalized-export-package`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_finalized_export_package.py`
