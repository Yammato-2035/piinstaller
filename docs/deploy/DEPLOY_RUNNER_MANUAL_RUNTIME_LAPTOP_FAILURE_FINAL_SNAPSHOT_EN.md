# Manual Runtime Laptop Failure Final Snapshot

Read-only final snapshot from `laptop_failure_evidence_timeline.json` with timeline hash and snapshot hash. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json` (atomic `.tmp` -> replace, max 256 KiB, no overwrite without `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-snapshot`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_{OK|REVIEW_REQUIRED|BLOCKED}`.

Module: `backend/deploy/runner_manual_runtime_laptop_failure_final_snapshot.py`
