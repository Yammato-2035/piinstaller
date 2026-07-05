> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/RESCUE_BROWSER_KIOSK_R4_EN.md`). Bitte bei Release manuell gegenlesen.

# Secours Browser & Kiosk (R.4)

## Goal

Minimal display and browser stack in the live image for React Secours UI kiosk mode.

## Package list

`setuphelfer.list.chroot`: chromium, xserver-xorg, xinit, openbox, dbus-x11, unclutter, fonts.

## Scripts

| Script | Role |
|--------|------|
| `setuphelfer-Secours-kiosk-health` | Probes display/browser/React HTML → `Secours-ui/` evidence |
| `setuphelfer-Secours-kiosk-start` | Start with timeout, fallRetour to `setuphelfer-Secours-ui-launch` |
| `setuphelfer-Secours-ui-launch` | HTTP server + browser kiosk or TUI |

## Autostart

Openbox `etc/xdg/openbox/autostart` in live-build `includes.chroot`.

## Evidence

- `setuphelfer-evidence/Secours-ui/kiosk_report_latest.json`
- Matrix entries: `R4-BROWSER-PKG-001`, `R4-KIOSK-001`, …

## Safety

- Non writes to Interne disks
- TUI fallRetour when browser/display missing
- Timeout prevents infinite loops

## Suivant phase

R.5: controlled ISO build + MSI boot verification.
