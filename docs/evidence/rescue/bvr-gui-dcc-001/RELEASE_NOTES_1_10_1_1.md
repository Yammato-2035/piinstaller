# Rescue Payload 1.10.1.1 – Release Notes

**Task:** PI-RS-BVR-GUI-DCC-001  
**Status:** `implemented_pending_physical_retest`  
**Previous:** 1.10.1.0 (`passed_with_gui_fallback`, `http_server_failed`)

## Changes

- Dedicated ASCII-safe GUI HTTP server (`setuphelfer-rescue-ui-http-server`)
- Health/readiness (`/health.json`) before Chromium starts
- Progress UI locales: de-DE, en-US, fr-FR, nl-NL
- Structured GUI error codes (`rescue.gui.*`)
- Watchdog/TUI fallback retained
- DCC status endpoint for BVR/GUI/i18n/drift

## Not claimed

GUI visibility on MSI hardware is **not** verified until the physical retest with this payload completes.
