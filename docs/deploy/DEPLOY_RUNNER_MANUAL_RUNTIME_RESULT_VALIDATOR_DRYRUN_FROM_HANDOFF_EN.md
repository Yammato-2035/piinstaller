# Deploy Runner Manual Runtime Result Validator Dry-Run from Handoff (read-only)

## Purpose

Run the existing runtime result ingestion validator strictly against the handoff manifest: read, validate, write a dry-run report only.

## Flow

- Validate manifest under `docs/evidence/runtime-results/handoff/` (path, size, JSON, exactly seven `validator_input_files`)
- Re-check result paths (not under `handoff/`, must exist, max 2 MB)
- Call `validate_runner_runtime_result_bundle(..., acceptance_decision="blocked")` (no ingestion)
- Write report to `docs/evidence/runtime-results/handoff/validator_dryrun_report.json` (atomic; replace only with `explicit_overwrite`)

## API

- `POST /api/deploy/runner/manual-runtime/result-validator-dryrun-from-handoff`
