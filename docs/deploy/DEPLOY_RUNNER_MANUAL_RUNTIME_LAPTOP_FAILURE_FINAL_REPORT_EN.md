# Manual Runtime Laptop Failure Final Report

Read-only final report from `laptop_failure_test_summary.json` with status, recommendation, and SHA256 of summary raw bytes. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_report.json` (atomic `.tmp` -> replace, max 256 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-report`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_final_report.py`
