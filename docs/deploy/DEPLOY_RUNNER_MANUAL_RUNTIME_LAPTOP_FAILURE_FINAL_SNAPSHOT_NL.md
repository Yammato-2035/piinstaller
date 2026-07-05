> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Snapshot

alleen-lezen final snapshot from `laptop_failure_evidence_timeline.json` with timeline hash and snapshot hash. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json` (atomic `.tmp` -> replace, max 256 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-final-snapshot`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_{OK|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_final_snapshot.py`
