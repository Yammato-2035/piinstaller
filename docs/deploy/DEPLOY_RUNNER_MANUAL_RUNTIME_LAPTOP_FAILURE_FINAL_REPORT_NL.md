> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Report

alleen-lezen final report from `laptop_failure_test_summary.json` with status, recommendation, and SHA256 of summary raw bytes. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_report.json` (atomic `.tmp` -> replace, max 256 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-final-report`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_{OK|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_final_report.py`
