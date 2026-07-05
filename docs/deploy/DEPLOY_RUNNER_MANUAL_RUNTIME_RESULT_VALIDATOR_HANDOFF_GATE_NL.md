> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Manual Runtime Result Validator Handoff Gate (alleen-lezen for result files)

## Purpose

Prepare only a seven-file result bundle that the bundle checker marked ready for the runtime result ingestion validator—without running ingestion or any runtime work.

## Rules

- `validator_bundle_readiness.ready_for_runtime_result_validator` must be true
- `expected_validator_status` must be `ok` (validator-ready)
- exactly seven paths, must match `validator_input_files`
- Nee `bundle_findings`, every per-file check `ok`, sequence and chain flags intact
- paths re-checked for symlink/traversal/existence; result files must Neet live under `handoff/`

## Manifest

- only under `docs/evidence/runtime-results/handoff/`
- atomic write (`.tmp` then replace), max 512 KB
- Nee replace without `explicit_overwrite=true`

## API

- `POST /api/Deploy/runner/manual-runtime/result-validator-handoff`
