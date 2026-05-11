# Deploy runner permission boundary (read-only audit)

## Goal

Read-only security analysis for future privileged runner execution, without sudoers installation and without changing system permissions.

## Module

`backend/deploy/runner_permission_boundary.py`

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

Required restrictions:
- `RUNNER_REQUIRE_ABSOLUTE_PATH`
- `RUNNER_REQUIRE_FIXED_JOB_DIRECTORY`
- `RUNNER_REQUIRE_ENV_RESET`
- `RUNNER_BLOCK_PYTHONPATH`
- `RUNNER_BLOCK_LD_PRELOAD`
- `RUNNER_BLOCK_DYNAMIC_PATH`
- `RUNNER_BLOCK_WILDCARDS`
- `RUNNER_REQUIRE_NOINTERACTIVE`
- `RUNNER_REQUIRE_NO_SHELL`

## Read-only API routes

- `POST /api/deploy/runner/audit/sudoers`
- `POST /api/deploy/runner/audit/environment`
- `POST /api/deploy/runner/audit/path`
- `POST /api/deploy/runner/audit/jobdir`

## Limits

- No sudoers write, no visudo, no sudo execution
- No chmod/chown changes on system files
- No device writes, no mount/partition tools
