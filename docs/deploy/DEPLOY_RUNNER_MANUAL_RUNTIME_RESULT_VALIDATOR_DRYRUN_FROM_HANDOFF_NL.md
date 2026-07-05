> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_FROM_HANDOFF_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Manual Runtime Result Validator Dry-Run from Handoff (alleen-lezen)

## Purpose

Run the existing runtime result ingestion validator strictly against the handoff manifest: read, validate, write a dry-run report only.

## Flow

- Validate manifest under `docs/evidence/runtime-results/handoff/` (path, size, JSON, exactly seven `validator_input_files`)
- Re-check result paths (Neet under `handoff/`, must exist, max 2 MB)
- Call `validate_runner_runtime_result_bundle(..., acceptance_decision="geblokkeerd")` (Nee ingestion)
- Write report to `docs/evidence/runtime-results/handoff/validator_dryrun_report.json` (atomic; replace only with `explicit_overwrite`)

## API

- `POST /api/Deploy/runner/manual-runtime/result-validator-dryrun-from-handoff`
