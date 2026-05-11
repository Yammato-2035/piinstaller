# Deploy runner handoff (dry-run)

## Purpose

Secure backend-to-runner handoff via a local job file: backend validates preconditions, writes the job atomically, launches runner dry-run only, parses JSON response, and writes audit events.

## Module

- `backend/deploy/runner_handoff.py`
- Functions:
  - `create_runner_job_handoff(...)`
  - `execute_runner_dryrun_handoff(...)`
  - `cleanup_runner_job_handoff(...)`

## Job storage

- Only under `backend/cache/deploy/runner-jobs/`
- Filename: `runner-job-<job_id>.json`
- Atomic write: write `.tmp`, `fsync`, `replace`
- Defensive `chmod 0600` (best effort)
- No traversal/symlink escape outside allowed prefix

## Flow

1. `real_write_guard_result.code == DEPLOY_REAL_WRITE_READY`
2. `final_confirmation_result.code == DEPLOY_FINAL_CONFIRMATION_READY`
3. `hardware_gate_report.readiness_level == test_ready`
4. `build_real_write_job(...)`
5. Write job file
6. Start runner: `python3 backend/tools/deploy_write_runner.py --job <path> --dry-run`
7. Parse/validate runner JSON
8. Append audit
9. Return handoff response

## Runner launch security

- `subprocess.run(..., shell=False, timeout=30, capture_output=True)`
- No free-form command arguments
- Controlled `cwd` (repo root)
- Minimal environment (no `PYTHONPATH`, no `LD_PRELOAD`)

## Response codes

- `DEPLOY_RUNNER_HANDOFF_CREATED`
- `DEPLOY_RUNNER_HANDOFF_COMPLETED`
- `DEPLOY_RUNNER_HANDOFF_FAILED`
- `DEPLOY_RUNNER_HANDOFF_TIMEOUT`
- `DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE`

## Limits

- No real device writes
- No privileged runner start
- No sudoers installation
