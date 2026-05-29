# Vorheriger VM-Smoke (120s, serial+display none)

| Feld | Wert |
|------|------|
| stdout leer | **ja** (0 Bytes) |
| stderr nur Timeout | **ja** |
| Bootmarker | **nein** |
| qemu_exit | **124** |
| Host-Disk / USB | **kein Verstoß** |

**Interpretation:** `timeout_no_boot_signal` mit `-display none -serial stdio` bedeutet **nicht**, dass die ISO defekt ist — die Konsole war für BIOS/ISOLINUX effektiv unsichtbar.

JSON: `rescue_iso_vm_boot_timeout_previous_run_analysis_latest.json`
