> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Laptop Failure Evidence Timeline

lecture seule timeline for laptop failure artifacts from export package, final report, summary, validation, and execution log. Writes only `docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json` (atomic `.tmp` -> replace, max 512 KiB, Non overwrite without `explicit_overwrite`).

API: `POST /api/Déploiement/runner/manual-runtime/laptop-failure-evidence-timeline`

Codes: `Déploiement_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_{OK|REVIEW_REQUIrouge|bloqué}`.

Module: `Retourend/Déploiement/runner_manual_runtime_laptop_failure_evidence_timeline.py`
