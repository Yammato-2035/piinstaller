# Knowledge base: deploy real write prototype v1

## Module

- `backend/deploy/real_write_prototype.py` — `execute_deploy_real_write_prototype(request: dict)`
- Route: `backend/deploy/routes.py` → `POST /api/deploy/write/prototype` (`DeployRealWritePrototypeRequest`)

## Request shape (Pydantic / JSON)

- `target_device`, `image_path`, `expected_checksum` (required; checksum mandatory for prototype)
- `inspect_result`, `safety_summary`
- `write_harness_result`, `real_write_guard_result` (`code` must be `DEPLOY_REAL_WRITE_READY`)
- `guard_snapshot` — snapshot from `build_real_write_snapshot` at gate time; `fingerprint` must still match live inspect
- `final_confirmation_id`, `confirmation_token`, `target_snapshot` — passed to `check_final_confirmation_dryrun`

## Dependencies

- `deploy.hardware_gate.build_hardware_gate_report`, `validate_test_device`
- `deploy.real_write_guard`: `_validate_harness_proof`, `build_real_write_snapshot`
- `deploy.final_confirmation`: `check_final_confirmation_dryrun`, `get_final_confirmation_bindings`
- `deploy.image_inspect.inspect_deploy_image` + `deploy.write_execute._image_valid`

## Concurrency

- `threading.Lock` non-reentrant acquisition at start of write phase; second caller gets `DEPLOY_REAL_WRITE_ABORTED` if lock busy (non-blocking try).

## Security posture

- Fail-closed: any gate failure returns without opening the device (except after successful recheck inside the lock).
- Block device enforcement prevents accidental “write” to a normal file path that looks like a path string.
- No external tooling: easier to audit; avoids shell injection and implicit behaviour of `dd`/coreutils.

## Test module

- `backend/tests/test_deploy_real_write_prototype_v1.py`
- `backend/tests/test_deploy_real_write_failure_injection_v1.py` (nur mit `SETUPHELFER_REAL_WRITE_TESTMODE=1`)

## Verify-Antwort

`verify` und `verify_result` sind identisch; Felder u. a. `bytes_verified`, `expected_sha256`, `actual_sha256`, optional `mismatch_offset`.
