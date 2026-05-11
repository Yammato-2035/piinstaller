# Deploy runner — lifecycle (dry-run)

## Purpose

State machine, locking, read-only TOCTOU rechecks, and audit for the **real-write runner**. **No** block-device write, no `dd`/`mkfs`/`mount`, no sudoers installation in this phase.

## States

`created` → `validated` → `locked` → `ready` → (`writing` → `verifying` →) `completed`

Terminal: `completed`, `aborted`, `failed`, `expired` — no further transitions.

Later phases use `writing` / `verifying`; **dry-run** goes from `ready` to `completed`.

## API codes

- `DEPLOY_RUNNER_STATE_CREATED` — successful `build_runner_lifecycle`
- `DEPLOY_RUNNER_STATE_INVALID` — bad input
- `DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED` — illegal edge
- `DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK` — transition applied

## Locking

- Directory: `backend/cache/deploy/runner-locks/`
- Exclusive file via `O_CREAT|O_EXCL` (no `flock` subprocess)
- JSON: `lock_id`, `job_id`, `pid`, `created_at`, `state`
- Stale: dead PID or age &gt; TTL (default 3600 s)
- `cleanup_stale_runner_locks` / `cleanup_expired_runner_locks`

## TOCTOU mitigation

`extract_runner_baseline_from_job` + `recheck_runner_consistency` at:

- `pre_ready`
- `pre_writing`
- `pre_verifying`

Compared fields include `job_hash`, `snapshot_fingerprint`, `image_sha256`, `image_size_bytes`, `target_device`, `mounted`, `removable`, `readonly`, `guard_subset`. Optional job keys `_runtime_mounted` / `_runtime_removable` / `_runtime_readonly` for tests/integration.

## Audit

- `backend/cache/deploy/runner-audit/audit-YYYYMMDD.jsonl`
- No full checksums, no tokens/SSH keys
- `prepare_audit_rotation(keep_days=…)` for old files

## Cleanup

- `cleanup_expired_runner_jobs`: job JSON under a root with past `expires_at`
- Locks: see above

## Dry-run CLI

`backend/tools/deploy_write_runner.py --job … --dry-run` — extended JSON includes `runner_state`, `lock_id`, `audit_entries_written`.

## Modules

- `backend/deploy/runner_lifecycle.py`
- `backend/tools/deploy_write_runner.py`

## Tests

`backend/tests/test_deploy_runner_lifecycle_v1.py`

## Evidence

`docs/evidence/DEPLOY_RUNNER_LIFECYCLE_RUNTIME.md`
