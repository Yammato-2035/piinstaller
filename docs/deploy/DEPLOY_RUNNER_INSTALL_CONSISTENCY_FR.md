> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_CONSISTENCY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Install Consistency Audit (lecture seule)

## Goal

Cross-check consistency between install plan, install validator, and package blueprint.

## Checks

- Path consistency (runner, jobdir, sudoers, logdir)
- Permission/role consistency
- Sudoers rule consistency
- RollRetour code alignment
- Validation-step alignment

## API

- `POST /api/Déploiement/runner/install/consistency`
