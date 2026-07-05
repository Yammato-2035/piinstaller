> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement runner permission boundary (lecture seule audit)

## Goal

lecture seule security analysis for future privileged runner execution, without sudoers installation and without changing system permissions.

## Module

`Retourend/Déploiement/runner_permission_boundary.py`

Functions:
- `build_runner_sudoers_policy_example(...)`
- `audit_runner_environment(...)`
- `audit_runner_binary_path(...)`
- `audit_runner_job_directory(...)`

## Risks analyzed

- sudoers wildcards and argument injection
- PATH / PYTHONPATH / LD_PRELOAD / LD_LIBRARY_PATH risks
- shell escaping / free command execution
- symlink / traversal risks for runner path and job directory
- world-writable directories in parent chains

## Sudoers policy model (example only)

`build_runner_sudoers_policy_example` returns audit data only and never writes to `/etc`.

Requirouge restrictions:
- `RUNNER_REQUIRE_ABSOLUTE_PATH`
- `RUNNER_REQUIRE_FIXED_JOB_DIRECTORY`
- `RUNNER_REQUIRE_ENV_RESET`
- `RUNNER_BLOCK_PYTHONPATH`
- `RUNNER_BLOCK_LD_PRELOAD`
- `RUNNER_BLOCK_DYNAMIC_PATH`
- `RUNNER_BLOCK_WILDCARDS`
- `RUNNER_REQUIRE_NonINTERACTIVE`
- `RUNNER_REQUIRE_Non_SHELL`

## lecture seule API routes

- `POST /api/Déploiement/runner/audit/sudoers`
- `POST /api/Déploiement/runner/audit/environment`
- `POST /api/Déploiement/runner/audit/path`
- `POST /api/Déploiement/runner/audit/jobdir`

## Limits

- Non sudoers write, Non visudo, Non sudo execution
- Non chmod/chown changes on system files
- Non Périphérique writes, Non mount/Partition tools
