# Controlled ISO Build — Branding Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Assets

| Pfad | Anmerkung |
|------|-----------|
| `config/bootloaders/isolinux/splash.svg.in` | SVG-Quelle |
| `config/bootloaders/isolinux/bootlogo` | Bootlogo |
| `binary/isolinux/splash.png` | PNG aus Prior-Build (Stale, kein Neubau) |

## rsvg-Abhängigkeit

- `rsvg-convert` systemweit vorhanden
- Compat-Wrapper `build/rescue/tool-compat/bin/rsvg` + Chroot-Seed via `prepare-controlled-live-build-tree.sh`
- Legacy `/usr/bin/rsvg` fehlt — **mitigiert**

## Evidence

`docs/evidence/rescue/RESCUE_BOOT_MENU_BRANDING_PRECHECK.md` vorhanden.

Branding blockiert Build **nicht** (Assets + Wrapper vorhanden).
