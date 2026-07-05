> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Manual Runtime Precheck (alleen-lezen)

## Goal

Evaluate readiness before a manual runtime runbook step starts, without triggering execution.

## Scope

- selected runbook validation (only 7 allowed IDs)
- environment/operator/test-media checks
- evidence plan under `docs/evidence/runtime-results/`
- fail-Sluitend stop conditions

## API

- `POST /api/Deploy/runner/manual-runtime/precheck`
