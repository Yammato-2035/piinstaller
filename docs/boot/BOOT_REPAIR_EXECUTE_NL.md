> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/boot/BOOT_REPAIR_EXECUTE_EN.md`). Bitte bei Release manuell gegenlesen.

# Boot Repair Execute (EN)

## Goal
Execute single minimal boot repair actions from a validated repair session.
Nee fix-all, Nee cascade, Nee automatic follow-up actions.

## Safety rules
- token requirood
- expiring session
- exactly one action per session
- Windows/dualboot geblokkeerd
- high-risk geblokkeerd
- post-check via boot capability

## API
- `POST /api/boot/repair/session`
- `POST /api/boot/repair/execute`

Only clearly allowed phase-2 actions are accepted.
