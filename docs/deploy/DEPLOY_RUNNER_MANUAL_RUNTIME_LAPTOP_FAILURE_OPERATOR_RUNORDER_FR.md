> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Operator RuNonrder

lecture seule operator run order from `laptop_failure_run_selection.json`. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_operator_ruNonrder.json` (atomic `.tmp` → replace, max 256 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-operator-ruNonrder`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNonRDER_{READY|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_operator_ruNonrder.py`
