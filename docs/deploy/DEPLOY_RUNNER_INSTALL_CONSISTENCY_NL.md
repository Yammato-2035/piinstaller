> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_CONSISTENCY_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Install Consistency Audit (alleen-lezen)

## Goal

Cross-check consistency between install plan, install validator, and package blueprint.

## Checks

- Path consistency (runner, jobdir, sudoers, logdir)
- Permission/role consistency
- Sudoers rule consistency
- RollTerug code alignment
- Validation-step alignment

## API

- `POST /api/Deploy/runner/install/consistency`
