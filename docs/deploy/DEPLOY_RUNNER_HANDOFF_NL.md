> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_HANDOFF_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy runner handoff (dry-run)

## Purpose

Secure Terugend-to-runner handoff via a local job file: Terugend validates preconditions, writes the job atomically, launches runner dry-run only, parses JSON response, and writes audit events.

## Module

- `Terugend/Deploy/runner_handoff.py`
- Functions:
  - `create_runner_job_handoff(...)`
  - `execute_runner_dryrun_handoff(...)`
  - `cleanup_runner_job_handoff(...)`

## Job storage

- Only under `Terugend/cache/Deploy/runner-jobs/`
- Filename: `runner-job-<job_id>.json`
- Atomic write: write `.tmp`, `fsync`, `replace`
- Defensive `chmod 0600` (best effort)
- Nee traversal/symlink escape outside allowed prefix

## Flow

1. `real_write_guard_result.code == Deploy_REAL_WRITE_READY`
2. `final_confirmation_result.code == Deploy_FINAL_CONFIRMATION_READY`
3. `hardware_gate_report.readiness_level == test_ready`
4. `build_real_write_job(...)`
5. Write job file
6. Start runner: `python3 Terugend/tools/Deploy_write_runner.py --job <path> --dry-run`
7. Parse/validate runner JSON
8. Append audit
9. Return handoff response

## Runner launch security

- `subprocess.run(..., shell=False, timeout=30, capture_output=True)`
- Nee free-form command arguments
- Controlled `cwd` (repo root)
- Minimal environment (Nee `PYTHONPATH`, Nee `LD_PRELOAD`)

## Response codes

- `Deploy_RUNNER_HANDOFF_CREATED`
- `Deploy_RUNNER_HANDOFF_COMPLETED`
- `Deploy_RUNNER_HANDOFF_FAILED`
- `Deploy_RUNNER_HANDOFF_TIMEOUT`
- `Deploy_RUNNER_HANDOFF_INVALID_RESPONSE`

## Limits

- Nee real Apparaat writes
- Nee privileged runner start
- Nee sudoers installation
