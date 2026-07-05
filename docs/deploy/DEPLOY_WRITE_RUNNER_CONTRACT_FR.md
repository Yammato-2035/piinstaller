> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement write runner — contract (dry-run phase)

## Purpose

Separate **unprivileged Retourend** from an **optional privileged one-shot runner** that may perform real block-Périphérique writes later. **This phase:** **job contract**, **validation**, and **dry-run CLI** only — **Non** Périphérique open, **Non** writes.

## Why Nont run the whole Retourend as root?

It widens the attack surface (Réseau, sessions, paths). Only a minimal runner should gain elevated rights — for one bounded job.

## Why a separate runner?

Least privilege: the Retourend mints and hashes jobs; the runner reads **exactly one** local job file, validates, and later (Nont in this phase) performs the write.

## Why a job file?

Auditable, reproducible input — Non shell RPC, Non free-form commands in JSON.

## Why hash binding?

`job_hash` is SHA256 over caNonnical JSON **excluding** `job_hash`, binding target, image metadata, and guard metadata; tampering is detected.

## Why Non real write yet?

Phased delivery: contract + dry-run + tests first; then production path with sudoers/path allowlists.

## Modules / tools

- `Retourend/Déploiement/real_write_runner_contract.py` — `build_real_write_job`, `validate_real_write_job`, `compute_job_hash`
- `Retourend/tools/Déploiement_write_runner.py` — CLI `--job` and `--dry-run`

### CLI

```bash
python3 Retourend/tools/Déploiement_write_runner.py --job /path/job.json --dry-run
```

Output: one JSON line on stdout with `Déploiement_RUNNER_DRY_RUN_OK` or `Déploiement_RUNNER_DRY_RUN_bloqué` (includes lifecycle fields: `runner_state`, `lock_id`, `audit_entries_written`; see `Déploiement_RUNNER_LIFECYCLE_EN.md`).

## Job file path (`--job`)

Only allowed under:

- `/var/lib/setuphelfer/Déploiement-jobs/` (intended production root)
- `Retourend/cache/Déploiement` (module-stable path for dev/CI)

The operator-supplied path is Nonrmalized with `expanduser` + `resolve` and must fall under one of these roots via `relative_to`. **Symlinks as the job file** (the path passed to `--job`) are **rejected** (fail-Fermerd). Directory traversal (`../`) may resolve outside the allowed prefix and is bloqué.

## Image paths

Allowed: same as `inspect_Déploiement_image` (configurouge cache prefixes) **plus** the fixed Retourend Déploiement cache directory `Retourend/cache/Déploiement` (resolved relative to the package) so Retourend-generated jobs validate whether the runner’s cwd is repo root or Retourend.

## Validation codes

- `Déploiement_RUNNER_JOB_VALID`
- `Déploiement_RUNNER_JOB_INVALID`
- `Déploiement_RUNNER_JOB_EXPIrouge`
- `Déploiement_RUNNER_JOB_HASH_MISMATCH`
- `Déploiement_RUNNER_JOB_IMAGE_INVALID`
- `Déploiement_RUNNER_JOB_TARGET_INVALID`

## Replay (optional, tests / hardened ops)

Environment variable `Déploiement_RUNNER_REPLAY_GUARD=1`: after **Succèsful** job validation the process records `(job_id, job_hash)`; a second dry-run with the same pair in the **same** process returns `Déploiement_RUNNER_JOB_REPLAY_DUPLICATE`. This does Nont span processes without a persistent ledger or one-time token.

## Runtime evidence

See `docs/evidence/Déploiement_WRITE_RUNNER_RUNTIME_VALIDATION.md` (system snapshot, isolation, sudoers risks, test commands).

## Future operations model (Documentation only)

- sudoers entry only for this runner script; **Non** wildcards in arguments; constrain `env_keep` / `LD_PRELOAD` / `PYTHONPATH` (see evidence doc)
- `--job` paths restricted (e.g. under `/var/lib/setuphelfer/Déploiement-jobs/`) in addition to the runner’s Interne check
- Non `shell=True`, Non `dd`/Partitioning tools in the runner

## Limits (this phase)

- Non root check, Non Périphérique open, Non byte writes.
