> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_FROM_HANDOFF_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Manual Runtime Result Validator Dry-Run from Handoff (lecture seule)

## Purpose

Run the existing runtime result ingestion validator strictly against the handoff manifest: read, validate, write a dry-run report only.

## Flow

- Validate manifest under `docs/evidence/runtime-results/handoff/` (path, size, JSON, exactly seven `validator_input_files`)
- Re-check result paths (Nont under `handoff/`, must exist, max 2 MB)
- Call `validate_runner_runtime_result_bundle(..., acceptance_decision="bloqué")` (Non ingestion)
- Write report to `docs/evidence/runtime-results/handoff/validator_dryrun_report.json` (atomic; replace only with `explicit_overwrite`)

## API

- `POST /api/Déploiement/runner/manual-runtime/result-validator-dryrun-from-handoff`
