# Deploy write runner — contract (dry-run phase)

## Purpose

Separate **unprivileged backend** from an **optional privileged one-shot runner** that may perform real block-device writes later. **This phase:** **job contract**, **validation**, and **dry-run CLI** only — **no** device open, **no** writes.

## Why not run the whole backend as root?

It widens the attack surface (network, sessions, paths). Only a minimal runner should gain elevated rights — for one bounded job.

## Why a separate runner?

Least privilege: the backend mints and hashes jobs; the runner reads **exactly one** local job file, validates, and later (not in this phase) performs the write.

## Why a job file?

Auditable, reproducible input — no shell RPC, no free-form commands in JSON.

## Why hash binding?

`job_hash` is SHA256 over canonical JSON **excluding** `job_hash`, binding target, image metadata, and guard metadata; tampering is detected.

## Why no real write yet?

Phased delivery: contract + dry-run + tests first; then production path with sudoers/path allowlists.

## Modules / tools

- `backend/deploy/real_write_runner_contract.py` — `build_real_write_job`, `validate_real_write_job`, `compute_job_hash`
- `backend/tools/deploy_write_runner.py` — CLI `--job` and `--dry-run`

### CLI

```bash
python3 backend/tools/deploy_write_runner.py --job /path/job.json --dry-run
```

Output: one JSON line on stdout with `DEPLOY_RUNNER_DRY_RUN_OK` or `DEPLOY_RUNNER_DRY_RUN_BLOCKED` (includes lifecycle fields: `runner_state`, `lock_id`, `audit_entries_written`; see `DEPLOY_RUNNER_LIFECYCLE_EN.md`).

## Job file path (`--job`)

Only allowed under:

- `/var/lib/setuphelfer/deploy-jobs/` (intended production root)
- `backend/cache/deploy` (module-stable path for dev/CI)

The operator-supplied path is normalized with `expanduser` + `resolve` and must fall under one of these roots via `relative_to`. **Symlinks as the job file** (the path passed to `--job`) are **rejected** (fail-closed). Directory traversal (`../`) may resolve outside the allowed prefix and is blocked.

## Image paths

Allowed: same as `inspect_deploy_image` (configured cache prefixes) **plus** the fixed backend deploy cache directory `backend/cache/deploy` (resolved relative to the package) so backend-generated jobs validate whether the runner’s cwd is repo root or backend.

## Validation codes

- `DEPLOY_RUNNER_JOB_VALID`
- `DEPLOY_RUNNER_JOB_INVALID`
- `DEPLOY_RUNNER_JOB_EXPIRED`
- `DEPLOY_RUNNER_JOB_HASH_MISMATCH`
- `DEPLOY_RUNNER_JOB_IMAGE_INVALID`
- `DEPLOY_RUNNER_JOB_TARGET_INVALID`

## Replay (optional, tests / hardened ops)

Environment variable `DEPLOY_RUNNER_REPLAY_GUARD=1`: after **successful** job validation the process records `(job_id, job_hash)`; a second dry-run with the same pair in the **same** process returns `DEPLOY_RUNNER_JOB_REPLAY_DUPLICATE`. This does not span processes without a persistent ledger or one-time token.

## Runtime evidence

See `docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md` (system snapshot, isolation, sudoers risks, test commands).

## Future operations model (documentation only)

- sudoers entry only for this runner script; **no** wildcards in arguments; constrain `env_keep` / `LD_PRELOAD` / `PYTHONPATH` (see evidence doc)
- `--job` paths restricted (e.g. under `/var/lib/setuphelfer/deploy-jobs/`) in addition to the runner’s internal check
- no `shell=True`, no `dd`/partitioning tools in the runner

## Limits (this phase)

- No root check, no device open, no byte writes.
