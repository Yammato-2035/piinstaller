# R.8 — SquashFS R.4 Regression Check

**Datum:** 2026-06-13  
**ISO SHA256:** `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390`

## Browser / Display Stack

| Komponente | Status | Hinweis |
|------------|--------|---------|
| chromium | **FOUND** | 78 Treffer |
| xserver-xorg | **FOUND** | 151 Treffer |
| xinit | **FOUND** | 15 Treffer |
| openbox | **FOUND** | 211 Treffer |
| dbus-x11 | **FOUND** | 10 Treffer |
| unclutter | **FOUND** | 28 Treffer |

## Rescue UI / Kiosk

| Komponente | Status |
|------------|--------|
| `rescue.html` | **FOUND** |
| Rescue JS (`rescue-BE5PiphK.js`) | **FOUND** (150 KB) |
| `setuphelfer-rescue-kiosk-start` | **FOUND** |
| `setuphelfer-rescue-kiosk-health` | **FOUND** |
| `setuphelfer-rescue-telemetry-push` | **FOUND** |
| `setuphelfer-rescue-ui-launch` | **FOUND** |

## Package Policy

| Check | Ergebnis |
|-------|----------|
| `x-www-browser` in dpkg status | **ABSENT** (0) |

## Boot-Menu Assets (Squashfs)

| Asset | Status |
|-------|--------|
| `setuphelfer-boot-menu-de.png` | **FOUND** |
| `setuphelfer-boot-menu-en.png` | **FOUND** |

## Entscheidung

**PASS** — Keine R.4-Regression. Browser/Kiosk-Stack vollständig.
