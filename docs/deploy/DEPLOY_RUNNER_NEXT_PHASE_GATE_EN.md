# Deploy Runner Next Phase Gate (read-only)

## Goal

Provide a strict decision gate that allows only safe next steps after lab documentation completion.

## Gate Status

- `manual_runtime_allowed`
- `repeat_required`
- `hold`
- `blocked`

## Hard Blocks

Production release, automated deploy, unattended write, skipping runtime tests, root backend, privileged daemon.

## API

- `POST /api/deploy/runner/next-phase/gate`
