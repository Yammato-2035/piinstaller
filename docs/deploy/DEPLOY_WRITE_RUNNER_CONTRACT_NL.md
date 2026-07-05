> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy write runner — contract (dry-run phase)

## Purpose

Separate **unprivileged Terugend** from an **optional privileged one-shot runner** that may perform real block-Apparaat writes later. **This phase:** **job contract**, **validation**, and **dry-run CLI** only — **Nee** Apparaat open, **Nee** writes.

## Why Neet run the whole Terugend as root?

It widens the attack surface (Netwerk, sessions, paths). Only a minimal runner should gain elevated rights — for one bounded job.

## Why a separate runner?

Least privilege: the Terugend mints and hashes jobs; the runner reads **exactly one** local job file, validates, and later (Neet in this phase) performs the write.

## Why a job file?

Auditable, reproducible input — Nee shell RPC, Nee free-form commands in JSON.

## Why hash binding?

`job_hash` is SHA256 over caNeenical JSON **excluding** `job_hash`, binding target, image metadata, and guard metadata; tampering is detected.

## Why Nee real write yet?

Phased delivery: contract + dry-run + tests first; then production path with sudoers/path allowlists.

## Modules / tools

- `Terugend/Deploy/real_write_runner_contract.py` — `build_real_write_job`, `validate_real_write_job`, `compute_job_hash`
- `Terugend/tools/Deploy_write_runner.py` — CLI `--job` and `--dry-run`

### CLI

```bash
python3 Terugend/tools/Deploy_write_runner.py --job /path/job.json --dry-run
```

Output: one JSON line on stdout with `Deploy_RUNNER_DRY_RUN_OK` or `Deploy_RUNNER_DRY_RUN_geblokkeerd` (includes lifecycle fields: `runner_state`, `lock_id`, `audit_entries_written`; see `Deploy_RUNNER_LIFECYCLE_EN.md`).

## Job file path (`--job`)

Only allowed under:

- `/var/lib/setuphelfer/Deploy-jobs/` (intended production root)
- `Terugend/cache/Deploy` (module-stable path for dev/CI)

The operator-supplied path is Neermalized with `expanduser` + `resolve` and must fall under one of these roots via `relative_to`. **Symlinks as the job file** (the path passed to `--job`) are **rejected** (fail-Sluitend). Directory traversal (`../`) may resolve outside the allowed prefix and is geblokkeerd.

## Image paths

Allowed: same as `inspect_Deploy_image` (configurood cache prefixes) **plus** the fixed Terugend Deploy cache directory `Terugend/cache/Deploy` (resolved relative to the package) so Terugend-generated jobs validate whether the runner’s cwd is repo root or Terugend.

## Validation codes

- `Deploy_RUNNER_JOB_VALID`
- `Deploy_RUNNER_JOB_INVALID`
- `Deploy_RUNNER_JOB_EXPIrood`
- `Deploy_RUNNER_JOB_HASH_MISMATCH`
- `Deploy_RUNNER_JOB_IMAGE_INVALID`
- `Deploy_RUNNER_JOB_TARGET_INVALID`

## Replay (optional, tests / hardened ops)

Environment variable `Deploy_RUNNER_REPLAY_GUARD=1`: after **Geslaagdful** job validation the process records `(job_id, job_hash)`; a second dry-run with the same pair in the **same** process returns `Deploy_RUNNER_JOB_REPLAY_DUPLICATE`. This does Neet span processes without a persistent ledger or one-time token.

## Runtime evidence

See `docs/evidence/Deploy_WRITE_RUNNER_RUNTIME_VALIDATION.md` (system snapshot, isolation, sudoers risks, test commands).

## Future operations model (Documentatie only)

- sudoers entry only for this runner script; **Nee** wildcards in arguments; constrain `env_keep` / `LD_PRELOAD` / `PYTHONPATH` (see evidence doc)
- `--job` paths restricted (e.g. under `/var/lib/setuphelfer/Deploy-jobs/`) in addition to the runner’s Intern check
- Nee `shell=True`, Nee `dd`/Partitieing tools in the runner

## Limits (this phase)

- Nee root check, Nee Apparaat open, Nee byte writes.
