# Deploy Runner Release Readiness Matrix (read-only)

## Goal

Central readiness matrix for the runner/deploy-write chain with status, risks, and gaps.

## Status model

- `blocked`: blocking gaps present
- `review_required`: no blockers, but review gaps remain
- `ready_for_lab`: lab-ready only, not production release

## API

- `POST /api/deploy/runner/release/readiness`
