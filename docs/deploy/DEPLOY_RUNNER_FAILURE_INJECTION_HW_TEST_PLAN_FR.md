> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Failure Injection Hardware Test Design (lecture seule)

## Goal

Safe test design for later failure-injection runs on real hardware in a controlled lab setup.

## Contents

- preconditions and manual steps
- defined failure cases with expected outcomes
- evidence, risk, stop-condition, and rollRetour planning

## API

- `POST /api/Déploiement/runner/failure-injection-hardware/test-plan`
