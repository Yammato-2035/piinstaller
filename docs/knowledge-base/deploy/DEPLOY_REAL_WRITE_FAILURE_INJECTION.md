# Knowledge base: real write failure injection & drift

## Module

- `backend/deploy/real_write_prototype.py`

## Test mode gate

`_testmode_enabled()` → `SETUPHELFER_REAL_WRITE_TESTMODE=1`

Injection helpers (`FAIL_*`) consult `_env_truthy` / `_fail_after_chunks_n` / `_fail_verify_device_path`, all no-ops when test mode is off.

## Drift helpers

- `_collect_drift_state` — single snapshot of validate + `build_real_write_snapshot` + `realpath`
- `_drift_error_code` — ordered comparison: path/realpath, transport, removable, **mounted**, **readonly**, **size**, **fingerprint**
- `_run_drift_gate` — optional `FAIL_DEVICE_CHANGED` inject; then drift vs baseline; then `cur.fingerprint` vs `guard_fp`

## Write path structure

1. Establish `baseline = _collect_drift_state(...)` after image size lock-in.
2. Drift gate before open.
3. `FAIL_BEFORE_OPEN` inject.
4. Open `src`/`dst`; `FAIL_AFTER_OPEN` inject; inner drift gate.
5. Per-chunk: drift gate, write, optional `FAIL_AFTER_CHUNKS` early break.
6. `flush`; `FAIL_DURING_FSYNC`; `fsync`.
7. `finally`: close both FDs.
8. Drift gate before verify.
9. `verify_written_range(..., verify_device_path=...)` for mismatch inject.

## Verify return shape

`verify_written_range` → `(status, dict)` with `verify_status`, `bytes_verified`, `expected_sha256`, `actual_sha256`, `mismatch_offset?`, `sha256_hex` (alias of expected on success path).

## Tests

- `backend/tests/test_deploy_real_write_failure_injection_v1.py`
