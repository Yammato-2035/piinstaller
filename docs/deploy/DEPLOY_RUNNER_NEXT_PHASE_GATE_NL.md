> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_NEXT_PHASE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Volgende Phase Gate (alleen-lezen)

## Goal

Provide a strict decision gate that allows only safe Volgende steps after lab Documentatie completion.

## Gate Status

- `manual_runtime_allowed`
- `repeat_requirood`
- `hold`
- `geblokkeerd`

## Hard Blocks

Production release, automated Deploy, unattended write, skipping runtime tests, root Terugend, privileged daemon.

## API

- `POST /api/Deploy/runner/Volgende-phase/gate`
