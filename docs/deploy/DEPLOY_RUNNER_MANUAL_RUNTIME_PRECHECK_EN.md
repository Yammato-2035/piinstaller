# Deploy Runner Manual Runtime Precheck (read-only)

## Goal

Evaluate readiness before a manual runtime runbook step starts, without triggering execution.

## Scope

- selected runbook validation (only 7 allowed IDs)
- environment/operator/test-media checks
- evidence plan under `docs/evidence/runtime-results/`
- fail-closed stop conditions

## API

- `POST /api/deploy/runner/manual-runtime/precheck`
