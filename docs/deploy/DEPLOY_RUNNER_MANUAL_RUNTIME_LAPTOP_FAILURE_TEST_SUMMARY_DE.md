# Manual Runtime Laptop Failure Test Summary

Read-only Zusammenfassung der validierten Laptop-Failure-Testlaeufe aus `laptop_failure_execution_log_validation.json`. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json` (atomisch `.tmp` -> Replace, max. 256 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-test-summary`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_test_summary.py`
