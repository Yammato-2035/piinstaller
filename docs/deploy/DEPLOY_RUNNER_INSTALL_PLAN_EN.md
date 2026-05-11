# Deploy runner installation plan (read-only)

## Goal

Create a safe installation/operations plan for future privileged runner integration, with no execution in this phase.

## Key points

- Never run backend as root
- No daemon/service model
- One-shot runner with fixed interpreter and runner paths
- Job directory under `/var/lib/setuphelfer/deploy-jobs/`
- Sudoers represented as plan text only, not installed
- Manual steps are mandatory (`auto_allowed=false`)

## Module

`backend/deploy/runner_install_plan.py` with `build_runner_install_plan(...)`.

## API

Read-only:
- `POST /api/deploy/runner/install/plan`

No apply/install/execute route in this phase.
