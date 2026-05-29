# Rescue ISO Artifact Verify

**Ergebnis:** `artifact_verified`  
**Rescue ISO Artefakt:** `partial_green`  
**Rescue overall:** `yellow` (kein Boot-/USB-/Restore-Nachweis)

## Artefakt

- **Pfad:** `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`
- **Größe:** 507510784 Bytes
- **SHA256:** `03d5aa95ba5e63f603a13bc7ec8765156aadddf3f8e7b6946c0bb08f9aba31f6` (match)
- **file:** ISO 9660, bootable, Volume `SETUPHELFER_RESCUE`
- **isoinfo:** El Torito, `/isolinux/isolinux.bin`, isohybrid-suitable

## Nicht ausgeführt

- mount, losetup, qemu, dd, USB-Write, Restore, Boot-/VM-/Hardwaretest

## Nächster Schritt

`RESCUE_ISO_VM_BOOT_VALIDATION_PREP` — kein USB-Write.

JSON: `rescue_iso_artifact_verify_latest.json`
