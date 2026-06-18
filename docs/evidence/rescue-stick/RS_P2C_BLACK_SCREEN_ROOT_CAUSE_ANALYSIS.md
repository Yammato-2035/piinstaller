# RS-P2C Black Screen Root Cause Analysis

## Beantwortete Pflichtfragen

| # | Frage | Befund |
|---|-------|--------|
| 1 | Wird setuphelfer_kiosk=1 automatisch gesetzt? | **Ja** — RS-P2A setzte `setuphelfer_kiosk=1` im ersten GRUB-Eintrag (`rescue_fat32_esp_usb_writer.py`) und start-assistant startete GUI zuerst. |
| 2 | Wird dadurch Textmodus übersprungen? | **Ja** — boot-trigger versuchte `setuphelfer-rescue-gui-start` vor TUI; bei `setuphelfer_kiosk=1` zusätzlich direkter Kiosk-exec. |
| 3 | Welcher Service startet die GUI? | `setuphelfer-rescue-start-assistant.service` → GUI-Start-Skript → `setuphelfer-rescue-kiosk-start`. |
| 4 | Startet ein Displayserver? | Kiosk-Launcher versucht X/Chromium; auf MSI/NVIDIA oft ohne funktionierenden Modus. |
| 5 | Browser/Kiosk im Squashfs? | Ja (`rescue.html`, `setuphelfer-rescue-kiosk-start`). |
| 6 | Läuft Backend vor GUI? | Sollte — aber bei GUI-Fehler kein sichtbarer TUI-Fallback auf tty1. |
| 7 | GUI-Start Logs? | Teilweise journal; kein konsistenter `/run/setuphelfer/gui-start.log` + SETUP_LOGS-Spiegel in P2A. |
| 8 | Timeout? | **Nein** — kein GUI-Watchdog in P2A. |
| 9 | Fallback TUI? | Nur whiptail-Hinweis bei GUI-exit ≠ 0; kein exec TUI, oft schwarzer tty1. |
| 10 | Schwarz weil X ohne UI? | **Wahrscheinlich** — `black_screen_root_cause=likely_display_without_ui` |
| 11 | TTY-Ausgabe nach GUI-Fehler? | **Nein** — blinkender Cursor, kein Menü. |
| 12 | Recovery-Taste/Fallback? | **Nein** — kein GRUB-Textmodus-Default, kein Watchdog. |

## GRUB-Bedienbarkeit

- gfxmenu + JPEG-Hintergrund → dünne Schrift am Rand, keine echten Buttons.
- Menüband-Position war an Wallpaper-Layout gekoppelt (52%-Problem aus P2A).

## RS-P2C Maßnahmen

- Plain GRUB, hoher Kontrast, kein Theme-Default.
- Default: `setuphelfer_mode=text setuphelfer_kiosk=0`.
- Entrypoint + TUI + GUI-Watchdog mit Fallback.
- Boot-Evidence nach SETUP_LOGS.

`runtime_validated` bleibt **false** bis RS-P2D MSI-Retest.
