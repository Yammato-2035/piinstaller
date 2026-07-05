> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_WRITE_EXECUTE_DRYRUN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Write Execute Dry-Run (EN)

## Goal

Final dry-run contract phase for Déploiement write with session/token/confirmation binding and immediate re-checks before simulated execution.

## Guarantees

- Non disk writes
- Non Partitioning/formatting
- Non mount/loop/chroot
- simulated step output only

## API

- `POST /api/Déploiement/write/session`
- `POST /api/Déploiement/write/execute`

Both endpoints are fail-Fermerd and code-based.
