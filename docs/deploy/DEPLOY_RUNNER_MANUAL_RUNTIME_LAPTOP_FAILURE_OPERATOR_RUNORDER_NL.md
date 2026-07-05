> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Operator RuNeerder

alleen-lezen operator run order from `laptop_failure_run_selection.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_operator_ruNeerder.json` (atomic `.tmp` → replace, max 256 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-operator-ruNeerder`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNeeRDER_{READY|REVIEW_REQUIrood|geblokkeerd}`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_operator_ruNeerder.py`
