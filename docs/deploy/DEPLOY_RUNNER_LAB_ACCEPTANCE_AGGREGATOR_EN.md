# Deploy Runner Lab Acceptance Aggregator (read-only)

## Goal

Aggregate validated runtime result data and derive a central lab acceptance status.

## Status Rules

- `lab_ready_candidate`: only with validator `ok`, all 7 runbooks present, all 7 `pass`, no blocking findings
- `repeat_required`: for partial evidence, explicit repeats, or open operator decision
- `blocked`: for safety findings, invalid sequence, incomplete rollback, or contradictory acceptance decision

## Safety

- read-only aggregation of already validated runtime data
- no automatic approval
- `operator_decision_required` is always `true`

## API

- `POST /api/deploy/runner/lab-readiness/acceptance`
