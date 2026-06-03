# Rescue Boot Menu Branding Precheck

**Datum:** 2026-06-03  
**HEAD:** `2ca3a70`  
**Laufart:** statisch — **kein ISO-Build**

## Assets gefunden

| Asset | Pfad / Hinweis |
|-------|----------------|
| SVG Logos | `setuphelfer-logo-main.svg`, `setuphelfer-logo-mascot.svg` (Repo-Suche) |
| PNG / Public | `frontend/public`, Flyer-PNGs |
| Bootloader config | `build/rescue/live-build/.../config/bootloaders/isolinux/isolinux.cfg` (developer-qemu serial auto-boot) |

## Checks

| # | Prüfung | Ergebnis |
|---|---------|----------|
| 1 | Logo-Datei vorhanden | **yes** (SVG + PNG-Kandidaten) |
| 2 | Format / Conversion | **review_required** — ISOLINUX/GRUB brauchen oft PNG; `librsvg2-bin` / `rsvg-convert` dokumentieren |
| 3 | Legacy-Identifier | **keine neuen** im Precheck |
| 4 | rsvg-Abhängigkeit | **explizit dokumentiert** in `docs/rescue-stick/RESCUE_BOOT_MENU_BRANDING.md` |
| 5 | ISO-Build | **nein** |

## Status

**review_required** — Branding-Contract und Asset-Inventar ok; vorgerenderte Bootloader-PNGs und Build-Lauf ausstehend.

## Siehe auch

- `docs/rescue-stick/RESCUE_BOOT_MENU_BRANDING.md`
