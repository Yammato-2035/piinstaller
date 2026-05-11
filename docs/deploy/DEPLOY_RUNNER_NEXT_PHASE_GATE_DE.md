# Deploy Runner Next Phase Gate (read-only)

## Ziel

Ein Entscheidungs-Gate, das nur sichere naechste Schritte nach der Lab-Dokumentationsphase zulaesst.

## Gate-Status

- `manual_runtime_allowed`
- `repeat_required`
- `hold`
- `blocked`

## Harte Blockierungen

Production Release, Automated Deploy, Unattended Write, Skip Runtime Tests, Root Backend, privilegierter Daemon.

## API

- `POST /api/deploy/runner/next-phase/gate`
