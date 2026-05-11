# Manual Runtime Laptop Failure Final Snapshot

Read-only Final-Snapshot aus `laptop_failure_evidence_timeline.json` mit Timeline-Hash und Snapshot-Hash. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json` (atomisch `.tmp` -> Replace, max. 256 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-snapshot`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_{OK|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_final_snapshot.py`
