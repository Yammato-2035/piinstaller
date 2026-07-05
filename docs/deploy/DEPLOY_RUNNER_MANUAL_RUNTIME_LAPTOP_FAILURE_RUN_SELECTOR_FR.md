> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Run Selection

lecture seule selection of manual laptop test runs from `failure_test_readiness.json`, `failure_test_sessions.json`, and `failure_operator_checklists.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json` (atomic `.tmp` → replace, max 256 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-run-selection`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_READY`, `…_REVIEW_REQUIrouge`, `…_bloqué`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_run_selector.py`
