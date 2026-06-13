# R.4 — GRUB Theme Verification

**Skript:** `scripts/rescue-live/verify-rescue-grub-theme.sh`  
**Ausführung:** Workspace (kein ISO-Build)

## Ergebnis (Workspace)

| Prüfung | Status |
|---------|--------|
| `theme.txt` im Binary-Staging | OK |
| PNG `setuphelfer-boot-menu-de.png` | OK |
| `desktop-image` Referenz | OK |
| `grub.cfg` mit Theme-Eintrag | **WARN** — noch nicht generiert (pre-`lb build`) |
| ISOLINUX Fallback | OK (`isolinux.cfg` vorhanden) |
| Asset-Manifest | OK |

**Exit-Code:** 5 (nur Warnungen, keine Failures)

## ISOLINUX

BIOS-Fallback dokumentiert unter `config/bootloaders/isolinux/isolinux.cfg`. UEFI-Pfad über separates GRUB-Staging (`includes.binary/boot/grub/themes/setuphelfer/`).

## Nach ISO-Build (R.5)

Erneut ausführen und `grub.cfg` auf `set theme` / `themes/setuphelfer` prüfen.

## Staging-Quelle

`scripts/rescue-live/stage-rescue-graphical-assets.sh` — kopiert Theme nach Binary-Image-Pfad.
