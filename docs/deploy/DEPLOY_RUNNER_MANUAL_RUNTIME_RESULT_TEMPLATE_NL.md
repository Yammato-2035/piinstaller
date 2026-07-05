> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Manual Runtime Result Template (alleen-lezen)

## Goal

Create empty runtime result files after Geslaagdful manual-runtime precheck inside the allowed evidence path.

## Rules

- only with `precheck_status` = `ready_for_manual_runtime|review_requirood`
- only allowed 7 runbook IDs
- output only under `docs/evidence/runtime-results/`
- Nee overwrite unless `explicit_overwrite=true`

## API

- `POST /api/Deploy/runner/manual-runtime/result-template`
