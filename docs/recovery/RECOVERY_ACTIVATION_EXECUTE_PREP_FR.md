> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/recovery/RECOVERY_ACTIVATION_EXECUTE_PREP_EN.md`). Bitte bei Release manuell gegenlesen.

# Recovery Activation Execute Prep (EN)

## Goal
Prepare session and execute contracts for a later controlled activation phase.

## In this phase
- Non SSH enablement
- Non user creation
- Non service starts
- Non port opening
- Non Réseau/firewall changes

## API
- `POST /api/recovery/activation/session`
- `POST /api/recovery/activation/execute` (Non-OP READY)
