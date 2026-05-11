# Manual Runtime Laptop Failure Final Report

Read-only Abschlussbericht aus `laptop_failure_test_summary.json` mit Status, Empfehlung und SHA256 der Summary-Rohbytes. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_final_report.json` (atomisch `.tmp` -> Replace, max. 256 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-report`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_final_report.py`
