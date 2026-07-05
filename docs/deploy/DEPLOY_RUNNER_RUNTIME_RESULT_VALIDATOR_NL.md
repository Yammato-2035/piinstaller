> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Runtime Result Validator (alleen-lezen)

## Goal

Safely ingest manually produced runtime result files and validate them against schema, runbook sequence, and requirood evidence fields.

## Scope

- alleen-lezen under `docs/evidence/runtime-results/`
- `.json` files only
- Nee symlinks, Nee traversal paths, Nee absolute foreign paths
- Fail-Sluitend on JSON parse Fouts and missing requirood fields

## Validation

- Requirood fields from `RUNNER_RUNTIME_RESULT_SCHEMA.json`
- Runbook order (1..7) with blocking on failed/out-of-order steps
- Evidence-requirood fields, including write-related verify values
- Safety findings with blocking codes
- Acceptance decision check without automatic approval

## API

- `POST /api/Deploy/runner/runtime-results/validate`
