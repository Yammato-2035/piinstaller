> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Acceptance Gate

alleen-lezen acceptance gate based on `laptop_failure_final_snapshot.json` with hash revalidation. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json` (atomic `.tmp` -> replace, max 128 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-final-acceptance`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_{ACCEPTED|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_final_acceptance_gate.py`
