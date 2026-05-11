# Recovery Minimal Execute Prep (EN)

## Goal
Prepare session and execute contracts for a future recovery execution phase.
No step is executed in this phase.

## API
- `POST /api/recovery/minimal/session`
- `POST /api/recovery/minimal/execute`

## Behavior
- session + token + plan-hash binding
- expiry and target checks
- execute returns `RECOVERY_MINIMAL_EXECUTE_READY` only
- no system modification
