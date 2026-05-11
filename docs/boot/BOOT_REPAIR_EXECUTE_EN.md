# Boot Repair Execute (EN)

## Goal
Execute single minimal boot repair actions from a validated repair session.
No fix-all, no cascade, no automatic follow-up actions.

## Safety rules
- token required
- expiring session
- exactly one action per session
- Windows/dualboot blocked
- high-risk blocked
- post-check via boot capability

## API
- `POST /api/boot/repair/session`
- `POST /api/boot/repair/execute`

Only clearly allowed phase-2 actions are accepted.
