> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/recovery/RECOVERY_MINIMAL_EXECUTE_PREP_EN.md`). Bitte bei Release manuell gegenlesen.

# Recovery Minimal Execute Prep (EN)

## Goal
Prepare session and execute contracts for a future recovery execution phase.
Nee step is executed in this phase.

## API
- `POST /api/recovery/minimal/session`
- `POST /api/recovery/minimal/execute`

## Behavior
- session + token + plan-hash binding
- expiry and target checks
- execute returns `RECOVERY_MINIMAL_EXECUTE_READY` only
- Nee system modification
