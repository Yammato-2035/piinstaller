# Rescue Browser & Kiosk (R.4)

## Goal

Minimal display and browser stack in the live image for React Rescue UI kiosk mode.

## Package list

`setuphelfer.list.chroot`: chromium, xserver-xorg, xinit, openbox, dbus-x11, unclutter, fonts.

## Scripts

| Script | Role |
|--------|------|
| `setuphelfer-rescue-kiosk-health` | Probes display/browser/React HTML → `rescue-ui/` evidence |
| `setuphelfer-rescue-kiosk-start` | Start with timeout, fallback to `setuphelfer-rescue-ui-launch` |
| `setuphelfer-rescue-ui-launch` | HTTP server + browser kiosk or TUI |

## Autostart

Openbox `etc/xdg/openbox/autostart` in live-build `includes.chroot`.

## Evidence

- `setuphelfer-evidence/rescue-ui/kiosk_report_latest.json`
- Matrix entries: `R4-BROWSER-PKG-001`, `R4-KIOSK-001`, …

## Safety

- No writes to internal disks
- TUI fallback when browser/display missing
- Timeout prevents infinite loops

## Next phase

R.5: controlled ISO build + MSI boot verification.
