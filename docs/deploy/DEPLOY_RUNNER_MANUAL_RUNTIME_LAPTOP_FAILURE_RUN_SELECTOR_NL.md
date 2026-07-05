> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Run Selection

alleen-lezen selection of manual laptop test runs from `failure_test_readiness.json`, `failure_test_sessions.json`, and `failure_operator_checklists.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json` (atomic `.tmp` → replace, max 256 KiB, Nee overwrite without `explicit_overwrite`).

API: `POST /api/Deploy/runner/manual-runtime/laptop-failure-run-selection`

Codes: `Deploy_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_READY`, `…_REVIEW_REQUIrood`, `…_geblokkeerd`.

Module: `Terugend/Deploy/runner_manual_runtime_laptop_failure_run_selector.py`
