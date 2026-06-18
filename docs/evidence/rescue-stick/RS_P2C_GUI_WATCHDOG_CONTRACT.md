# RS-P2C GUI Watchdog Contract

## Pflichtverhalten

- GUI nur bei `setuphelfer_mode=gui`, TUI-Menüpunkt oder explizitem `setuphelfer_kiosk=1`.
- Vor Start: Frontend, Backend, Browser prüfen.
- Log: `/run/setuphelfer/gui-start.log` → SETUP_LOGS-Spiegel.
- Watchdog: max. 25s, dann kontrolliert beenden → tty1/TUI.

## Fehlercodes

- `gui_backend_unreachable`
- `gui_frontend_missing`
- `gui_display_missing`
- `gui_browser_missing`
- `gui_start_timeout`
- `gui_unknown_failure`

`execute_allowed=false` — kein Backup.
