> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Finalized Export Package

alleen-lezen finalized export package from acceptance, snapshot, timeline, export, report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_finalized_export_package.json` (atomic `.tmp` -> replace, max 512 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-finalized-export-package`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_{OK|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_finalized_export_package.py`
