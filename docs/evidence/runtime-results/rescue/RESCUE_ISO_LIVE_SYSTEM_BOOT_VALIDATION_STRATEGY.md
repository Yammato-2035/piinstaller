# Live System Boot — Strategie

## Profil A — nographic 1200s (ausgeführt)

- Logbar, kein Host-Disk
- **Ergebnis:** identisch zu 600s (374 Bytes) — nur SeaBIOS/iPXE/ISOLINUX, kein Kernel auf Serial

## Profil B — visueller Operator-Smoke (empfohlen)

```bash
export LIVE_BOOT_VISUAL_FREIGEGEBEN=1
ISO_PATH="…/binary.hybrid.iso"
qemu-system-x86_64 -m 2048 -smp 2 -cdrom "$ISO_PATH" -boot d -snapshot -no-reboot
```

Operator prüft: Boot-Menü (ENTER?), Kernel, Live-Login, optional Setuphelfer.

**Hypothese:** ISOLINUX wartet auf Menü-Timeout/ENTER; Debian-Live-Kernel schreibt oft nicht auf Serial.

JSON: `rescue_iso_live_system_boot_validation_strategy_latest.json`
