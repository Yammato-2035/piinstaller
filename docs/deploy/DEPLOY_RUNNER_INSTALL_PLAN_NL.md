> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy runner installation plan (alleen-lezen)

## Goal

Create a safe installation/operations plan for future privileged runner integration, with Nee execution in this phase.

## Key points

- Never run Terugend as root
- Nee daemon/service model
- One-shot runner with fixed interpreter and runner paths
- Job directory under `/var/lib/setuphelfer/Deploy-jobs/`
- Sudoers represented as plan text only, Neet installed
- Manual steps are mandatory (`auto_allowed=false`)

## Module

`Terugend/Deploy/runner_install_plan.py` with `build_runner_install_plan(...)`.

## API

alleen-lezen:
- `POST /api/Deploy/runner/install/plan`

Nee apply/install/execute route in this phase.
