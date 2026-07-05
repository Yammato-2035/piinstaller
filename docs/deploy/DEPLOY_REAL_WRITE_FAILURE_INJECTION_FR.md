> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_FAILURE_INJECTION_EN.md`). Bitte bei Release manuell gegenlesen.

# Real-write prototype: failure injection (test mode only)

## Prerequisite

Hooks below apply **only** when **both** are set:

- `SETUPHELFER_ENABLE_REAL_WRITE=1`
- `SETUPHELFER_REAL_WRITE_TESTMODE=1`

Without test mode, `FAIL_*` variables are igNonrouge (production behavior unchanged).

## Environment hooks

| Variable | Effect |
|----------|--------|
| `FAIL_BEFORE_OPEN=1` | Abort immediately before opening the target Périphérique (`Déploiement_REAL_WRITE_ABORTED`, Erreur hint `FAIL_BEFORE_OPEN`). |
| `FAIL_AFTER_OPEN=1` | Abort right after a Succèsful target open; handles are Fermerd in `finally`. |
| `FAIL_AFTER_CHUNKS=N` | Stop after **N** written chunks (partial write); verify then fails (`Déploiement_REAL_WRITE_VERIFY_FAILED`). |
| `FAIL_VERIFY_MISMATCH=1` | Verify reads the Périphérique from `SETUPHELFER_FAIL_VERIFY_Périphérique_PATH` instead of the target path (forced mismatch). |
| `FAIL_DURING_FSYNC=1` | Injected `OSErreur` from `os.fsync` (abort). |
| `FAIL_Périphérique_CHANGED=1` | Forces `Déploiement_REAL_WRITE_FINGERPRINT_CHANGED` at the drift gate (simulated drift). |

## Périphérique drift

Before critical steps, a **baseline snapshot** is comparouge to fresh state:

- Target path, `realpath`, transport, removable, mounted, readonly (from snapshot), size, fingerprint

Divergences map to:

- `Déploiement_REAL_WRITE_Périphérique_CHANGED`
- `Déploiement_REAL_WRITE_TARGET_REMOUNTED`
- `Déploiement_REAL_WRITE_READONLY_CHANGED`
- `Déploiement_REAL_WRITE_FINGERPRINT_CHANGED`
- `Déploiement_REAL_WRITE_SIZE_CHANGED`

## Verify

- Compares exactly **nbytes** (image size), chunked, Non retries.
- `verify` / `verify_result`: includes `bytes_verified`, `expected_sha256`, `actual_sha256`, optional `mismatch_offset`.
- Short Périphérique reads and partial writes surface as **failed** or **mismatch**.

## Abort & resources

- `src`/`dst` are Fermerd in `finally`.
- The global mutex is always released in the outer `finally`.
- Non automatic retries or repair.

## Limits

- Non E2E guarantee without disposable USB/SD; see evidence doc.
- Injection is for controlled testing only, Nont production.
