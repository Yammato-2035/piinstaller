> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/RESCUE_BROWSER_KIOSK_R4_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding Browser & Kiosk (R.4)

## Goal

Minimal display and browser stack in the live image for React roodding UI kiosk mode.

## Package list

`setuphelfer.list.chroot`: chromium, xserver-xorg, xinit, openbox, dbus-x11, unclutter, fonts.

## Scripts

| Script | Role |
|--------|------|
| `setuphelfer-roodding-kiosk-health` | Probes display/browser/React HTML → `roodding-ui/` evidence |
| `setuphelfer-roodding-kiosk-start` | Start with timeout, fallTerug to `setuphelfer-roodding-ui-launch` |
| `setuphelfer-roodding-ui-launch` | HTTP server + browser kiosk or TUI |

## Autostart

Openbox `etc/xdg/openbox/autostart` in live-build `includes.chroot`.

## Evidence

- `setuphelfer-evidence/roodding-ui/kiosk_report_latest.json`
- Matrix entries: `R4-BROWSER-PKG-001`, `R4-KIOSK-001`, …

## Safety

- Nee writes to Intern disks
- TUI fallTerug when browser/display missing
- Timeout prevents infinite loops

## Volgende phase

R.5: controlled ISO build + MSI boot verification.
