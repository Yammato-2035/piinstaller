# RS-P2C GUI Watchdog Fix

## Implementiert

- `setuphelfer-rescue-gui-watchdog` — Backend-Start, Kiosk-Hintergrund, Prozess/Timeout-Prüfung.
- `setuphelfer-rescue-gui-start.sh` — `gui_enabled_by_default=false`, delegiert an Watchdog.
- `rescue_gui_watchdog_contract.py` + Tests.

## Fallback

Bei jedem Fehler: `fallback_to_tui=true`, Evidence in `gui-watchdog.json`.

Kein blinkender Cursor ohne Text — Entrypoint führt danach `setuphelfer-rescue-tui` aus.
