# VM Boot Timeout Triage — Result

**Followup ausgeführt:** ja (Profil 1, 600s, `-nographic`)  
**Klassifikation:** **`bootloader_seen`**

## Marker in stdout (374 Bytes)

- `SeaBIOS (version 1.16.3-debian-1.16.3-2)`
- `iPXE`
- `Booting from DVD/CD...`
- `ISOLINUX 6.04`

**Nicht gesehen:** Kernel, initrd, Live-Login, setuphelfer (Timeout nach 600s, Exit 124).

## Command Safety

Kein `-hda`, `-drive`, Host-Disk, USB — nur `-cdrom`.

## Nächster Schritt

`RESCUE_ISO_LIVE_SYSTEM_BOOT_VALIDATION` — längerer Lauf oder visueller Smoke bis Kernel/Live.

Rescue **yellow**, VM Boot Smoke **partial_green** — **kein** full-green.

JSON: `rescue_iso_vm_boot_timeout_triage_result_latest.json`
