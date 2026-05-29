# Live System Boot Validation — Result

**Profil:** `nographic_1200`  
**Ausgeführt:** ja | **Freigabe:** `LIVE_BOOT_NOGRAPHIC_FREIGEGEBEN=1`  
**Klassifikation:** **`timeout_after_bootloader`**

## Command Safety

Kein `-hda`, `-drive`, USB, Host-Disk — nur `-cdrom`.

## Befund (1200s)

| Stufe | Sichtbar |
|-------|----------|
| BIOS / iPXE | ja |
| Bootloader (ISOLINUX 6.04) | ja |
| Kernel | **nein** (Serial) |
| Initrd | **nein** |
| Live-System / Login | **nein** |
| Setuphelfer | **nein** |

**stdout:** 374 Bytes — **byte-identisch** zum 600s-nographic-Lauf.  
**qemu_exit:** 124 (timeout)

## Interpretation

Bootloader-Nachweis bestätigt; **kein** Live-System-Nachweis über nographic/Serial. Nächster Schritt: **visueller Operator-Smoke** (`RESCUE_ISO_VM_VISUAL_BOOT_OPERATOR_RUN`).

Rescue **yellow**, kein full-green.

JSON: `rescue_iso_live_system_boot_validation_result_latest.json`
