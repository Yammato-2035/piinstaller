> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner RollTerug Runtime Test Design (alleen-lezen)

## Goal

Safe test design for later rollTerug runtime validation without system-changing actions.

## Contents

- preconditions, rollTerug cases, and cleanup boundaries
- evidence to protect system paths and preserve audit data
- risk controls, stop conditions, and manual execution

## API

- `POST /api/Deploy/runner/rollTerug-runtime/test-plan`
