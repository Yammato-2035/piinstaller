# Deploy Runner Manual Runtime Result Validator Handoff Gate (read-only for result files)

## Purpose

Prepare only a seven-file result bundle that the bundle checker marked ready for the runtime result ingestion validator—without running ingestion or any runtime work.

## Rules

- `validator_bundle_readiness.ready_for_runtime_result_validator` must be true
- `expected_validator_status` must be `ok` (validator-ready)
- exactly seven paths, must match `validator_input_files`
- no `bundle_findings`, every per-file check `ok`, sequence and chain flags intact
- paths re-checked for symlink/traversal/existence; result files must not live under `handoff/`

## Manifest

- only under `docs/evidence/runtime-results/handoff/`
- atomic write (`.tmp` then replace), max 512 KB
- no replace without `explicit_overwrite=true`

## API

- `POST /api/deploy/runner/manual-runtime/result-validator-handoff`
