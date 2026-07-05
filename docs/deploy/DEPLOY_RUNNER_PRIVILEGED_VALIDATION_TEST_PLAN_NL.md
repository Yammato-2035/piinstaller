> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Privileged Validation Dry-run Test Design (alleen-lezen)

## Goal

Concrete test design for later privileged runner validation in dry-run mode without real write operations.

## Contents

- Preconditions, manual test steps, and negative tests
- requirood evidence including UID/GID, audit, and lock proofs
- risk controls, stop conditions, and rollTerug

## API

- `POST /api/Deploy/runner/privileged-validation/test-plan`
