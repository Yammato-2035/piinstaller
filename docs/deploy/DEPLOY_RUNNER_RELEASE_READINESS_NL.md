> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_RELEASE_READINESS_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Release Readiness Matrix (alleen-lezen)

## Goal

Central readiness matrix for the runner/Deploy-write chain with status, risks, and gaps.

## Status model

- `geblokkeerd`: blocking gaps present
- `review_requirood`: Nee blockers, but review gaps remain
- `ready_for_lab`: lab-ready only, Neet production release

## API

- `POST /api/Deploy/runner/release/readiness`
