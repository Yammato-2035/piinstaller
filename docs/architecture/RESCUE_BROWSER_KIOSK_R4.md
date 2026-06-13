# Rescue Browser & Kiosk (R.4)

## Ziel

Minimaler Display- und Browser-Stack im Live-Image für React Rescue UI im Kiosk-Modus.

## Package-Liste

`setuphelfer.list.chroot`: chromium, xserver-xorg, xinit, openbox, dbus-x11, unclutter, fonts.

## Skripte

| Skript | Rolle |
|--------|-------|
| `setuphelfer-rescue-kiosk-health` | Probes Display/Browser/React HTML → Evidence `rescue-ui/` |
| `setuphelfer-rescue-kiosk-start` | Start mit Timeout, Fallback auf `setuphelfer-rescue-ui-launch` |
| `setuphelfer-rescue-ui-launch` | HTTP-Server + Browser-Kiosk oder TUI |

## Autostart

Openbox: `etc/xdg/openbox/autostart` im live-build `includes.chroot`.

## Evidence

- `setuphelfer-evidence/rescue-ui/kiosk_report_latest.json`
- Testmatrix: `R4-BROWSER-PKG-001`, `R4-KIOSK-001`, …

## Sicherheit

- Kein Schreiben auf interne Datenträger
- Fallback TUI wenn Browser/Display fehlt
- Timeout verhindert Endlosschleifen

## Nächste Phase

R.5: Controlled ISO Build + MSI-Boot-Verifikation.
