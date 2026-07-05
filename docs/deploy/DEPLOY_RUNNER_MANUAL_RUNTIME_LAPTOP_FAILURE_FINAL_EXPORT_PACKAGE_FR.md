> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Final Export Package

lecture seule export package for final laptop failure test state from final report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json` (atomic `.tmp` -> replace, max 512 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-final-export-package`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_{OK|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_final_export_package.py`
