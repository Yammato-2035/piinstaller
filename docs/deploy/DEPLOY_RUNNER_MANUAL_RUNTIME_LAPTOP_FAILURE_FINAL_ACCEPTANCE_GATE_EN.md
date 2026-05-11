# Manual Runtime Laptop Failure Final Acceptance Gate

Read-only acceptance gate based on `laptop_failure_final_snapshot.json` with hash revalidation. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json` (atomic `.tmp` -> replace, max 128 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-acceptance`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_{ACCEPTED|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_final_acceptance_gate.py`
