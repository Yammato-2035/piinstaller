# Deploy Runner Install Consistency Audit (read-only)

## Goal

Cross-check consistency between install plan, install validator, and package blueprint.

## Checks

- Path consistency (runner, jobdir, sudoers, logdir)
- Permission/role consistency
- Sudoers rule consistency
- Rollback code alignment
- Validation-step alignment

## API

- `POST /api/deploy/runner/install/consistency`
