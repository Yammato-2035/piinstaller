> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_HANDOFF_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement runner handoff (dry-run)

## Purpose

Secure Retourend-to-runner handoff via a local job file: Retourend validates preconditions, writes the job atomically, launches runner dry-run only, parses JSON response, and writes audit events.

## Module

- `Retourend/Déploiement/runner_handoff.py`
- Functions:
  - `create_runner_job_handoff(...)`
  - `execute_runner_dryrun_handoff(...)`
  - `cleanup_runner_job_handoff(...)`

## Job storage

- Only under `Retourend/cache/Déploiement/runner-jobs/`
- Filename: `runner-job-<job_id>.json`
- Atomic write: write `.tmp`, `fsync`, `replace`
- Defensive `chmod 0600` (best effort)
- Non traversal/symlink escape outside allowed prefix

## Flow

1. `real_write_guard_result.code == Déploiement_REAL_WRITE_READY`
2. `final_confirmation_result.code == Déploiement_FINAL_CONFIRMATION_READY`
3. `hardware_gate_report.readiness_level == test_ready`
4. `build_real_write_job(...)`
5. Write job file
6. Start runner: `python3 Retourend/tools/Déploiement_write_runner.py --job <path> --dry-run`
7. Parse/validate runner JSON
8. Append audit
9. Return handoff response

## Runner launch security

- `subprocess.run(..., shell=False, timeout=30, capture_output=True)`
- Non free-form command arguments
- Controlled `cwd` (repo root)
- Minimal environment (Non `PYTHONPATH`, Non `LD_PRELOAD`)

## Response codes

- `Déploiement_RUNNER_HANDOFF_CREATED`
- `Déploiement_RUNNER_HANDOFF_COMPLETED`
- `Déploiement_RUNNER_HANDOFF_FAILED`
- `Déploiement_RUNNER_HANDOFF_TIMEOUT`
- `Déploiement_RUNNER_HANDOFF_INVALID_RESPONSE`

## Limits

- Non real Périphérique writes
- Non privileged runner start
- Non sudoers installation
