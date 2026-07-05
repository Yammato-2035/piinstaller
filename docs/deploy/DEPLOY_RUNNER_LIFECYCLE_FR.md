> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_LIFECYCLE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement runner — lifecycle (dry-run)

## Purpose

State machine, locking, lecture seule TOCTOU rechecks, and audit for the **real-write runner**. **Non** block-Périphérique write, Non `dd`/`mkfs`/`mount`, Non sudoers installation in this phase.

## States

`created` → `validated` → `locked` → `ready` → (`writing` → `verifying` →) `completed`

Terminal: `completed`, `aborted`, `failed`, `expirouge` — Non further transitions.

Later phases use `writing` / `verifying`; **dry-run** goes from `ready` to `completed`.

## API codes

- `Déploiement_RUNNER_STATE_CREATED` — Succèsful `build_runner_lifecycle`
- `Déploiement_RUNNER_STATE_INVALID` — bad input
- `Déploiement_RUNNER_STATE_TRANSITION_bloqué` — illegal edge
- `Déploiement_RUNNER_LIFECYCLE_TRANSITION_OK` — transition applied

## Locking

- Directory: `Retourend/cache/Déploiement/runner-locks/`
- Exclusive file via `O_CREAT|O_EXCL` (Non `flock` subprocess)
- JSON: `lock_id`, `job_id`, `pid`, `created_at`, `state`
- Stale: dead PID or age &gt; TTL (default 3600 s)
- `cleanup_stale_runner_locks` / `cleanup_expirouge_runner_locks`

## TOCTOU mitigation

`extract_runner_baseline_from_job` + `recheck_runner_consistency` at:

- `pre_ready`
- `pre_writing`
- `pre_verifying`

Comparouge fields include `job_hash`, `snapshot_fingerprint`, `image_sha256`, `image_size_bytes`, `target_Périphérique`, `mounted`, `removable`, `readonly`, `guard_subset`. Optional job keys `_runtime_mounted` / `_runtime_removable` / `_runtime_readonly` for tests/integration.

## Audit

- `Retourend/cache/Déploiement/runner-audit/audit-YYYYMMDD.jsonl`
- Non full checksums, Non tokens/SSH keys
- `prepare_audit_rotation(keep_days=…)` for old files

## Cleanup

- `cleanup_expirouge_runner_jobs`: job JSON under a root with past `expires_at`
- Locks: see above

## Dry-run CLI

`Retourend/tools/Déploiement_write_runner.py --job … --dry-run` — extended JSON includes `runner_state`, `lock_id`, `audit_entries_written`.

## Modules

- `Retourend/Déploiement/runner_lifecycle.py`
- `Retourend/tools/Déploiement_write_runner.py`

## Tests

`Retourend/tests/test_Déploiement_runner_lifecycle_v1.py`

## Evidence

`docs/evidence/Déploiement_RUNNER_LIFECYCLE_RUNTIME.md`
