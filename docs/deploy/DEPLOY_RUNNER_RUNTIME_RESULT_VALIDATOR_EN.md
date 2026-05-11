# Deploy Runner Runtime Result Validator (read-only)

## Goal

Safely ingest manually produced runtime result files and validate them against schema, runbook sequence, and required evidence fields.

## Scope

- Read-only under `docs/evidence/runtime-results/`
- `.json` files only
- No symlinks, no traversal paths, no absolute foreign paths
- Fail-closed on JSON parse errors and missing required fields

## Validation

- Required fields from `RUNNER_RUNTIME_RESULT_SCHEMA.json`
- Runbook order (1..7) with blocking on failed/out-of-order steps
- Evidence-required fields, including write-related verify values
- Safety findings with blocking codes
- Acceptance decision check without automatic approval

## API

- `POST /api/deploy/runner/runtime-results/validate`
