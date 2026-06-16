# R.5A PKFix — Test Matrix Preseed

**ISO:** `binary.hybrid.iso` (PKFix-Build)  
**Matrix-Version im Image:** R.4 (`RESCUE_TEST_MATRIX_VERSION = 4`)  
**MANIFEST source_head:** `57e30d9`

## Ampeln (statisch, Post-Build)

| Bereich | Ampel | Begründung |
|---------|-------|------------|
| Browser | **green** | chromium + alternatives x-www-browser → chromium |
| Display | **green** | Xorg, xinit, xset/xrandr |
| Openbox | **green** | openbox + session manager alt |
| Kiosk Scripts | **green** | kiosk-start, kiosk-health in sbin |
| Openbox Autostart | **green** | `etc/xdg/openbox/autostart` |
| Rescue UI | **green** | rescue.html + rescue-BE5PiphK.js |
| Telemetrie-Spool | **green** | telemetry-push + rescue_telemetry_spool.py |
| Evidence Bundle | **green** | evidence.py + rescue_evidence_bundle.py |
| R.3 Persistence | **green** | rescue_persistence.py, rescue_test_matrix.py |
| GRUB Theme | **yellow** | Assets da, `set theme=` fehlt |
| UEFI Boot | **green** | BOOTX64, validate_exit=0 |
| ISOLINUX Fallback | **green** | isolinux.cfg vorhanden |

## Vergleich Vorbuild (R.5A fehlgeschlagen)

| Bereich | Vorbuild | PKFix |
|---------|----------|-------|
| Browser/Display | red | **green** |
| R.3 Module | red | **green** |
| MANIFEST head | a8de59e | **57e30d9** |

## Hinweis

Matrix-Ampeln basieren auf **statischer** SquashFS/ISO-Inspektion. Runtime-Verhalten (Kiosk-Boot, MSI) erfordert separaten Hardware/QEMU-Lauf.
