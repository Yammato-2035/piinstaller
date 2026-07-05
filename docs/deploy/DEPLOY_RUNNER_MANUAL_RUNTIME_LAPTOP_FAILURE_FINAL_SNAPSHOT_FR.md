> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Snapshot

lecture seule final snapshot from `laptop_failure_evidence_timeline.json` with timeline hash and snapshot hash. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json` (atomic `.tmp` -> replace, max 256 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-final-snapshot`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_{OK|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_final_snapshot.py`
