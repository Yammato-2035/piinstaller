# PI-RS-BVR-GUI-DCC-001 – Implementierungsstatus

**Status:** `implemented_pending_physical_retest`

## Erledigt (Workspace)

- Root Cause: `http_server_failed` durch SyntaxError (Non-ASCII in `b'...'`)
- Dedizierter HTTP-Server `setuphelfer-rescue-ui-http-server`
- Readiness vor Chromium, strukturierte Fehlercodes `rescue.gui.*`
- Progress-HTML + Locales de-DE/en-US/fr-FR/nl-NL
- DCC-Endpoint `/api/dev-dashboard/rescue-bvr-status`
- Baseline bleibt `passed_with_gui_fallback` (nicht Fake-Green)
- Payload-Ziel: **1.10.1.1**
- Watchdog-Fallback erhalten + Negativtest

## Offen

- Commit der Feature-Änderungen
- Kontrolliertes USB-Inject auf SETUPHELFER
- Deploy nach `/opt/setuphelfer`
- Physischer MSI-Retest (GUI sichtbar, kein Fallback)
- Evidence-Import des Retests
