# Deploy Runner Manual Runtime Result Template (read-only)

## Goal

Create empty runtime result files after successful manual-runtime precheck inside the allowed evidence path.

## Rules

- only with `precheck_status` = `ready_for_manual_runtime|review_required`
- only allowed 7 runbook IDs
- output only under `docs/evidence/runtime-results/`
- no overwrite unless `explicit_overwrite=true`

## API

- `POST /api/deploy/runner/manual-runtime/result-template`
