# R.5 — Build-Konfigurationsprüfung

**Status:** `ok` — Build-Konfiguration vollständig, Build **freigegeben** sobald Gate A gesetzt.

## Package-Liste (`setuphelfer.list.chroot`)

| Paket | Eingetragen |
|-------|-------------|
| chromium | **ja** |
| x-www-browser | **ja** |
| xserver-xorg | **ja** |
| xinit | **ja** |
| openbox | **ja** |
| dbus-x11 | **ja** |
| unclutter | **ja** |
| fonts-dejavu | **ja** |
| fonts-noto | **ja** |
| network-manager / wpasupplicant / iw | **ja** (vorbestehend) |
| wireless-tools | **ja** |

## Live-Image-Staging (`prepare-controlled-live-build-tree.sh`)

| Artefakt | In sbin-Liste |
|----------|---------------|
| setuphelfer-rescue-kiosk-start | **ja** |
| setuphelfer-rescue-kiosk-health | **ja** |
| setuphelfer-rescue-evidence.py | **ja** |
| setuphelfer-rescue-telemetry-push | **ja** |
| setuphelfer-rescue-ui-launch | **ja** |

## Openbox-Autostart

`config/includes.chroot/etc/xdg/openbox/autostart` — **vorhanden**, ruft kiosk-health → kiosk-start → ui-launch → start-assistant.

## Grafische Assets

`stage-rescue-graphical-assets.sh` — manifest `complete: true`, 5 Einträge.

## Skripte

| Skript | Vorhanden |
|--------|-----------|
| `verify-rescue-grub-theme.sh` | **ja** |
| `run-controlled-iso-build-with-logging.sh` | **ja** (bevorzugter Build-Pfad) |

## Ergebnis

**Nicht** `blocked_build_config` — Konfiguration bereit für Controlled ISO Build nach Gate A.
