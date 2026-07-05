> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Privileged Validation Dry-run Test Design (lecture seule)

## Goal

Concrete test design for later privileged runner validation in dry-run mode without real write operations.

## Contents

- Preconditions, manual test steps, and negative tests
- requirouge evidence including UID/GID, audit, and lock proofs
- risk controls, stop conditions, and rollRetour

## API

- `POST /api/Déploiement/runner/privileged-validation/test-plan`
