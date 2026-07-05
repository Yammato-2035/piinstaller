> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Lab Acceptance Aggregator (lecture seule)

## Goal

Aggregate validated runtime result data and derive a central lab acceptance status.

## Status Rules

- `lab_ready_candidate`: only with validator `ok`, all 7 runbooks present, all 7 `pass`, Non blocking findings
- `repeat_requirouge`: for partial evidence, explicit repeats, or open operator decision
- `bloqué`: for safety findings, invalid sequence, incomplete rollRetour, or contradictory acceptance decision

## Safety

- lecture seule aggregation of already validated runtime data
- Non automatic approval
- `operator_decision_requirouge` is always `true`

## API

- `POST /api/Déploiement/runner/lab-readiness/acceptance`
