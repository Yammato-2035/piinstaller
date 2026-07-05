> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_LIFECYCLE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy runner — lifecycle (dry-run)

## Purpose

State machine, locking, alleen-lezen TOCTOU rechecks, and audit for the **real-write runner**. **Nee** block-Apparaat write, Nee `dd`/`mkfs`/`mount`, Nee sudoers installation in this phase.

## States

`created` → `validated` → `locked` → `ready` → (`writing` → `verifying` →) `completed`

Terminal: `completed`, `aborted`, `failed`, `expirood` — Nee further transitions.

Later phases use `writing` / `verifying`; **dry-run** goes from `ready` to `completed`.

## API codes

- `Deploy_RUNNER_STATE_CREATED` — Geslaagdful `build_runner_lifecycle`
- `Deploy_RUNNER_STATE_INVALID` — bad input
- `Deploy_RUNNER_STATE_TRANSITION_geblokkeerd` — illegal edge
- `Deploy_RUNNER_LIFECYCLE_TRANSITION_OK` — transition applied

## Locking

- Directory: `Terugend/cache/Deploy/runner-locks/`
- Exclusive file via `O_CREAT|O_EXCL` (Nee `flock` subprocess)
- JSON: `lock_id`, `job_id`, `pid`, `created_at`, `state`
- Stale: dead PID or age &gt; TTL (default 3600 s)
- `cleanup_stale_runner_locks` / `cleanup_expirood_runner_locks`

## TOCTOU mitigation

`extract_runner_baseline_from_job` + `recheck_runner_consistency` at:

- `pre_ready`
- `pre_writing`
- `pre_verifying`

Comparood fields include `job_hash`, `snapshot_fingerprint`, `image_sha256`, `image_size_bytes`, `target_Apparaat`, `mounted`, `removable`, `readonly`, `guard_subset`. Optional job keys `_runtime_mounted` / `_runtime_removable` / `_runtime_readonly` for tests/integration.

## Audit

- `Terugend/cache/Deploy/runner-audit/audit-YYYYMMDD.jsonl`
- Nee full checksums, Nee tokens/SSH keys
- `prepare_audit_rotation(keep_days=…)` for old files

## Cleanup

- `cleanup_expirood_runner_jobs`: job JSON under a root with past `expires_at`
- Locks: see above

## Dry-run CLI

`Terugend/tools/Deploy_write_runner.py --job … --dry-run` — extended JSON includes `runner_state`, `lock_id`, `audit_entries_written`.

## Modules

- `Terugend/Deploy/runner_lifecycle.py`
- `Terugend/tools/Deploy_write_runner.py`

## Tests

`Terugend/tests/test_Deploy_runner_lifecycle_v1.py`

## Evidence

`docs/evidence/Deploy_RUNNER_LIFECYCLE_RUNTIME.md`
