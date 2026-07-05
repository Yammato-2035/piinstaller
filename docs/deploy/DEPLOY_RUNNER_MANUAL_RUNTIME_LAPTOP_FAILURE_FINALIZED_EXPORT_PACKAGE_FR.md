> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Finalized Export Package

lecture seule finalized export package from acceptance, snapshot, timeline, export, report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_finalized_export_package.json` (atomic `.tmp` -> replace, max 512 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-finalized-export-package`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_{OK|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_finalized_export_package.py`
