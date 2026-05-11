# Deploy runner sandbox (simulated, read-only)

## Goal

This phase models a tightly controlled sandbox execution profile for a future privileged runner, without any real privilege escalation or device actions.

## Scope

- One-shot process model, non-interactive, no background mode
- Minimal environment whitelist + blocked high-risk variables
- STDIO/FD hardening policy model
- Timeout / graceful stop / hard-stop signal model (simulation only)
- Privilege-drop recommendations (analysis only)
- Crash/recovery failure-mode analysis

## Module

`backend/deploy/runner_sandbox.py`

Functions:
- `build_runner_sandbox_policy`
- `build_sandbox_environment`
- `build_runner_stdio_policy`
- `build_runner_timeout_model`
- `build_runner_privilege_model`
- `build_runner_recovery_analysis`

## Read-only API

- `POST /api/deploy/runner/sandbox/policy`
- `POST /api/deploy/runner/sandbox/environment`
- `POST /api/deploy/runner/sandbox/stdio`
- `POST /api/deploy/runner/sandbox/timeout`
- `POST /api/deploy/runner/sandbox/privileges`
- `POST /api/deploy/runner/sandbox/recovery`

## Limits

- No real signals
- No sudo/setuid
- No real process escalation
- No device writes, no mount, no deploy
