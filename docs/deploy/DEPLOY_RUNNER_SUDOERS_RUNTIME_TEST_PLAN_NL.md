> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Sudoers Runtime Dry-run Test Design (alleen-lezen)

## Goal

Safe test design for later manual runtime verification of sudoers policy constraints.

## Contents

- Preconditions and manual test steps
- negative tests for unsafe sudoers variants
- requirood evidence, risk controls, stop conditions, rollTerug

## API

- `POST /api/Deploy/runner/sudoers/runtime-test-plan`
