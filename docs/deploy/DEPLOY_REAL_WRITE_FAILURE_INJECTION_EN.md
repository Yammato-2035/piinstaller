# Real-write prototype: failure injection (test mode only)

## Prerequisite

Hooks below apply **only** when **both** are set:

- `SETUPHELFER_ENABLE_REAL_WRITE=1`
- `SETUPHELFER_REAL_WRITE_TESTMODE=1`

Without test mode, `FAIL_*` variables are ignored (production behavior unchanged).

## Environment hooks

| Variable | Effect |
|----------|--------|
| `FAIL_BEFORE_OPEN=1` | Abort immediately before opening the target device (`DEPLOY_REAL_WRITE_ABORTED`, error hint `FAIL_BEFORE_OPEN`). |
| `FAIL_AFTER_OPEN=1` | Abort right after a successful target open; handles are closed in `finally`. |
| `FAIL_AFTER_CHUNKS=N` | Stop after **N** written chunks (partial write); verify then fails (`DEPLOY_REAL_WRITE_VERIFY_FAILED`). |
| `FAIL_VERIFY_MISMATCH=1` | Verify reads the device from `SETUPHELFER_FAIL_VERIFY_DEVICE_PATH` instead of the target path (forced mismatch). |
| `FAIL_DURING_FSYNC=1` | Injected `OSError` from `os.fsync` (abort). |
| `FAIL_DEVICE_CHANGED=1` | Forces `DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED` at the drift gate (simulated drift). |

## Device drift

Before critical steps, a **baseline snapshot** is compared to fresh state:

- Target path, `realpath`, transport, removable, mounted, readonly (from snapshot), size, fingerprint

Divergences map to:

- `DEPLOY_REAL_WRITE_DEVICE_CHANGED`
- `DEPLOY_REAL_WRITE_TARGET_REMOUNTED`
- `DEPLOY_REAL_WRITE_READONLY_CHANGED`
- `DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED`
- `DEPLOY_REAL_WRITE_SIZE_CHANGED`

## Verify

- Compares exactly **nbytes** (image size), chunked, no retries.
- `verify` / `verify_result`: includes `bytes_verified`, `expected_sha256`, `actual_sha256`, optional `mismatch_offset`.
- Short device reads and partial writes surface as **failed** or **mismatch**.

## Abort & resources

- `src`/`dst` are closed in `finally`.
- The global mutex is always released in the outer `finally`.
- No automatic retries or repair.

## Limits

- No E2E guarantee without disposable USB/SD; see evidence doc.
- Injection is for controlled testing only, not production.
