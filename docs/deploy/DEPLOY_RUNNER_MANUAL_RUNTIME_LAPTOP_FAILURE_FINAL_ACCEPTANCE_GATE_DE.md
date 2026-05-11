# Manual Runtime Laptop Failure Final Acceptance Gate

Read-only Acceptance-Gate auf Basis von `laptop_failure_final_snapshot.json` mit Hash-Revalidierung. Schreibt nur `docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json` (atomisch `.tmp` -> Replace, max. 128 KiB, kein Overwrite ohne `explicit_overwrite`).

API: `POST /api/deploy/runner/manual-runtime/laptop-failure-final-acceptance`

Codes: `DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_{ACCEPTED|REVIEW_REQUIRED|BLOCKED}`.

Modul: `backend/deploy/runner_manual_runtime_laptop_failure_final_acceptance_gate.py`
