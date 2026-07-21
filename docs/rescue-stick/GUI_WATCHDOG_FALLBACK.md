# GUI Watchdog & Fallback

**Task:** PI-RS-BVR-GUI-DCC-001 (Watchdog unverändert im Verhalten; HTTP-Readiness neu)

## Prinzip

`setuphelfer-rescue-gui-watchdog.sh` startet die GUI-Kette mit Timeout. Scheitert X11/Chromium/Backend-Health → **TUI-Fallback** auf tty1. BVR Auto-E2E läuft weiter.

## Ablauf

1. MSI-Compat-Check — bei `nomodeset`/Compat: GUI blockiert, TUI sofort.
2. Backend async starten.
3. Kiosk auf dediziertem VT starten.
4. Health-Loop (Standard: 20 s Timeout, 3 s stabil).
5. Erfolg → GUI sichtbar; Timeout/Fehler → `_fail()` → TUI.

## Fallback-Status

Geschrieben nach `/run/setuphelfer-rescue/gui-watchdog.json` (Alias: `/run/setuphelfer/gui-watchdog.json`):

```json
{
  "schema_version": 1,
  "gui_started": false,
  "gui_failed": true,
  "gui_error_code": "http_server_failed",
  "fallback_to_tui": true,
  "execute_allowed": false,
  "secrets_exposed": false
}
```

## DCC-001-Bezug

- **Vor Fix:** HTTP-Server starb sofort (`SyntaxError`) → Watchdog sah keinen stabilen GUI-Start → Fallback.
- **Nach Fix:** Launcher prüft Readiness **vor** Chromium; Watchdog greift bei Browser/X11-Problemen weiterhin.
- Baseline: `watchdog_fallback=true`, `overall_status=passed_with_gui_fallback`.

## Launcher-Fallback (ohne grafischen Browser)

`setuphelfer-rescue-ui-launch` bietet Whiptail-TUI mit Status, Logs, Netzwerk, Reboot/Shutdown — `display_mode=fallback_tui`, `status=review_required`.

## Konfiguration

| Variable | Standard | Bedeutung |
|----------|----------|-----------|
| `SETUPHELFER_GUI_WATCHDOG_SEC` | 20 | Watchdog-Gesamt-Timeout |
| `SETUPHELFER_GUI_STABLE_SEC` | 3 | Stabile Health-Dauer |
| `SETUPHELFER_RESCUE_UI_READY_RETRIES` | 20 | HTTP-Readiness-Versuche |
| `SETUPHELFER_RESCUE_UI_READY_SLEEP_MS` | 250 | Pause zwischen Versuchen |

## Siehe auch

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [RESCUE_GUI_AUTOSTART_CONTRACT.md](./RESCUE_GUI_AUTOSTART_CONTRACT.md)
