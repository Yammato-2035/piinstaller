> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Manual Runtime Precheck (lecture seule)

## Goal

Evaluate readiness before a manual runtime runbook step starts, without triggering execution.

## Scope

- selected runbook validation (only 7 allowed IDs)
- environment/operator/test-media checks
- evidence plan under `docs/evidence/runtime-results/`
- fail-Fermerd stop conditions

## API

- `POST /api/Déploiement/runner/manual-runtime/precheck`
