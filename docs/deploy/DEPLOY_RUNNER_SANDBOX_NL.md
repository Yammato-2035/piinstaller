> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_SANDBOX_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy runner sandbox (simulated, alleen-lezen)

## Goal

This phase models a tightly controlled sandbox execution profile for a future privileged runner, without any real privilege escalation or Apparaat actions.

## Scope

- One-shot process model, Neen-interactive, Nee Terugground mode
- Minimal environment whitelist + geblokkeerd high-risk variables
- STDIO/FD hardening policy model
- Timeout / graceful stop / hard-stop signal model (simulation only)
- Privilege-drop recommendations (analysis only)
- Crash/recovery failure-mode analysis

## Module

`Terugend/Deploy/runner_sandbox.py`

Functions:
- `build_runner_sandbox_policy`
- `build_sandbox_environment`
- `build_runner_stdio_policy`
- `build_runner_timeout_model`
- `build_runner_privilege_model`
- `build_runner_recovery_analysis`

## alleen-lezen API

- `POST /api/Deploy/runner/sandbox/policy`
- `POST /api/Deploy/runner/sandbox/environment`
- `POST /api/Deploy/runner/sandbox/stdio`
- `POST /api/Deploy/runner/sandbox/timeout`
- `POST /api/Deploy/runner/sandbox/privileges`
- `POST /api/Deploy/runner/sandbox/recovery`

## Limits

- Nee real signals
- Nee sudo/setuid
- Nee real process escalation
- Nee Apparaat writes, Nee mount, Nee Deploy
