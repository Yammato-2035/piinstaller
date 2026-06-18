# RS-P2C Text Mode Contract

## Kernel-Parameter → Verhalten

| setuphelfer_mode | Verhalten |
|------------------|-----------|
| (fehlt) | text |
| text | TUI auf tty1, kein GUI-Autostart |
| gui | GUI-Watchdog, bei Fehler TUI |
| diagnostics | Evidence sammeln, dann TUI |
| hardware | WLAN vorbereiten, dann TUI |

## TUI-Menü (8 Punkte)

1. System erkennen
2. Hardware/WLAN prüfen
3. Backup-Plan erstellen (dry-run)
4. Evidence auf Stick speichern
5. Grafische Oberfläche starten (opt-in)
6. Shell öffnen
7. Neustart
8. Ausschalten

`backup_execute_allowed=false` — durchgängig.

## Skripte

- `setuphelfer-rescue-entrypoint`
- `setuphelfer-rescue-tui`
- `setuphelfer-rescue-start-assistant` → delegiert an Entrypoint
