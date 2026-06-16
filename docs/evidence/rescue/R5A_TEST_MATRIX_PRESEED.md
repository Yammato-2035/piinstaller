# R.5A — Testmatrix Pre-Seed

**Quelle:** Post-Build SquashFS + ISO statisch (kein Boot)

| Bereich | Ampel | Evidence |
|---------|-------|----------|
| Browser | **red** | chromium/x-www-browser MISSING |
| Display (xorg) | **red** | Xorg/xinit MISSING |
| Openbox | **red** | Binary MISSING (Autostart config FOUND) |
| Kiosk-Skripte | **green** | kiosk-start/health in sbin |
| GRUB Theme Assets | **green** | theme.txt + PNG in ISO |
| GRUB Theme aktiv | **yellow** | kein `set theme` in grub.cfg |
| Rescue UI | **green** | rescue.html + rescue-BE5PiphK.js |
| Telemetrie-Push Skript | **green** | telemetry-push in sbin |
| Telemetrie-Spool Module | **red** | rescue_telemetry_spool.py MISSING |
| Evidence Bundle (Runtime) | **red** | R.3 Module MISSING; evidence.py ohne Backend |
| UEFI Boot Path | **green** | BOOTX64 + validate_exit=0 |
| ISOLINUX Fallback | **green** | isolinux.cfg vorhanden |
| Stick-Persistenz | **gray** | erst nach Boot testbar |
| TUI / WLAN / MSI | **gray** | Hardware pending |

## Matrix-IDs (statisch)

| ID | Erwartung nach Fix |
|----|-------------------|
| R4-BROWSER-PKG-001 | red → green nach Rebuild mit 48-Zeilen package-list |
| R4-KIOSK-001 | yellow (Scripts OK, openbox fehlt) |
| R4-TELEM-SPOOL-INT-001 | red (Modul fehlt im Bundle) |
