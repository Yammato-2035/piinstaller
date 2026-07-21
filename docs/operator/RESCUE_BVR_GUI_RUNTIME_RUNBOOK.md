# Operator-Runbook: Rescue BVR + GUI Runtime (PI-RS-BVR-GUI-DCC-001)

**Status:** `implemented_pending_physical_retest`  
**Payload-Ziel:** `1.10.1.1`  
**Baseline:** `e2e-rescue-msi-20260721-232222-ba58c7a7` — BVR **passed**, GUI **http_server_failed** → `passed_with_gui_fallback`

## Voraussetzungen

- Phase-0-Gate grün, wenn gegen `/opt` getestet wird (`./scripts/check-runtime-deploy-gate.sh`).
- Stick mit Payload **≥ 1.10.1.1** (ASCII-safe HTTP-Server + Readiness + 4 Locales).
- MSI GE63 oder vergleichbares Lab-Gerät für physischen Nachtest.
- BVR-Kern ist **eingefroren** — keine Änderungen an Backup/Verify/Restore ohne Regressionstests.

## Erwartetes Verhalten (nach Fix, noch nicht physisch bestätigt)

1. GRUB/Cmdline: `setuphelfer_mode=gui` + `setuphelfer_msi_e2e_auto=1`.
2. HTTP-Server startet (`setuphelfer-rescue-ui-http-server`).
3. `/health.json` → HTTP 200, `status=ready`, `payload_version` sichtbar.
4. Chromium startet **erst danach** im Kiosk.
5. BVR (Backup/Verify/Restore) läuft parallel/unabhängig.
6. Bei GUI-Fehler: Watchdog → TUI-Fallback; BVR setzt fort.

## Ablauf — physischer MSI-Nachtest

1. Payload `1.10.1.1` bauen und auf Stick schreiben (nur mit expliziter Freigabe).
2. GE63 booten; Auto-E2E-Lauf abwarten (~vollständiger BVR-Zyklus).
3. Evidence auf SETUP_LOGS prüfen:

```text
SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log
SETUP_LOGS/setuphelfer/evidence/boot/rescue-ui-status.json
SETUP_LOGS/setuphelfer/evidence/boot/gui-http-runtime.json
SETUP_LOGS/setuphelfer/evidence/boot/gui-http-health.json
SETUP_LOGS/setuphelfer/evidence/boot/gui-watchdog.json
```

4. Erfolgskriterien GUI (Ziel, noch nicht bestätigt):
   - `gui-http-health.json`: `status=ready`
   - `rescue-ui-status.json`: `server_started=true`, Browser gestartet oder dokumentierter Fallback
   - Kein `SyntaxError` / `http_server_failed` in `rescue-ui-launch.log`

5. Erfolgskriterien BVR (weiterhin Pflicht):
   - Backup/Verify/Restore **passed**
   - `overall_status`: `passed` (mit GUI) oder `passed_with_gui_fallback` (ohne GUI)

6. Ergebnis nach Workspace importieren → `docs/evidence/rescue/bvr-gui-dcc-001/physical_msi_result.json`

## Diagnose bei GUI-Ausfall

| Symptom | Log/Datei | Typischer Code |
|---------|-----------|----------------|
| Server startet nicht | `rescue-ui-launch.log` | `rescue.gui.process_exited`, `rescue.gui.index_missing` |
| Port belegt | Launcher-Log | `rescue.gui.port_in_use` |
| Health timeout | Launcher-Log | `rescue.gui.readiness_timeout` |
| Locales fehlen | Launcher-Log | `rescue.gui.locale_assets_missing` |
| Watchdog-Fallback | `gui-watchdog.json` | diverse Legacy-Codes |

**Wichtig:** BVR-Erfolg und GUI-Sichtbarkeit getrennt bewerten.

## Abbruch / Sicherheit

- Kein manuelles Backup/Restore außerhalb des Auto-E2E-Pfads.
- Bei `failed` BVR-Kern: Evidence sichern, Stick nicht überschreiben.
- Graceful Shutdown respektieren — HTTP-Server nicht hart killen vor Auto-Shutdown.

## DCC-Status prüfen

Development Control Center → Rescue Stick / PI-RS-BVR-GUI-DCC-001:  
`bvr_core_status`, `gui_status`, `gui_failure_code`, `traffic_lights`, `next_action`.

## Siehe auch

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [GUI_WATCHDOG_FALLBACK.md](../rescue-stick/GUI_WATCHDOG_FALLBACK.md)
- [docs/evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md](../evidence/rescue/bvr-gui-dcc-001/BASELINE_BVR_RESULT.md)
