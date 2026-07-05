> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Manual Runtime Result Validator Handoff Gate (lecture seule for result files)

## Purpose

Prepare only a seven-file result bundle that the bundle checker marked ready for the runtime result ingestion validator—without running ingestion or any runtime work.

## Rules

- `validator_bundle_readiness.ready_for_runtime_result_validator` must be true
- `expected_validator_status` must be `ok` (validator-ready)
- exactly seven paths, must match `validator_input_files`
- Non `bundle_findings`, every per-file check `ok`, sequence and chain flags intact
- paths re-checked for symlink/traversal/existence; result files must Nont live under `handoff/`

## Manifest

- only under `docs/evidence/runtime-results/handoff/`
- atomic write (`.tmp` then replace), max 512 KB
- Non replace without `explicit_overwrite=true`

## API

- `POST /api/Déploiement/runner/manual-runtime/result-validator-handoff`
