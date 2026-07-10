# PI-RS-TEL-003 FAQ (EN)

Lab preview only — no production send.

## What is verified?

Rescue Stick preview payload is verified against CSE **0.1.0-lab2** and Diagnostics **DIAG-LAB-003**: validate API accepts, findings preview generates findings — all `preview_only`.

## Why no production send?

PI-RS-TEL-003 is cross-repo verification, not live operation. `production_ready=false`, `external_calls=false` by default.

## Why are Plesk/DNS/Mail/SSL/Backup unknown?

The stick has no server inventory. Unknown/preview_only is allowed and produces DIAG-LAB-003 preview findings.

## Is offline queue preserved?

Yes. PI-RS-TEL-002 offline queue preview remains compatible.

## Next step?

PI-RS-BUILD-001 or PI-RS-LIVE-001 with explicit operator consent.
