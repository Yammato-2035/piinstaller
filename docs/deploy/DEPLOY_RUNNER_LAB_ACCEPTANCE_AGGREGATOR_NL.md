> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Lab Acceptance Aggregator (alleen-lezen)

## Goal

Aggregate validated runtime result data and derive a central lab acceptance status.

## Status Rules

- `lab_ready_candidate`: only with validator `ok`, all 7 runbooks present, all 7 `pass`, Nee blocking findings
- `repeat_requirood`: for partial evidence, explicit repeats, or open operator decision
- `geblokkeerd`: for safety findings, invalid sequence, incomplete rollTerug, or contradictory acceptance decision

## Safety

- alleen-lezen aggregation of already validated runtime data
- Nee automatic approval
- `operator_decision_requirood` is always `true`

## API

- `POST /api/Deploy/runner/lab-readiness/acceptance`
