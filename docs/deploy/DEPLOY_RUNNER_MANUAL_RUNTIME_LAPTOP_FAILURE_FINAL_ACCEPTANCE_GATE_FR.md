> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Acceptance Gate

lecture seule acceptance gate based on `laptop_failure_final_snapshot.json` with hash revalidation. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json` (atomic `.tmp` -> replace, max 128 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-final-acceptance`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_{ACCEPTED|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_final_acceptance_gate.py`
