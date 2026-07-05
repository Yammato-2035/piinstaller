> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement runner installation plan (lecture seule)

## Goal

Create a safe installation/operations plan for future privileged runner integration, with Non execution in this phase.

## Key points

- Never run Retourend as root
- Non daemon/service model
- One-shot runner with fixed interpreter and runner paths
- Job directory under `/var/lib/setuphelfer/Déploiement-jobs/`
- Sudoers represented as plan text only, Nont installed
- Manual steps are mandatory (`auto_allowed=false`)

## Module

`Retourend/Déploiement/runner_install_plan.py` with `build_runner_install_plan(...)`.

## API

lecture seule:
- `POST /api/Déploiement/runner/install/plan`

Non apply/install/execute route in this phase.
