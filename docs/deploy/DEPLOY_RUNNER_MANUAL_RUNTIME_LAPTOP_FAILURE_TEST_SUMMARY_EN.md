# Manual Runtime Laptop Failure Test Summary

Read-only summary of validated laptop failure test runs from `laptop_failure_execution_log_validation.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json` (atomic `.tmp` -> replace, max 256 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-test-summary`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_test_summary.py`
