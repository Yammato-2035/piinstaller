# Rescue Summary / Recovery Report (EN)

## Goal
The Recovery Report aggregates existing partial results into one structured report.
No action is executed.

## API
`POST /api/rescue/report`

Response provides:
- `report_status`
- `sections`
- `risks`
- `recommendations`
- `blocked_actions`
- `next_steps`

## Principles
- aggregation only
- no new diagnostic/restore/crypto logic
- no write operations
- unclear states remain `warning`/`unknown`
