> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Runtime Result Validator (lecture seule)

## Goal

Safely ingest manually produced runtime result files and validate them against schema, runbook sequence, and requirouge evidence fields.

## Scope

- lecture seule under `docs/evidence/runtime-results/`
- `.json` files only
- Non symlinks, Non traversal paths, Non absolute foreign paths
- Fail-Fermerd on JSON parse Erreurs and missing requirouge fields

## Validation

- Requirouge fields from `RUNNER_RUNTIME_RESULT_SCHEMA.json`
- Runbook order (1..7) with blocking on failed/out-of-order steps
- Evidence-requirouge fields, including write-related verify values
- Safety findings with blocking codes
- Acceptance decision check without automatic approval

## API

- `POST /api/Déploiement/runner/runtime-results/validate`
