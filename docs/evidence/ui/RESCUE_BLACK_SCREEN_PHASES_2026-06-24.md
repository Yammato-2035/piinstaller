# Schwarze Boot-Phasen — Analyse (2026-06-24)

## Beobachtung (MSI, Payload 1.9.16.2)

- Systemnachrichten auf TTY1 unterdrückt (Fix RS-P3K)
- Fortschritts-Splash sichtbar wenn React/Chromium läuft
- **Lange schwarze Phasen** vor und zwischen Splash-Updates bleiben

## Zeitliche Einordnung (typisch)

| Phase | Dauer (ca.) | Dienst/State | Anzeige |
|---|---|---|---|
| GRUB → Kernel | kurz | — | Schwarz |
| systemd early | 5–30s | units starten | Schwarz (kein Konsolen-Rauschen mehr) |
| X11 start | variabel | `setuphelfer-rescue-x11` | Schwarz bis X ready |
| Chromium Kiosk | variabel | `gui-watchdog`, rescue UI | Schwarz bis first paint |
| React Splash | sichtbar | `/api/rescue/boot-status` polling | Fortschritt |
| Startmenü | nach `onReady` | React `RescueApp` | UI |

## Ursachen-Hypothesen

1. **X11 noch nicht bereit** — kein früher Framebuffer-Splash auf VT7
2. **Chromium cold start** — SquashFS + kein GPU-Beschleuniger-Cache
3. **Backend noch nicht ready** — Splash wartet auf API, Menü erst nach `bootReady`

## Verbesserungen (1.9.16.3)

- Kein Rückfall zu systemd-Text auf TTY1
- Logmarker in `gui-watchdog.sh` / `x11-hold` (bestehend)
- UI-Fix entkoppelt schwarze Phasen vom Startmenü-Blocker

## Offen

- Früherer statischer Splash auf Kiosk-VT (separates Epic)
- Live-Timing-Messung auf MSI mit `journalctl` + Screenshots

## Status

**GELB** — dokumentiert, nicht vollständig behoben
