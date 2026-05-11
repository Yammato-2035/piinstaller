# Recovery Activation Execute Prep (EN)

## Goal
Prepare session and execute contracts for a later controlled activation phase.

## In this phase
- no SSH enablement
- no user creation
- no service starts
- no port opening
- no network/firewall changes

## API
- `POST /api/recovery/activation/session`
- `POST /api/recovery/activation/execute` (NO-OP READY)
