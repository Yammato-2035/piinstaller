> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_WRITE_EXECUTE_DRYRUN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Write Execute Dry-Run (EN)

## Goal

Final dry-run contract phase for Deploy write with session/token/confirmation binding and immediate re-checks before simulated execution.

## Guarantees

- Nee disk writes
- Nee Partitieing/formatting
- Nee mount/loop/chroot
- simulated step output only

## API

- `POST /api/Deploy/write/session`
- `POST /api/Deploy/write/execute`

Both endpoints are fail-Sluitend and code-based.
