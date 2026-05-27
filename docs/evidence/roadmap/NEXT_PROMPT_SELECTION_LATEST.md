# Next Prompt Selection (Latest)

**selected_prompt_id:** `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`  
**selected_at:** 2026-05-27T22:25:00Z  
**HEAD:** `5786eb3` (Roadmap-Update folgt)

## Begründung

- `TERMINAL_A_READONLY` ist **completed** (read-only Command Logging, 5786eb3).
- Roadmap-Registry und Diagnostics-Teilfortschritt bleiben sichtbar, aber nicht full-green.
- Recovery-Core blockiert weiterhin über Rescue/BR-001/Restore/Verify.
- Nächster technischer Hauptblocker: **echter kontrollierter Rescue-ISO-Operator-Build** im Terminal.
- USB-Write, Restore, Hardwaretests ausgeschlossen.

## Vor Rescue-Build prüfen

Cockpit-/Roadmap-/Command-Logging-UI unter `/opt` per Deploy-Helper und Hard-Reload (siehe Roadmap-Notiz `dev-dashboard-live-deploy-before-rescue`).

## Alternativen

- `RESCUE_ISO_SUDOERS_ALLOWLIST_POLICY_DESIGN` — organisatorisch
- `BR001_EXTERNAL_EVIDENCE` — parallel wichtig, nicht primärer Build-Blocker
