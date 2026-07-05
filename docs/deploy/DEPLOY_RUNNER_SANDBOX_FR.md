> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_SANDBOX_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement runner sandbox (simulated, lecture seule)

## Goal

This phase models a tightly controlled sandbox execution profile for a future privileged runner, without any real privilege escalation or Périphérique actions.

## Scope

- One-shot process model, Nonn-interactive, Non Retourground mode
- Minimal environment whitelist + bloqué high-risk variables
- STDIO/FD hardening policy model
- Timeout / graceful stop / hard-stop signal model (simulation only)
- Privilege-drop recommendations (analysis only)
- Crash/recovery failure-mode analysis

## Module

`Retourend/Déploiement/runner_sandbox.py`

Functions:
- `build_runner_sandbox_policy`
- `build_sandbox_environment`
- `build_runner_stdio_policy`
- `build_runner_timeout_model`
- `build_runner_privilege_model`
- `build_runner_recovery_analysis`

## lecture seule API

- `POST /api/Déploiement/runner/sandbox/policy`
- `POST /api/Déploiement/runner/sandbox/environment`
- `POST /api/Déploiement/runner/sandbox/stdio`
- `POST /api/Déploiement/runner/sandbox/timeout`
- `POST /api/Déploiement/runner/sandbox/privileges`
- `POST /api/Déploiement/runner/sandbox/recovery`

## Limits

- Non real signals
- Non sudo/setuid
- Non real process escalation
- Non Périphérique writes, Non mount, Non Déploiement
