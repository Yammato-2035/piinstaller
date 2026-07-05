> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Test Summary

alleen-lezen summary of validated laptop failure test runs from `laptop_failure_execution_log_validation.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json` (atomic `.tmp` -> replace, max 256 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-test-summary`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_{OK|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_test_summary.py`
