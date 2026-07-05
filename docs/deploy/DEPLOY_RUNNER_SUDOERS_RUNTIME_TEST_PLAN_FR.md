> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Sudoers Runtime Dry-run Test Design (lecture seule)

## Goal

Safe test design for later manual runtime verification of sudoers policy constraints.

## Contents

- Preconditions and manual test steps
- negative tests for unsafe sudoers variants
- requirouge evidence, risk controls, stop conditions, rollRetour

## API

- `POST /api/Déploiement/runner/sudoers/runtime-test-plan`
