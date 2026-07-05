> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner RollRetour Runtime Test Design (lecture seule)

## Goal

Safe test design for later rollRetour runtime validation without system-changing actions.

## Contents

- preconditions, rollRetour cases, and cleanup boundaries
- evidence to protect system paths and preserve audit data
- risk controls, stop conditions, and manual execution

## API

- `POST /api/Déploiement/runner/rollRetour-runtime/test-plan`
