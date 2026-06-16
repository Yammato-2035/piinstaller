# R.5 — GRUB-/Asset-Preflight vor Build

**Datum:** 2026-06-10

## Ausführung

```bash
./scripts/rescue-live/stage-rescue-graphical-assets.sh  # Exit 0
./scripts/rescue-live/verify-rescue-grub-theme.sh       # Exit 5
```

## Ergebnis

| Prüfung | Status |
|---------|--------|
| theme.txt | OK |
| PNG setuphelfer-boot-menu-de.png | OK |
| desktop-image Referenz | OK |
| Asset-Manifest | OK (`build/rescue/asset-manifest.json`) |
| GRUB-Theme-Pfad | OK (`includes.binary/boot/grub/themes/setuphelfer/`) |
| ISOLINUX-Fallback | OK (`config/bootloaders/isolinux/isolinux.cfg`) |
| grub.cfg | **WARN** — noch nicht generiert (pre-`lb build`) |

## Bewertung

**Exit 5 = Warnung, buildfähig** — fehlende `grub.cfg` ist erwartet vor erstem `lb build`.

## Nächster Schritt

Gate A setzen → `run-controlled-iso-build-with-logging.sh`
