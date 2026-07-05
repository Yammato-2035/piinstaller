> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_FAILURE_INJECTION_EN.md`). Bitte bei Release manuell gegenlesen.

# Real-write prototype: failure injection (test mode only)

## Prerequisite

Hooks below apply **only** when **both** are set:

- `SETUPHELFER_ENABLE_REAL_WRITE=1`
- `SETUPHELFER_REAL_WRITE_TESTMODE=1`

Without test mode, `FAIL_*` variables are igNeerood (production behavior unchanged).

## Environment hooks

| Variable | Effect |
|----------|--------|
| `FAIL_BEFORE_OPEN=1` | Abort immediately before opening the target Apparaat (`Deploy_REAL_WRITE_ABORTED`, Fout hint `FAIL_BEFORE_OPEN`). |
| `FAIL_AFTER_OPEN=1` | Abort right after a Geslaagdful target open; handles are Sluitend in `finally`. |
| `FAIL_AFTER_CHUNKS=N` | Stop after **N** written chunks (partial write); verify then fails (`Deploy_REAL_WRITE_VERIFY_FAILED`). |
| `FAIL_VERIFY_MISMATCH=1` | Verify reads the Apparaat from `SETUPHELFER_FAIL_VERIFY_Apparaat_PATH` instead of the target path (forced mismatch). |
| `FAIL_DURING_FSYNC=1` | Injected `OSFout` from `os.fsync` (abort). |
| `FAIL_Apparaat_CHANGED=1` | Forces `Deploy_REAL_WRITE_FINGERPRINT_CHANGED` at the drift gate (simulated drift). |

## Apparaat drift

Before critical steps, a **baseline snapshot** is comparood to fresh state:

- Target path, `realpath`, transport, removable, mounted, readonly (from snapshot), size, fingerprint

Divergences map to:

- `Deploy_REAL_WRITE_Apparaat_CHANGED`
- `Deploy_REAL_WRITE_TARGET_REMOUNTED`
- `Deploy_REAL_WRITE_READONLY_CHANGED`
- `Deploy_REAL_WRITE_FINGERPRINT_CHANGED`
- `Deploy_REAL_WRITE_SIZE_CHANGED`

## Verify

- Compares exactly **nbytes** (image size), chunked, Nee retries.
- `verify` / `verify_result`: includes `bytes_verified`, `expected_sha256`, `actual_sha256`, optional `mismatch_offset`.
- Short Apparaat reads and partial writes surface as **failed** or **mismatch**.

## Abort & resources

- `src`/`dst` are Sluitend in `finally`.
- The global mutex is always released in the outer `finally`.
- Nee automatic retries or repair.

## Limits

- Nee E2E guarantee without disposable USB/SD; see evidence doc.
- Injection is for controlled testing only, Neet production.
