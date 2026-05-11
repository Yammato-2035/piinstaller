# Deploy Write Execute Dry-Run (EN)

## Goal

Final dry-run contract phase for deploy write with session/token/confirmation binding and immediate re-checks before simulated execution.

## Guarantees

- no disk writes
- no partitioning/formatting
- no mount/loop/chroot
- simulated step output only

## API

- `POST /api/deploy/write/session`
- `POST /api/deploy/write/execute`

Both endpoints are fail-closed and code-based.
