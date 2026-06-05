# RESCUE ISO UEFI Patch — Failure Triage

**Status:** `patch_script_fixed_awaiting_operator_run`  
**Datum:** 2026-06-05

## Symptom (Operator-Log)

```text
mkfs.vfat: Attempting to create a too small or a too large filesystem
```

Patch-Skript (`patch-rescue-iso-uefi-x64.sh`) erzeugte zuvor:

```bash
dd if=/dev/zero of="$EFI_IMG" bs=1M count=4
mkfs.vfat -F 16 -n EFIBOOT "$EFI_IMG"
```

## Root Cause

| Check | Ergebnis |
|-------|----------|
| ESP-Größe | 4 MiB |
| mkfs.vfat -F 16 | **Exit 1** — „too small or too large filesystem“ |
| mkfs.vfat -C 32768 (16 MiB) | **Exit 0** |
| 16 MiB zero + mkfs.vfat -F 16 | **Exit 0** |

FAT16 auf 4 MiB ist auf diesem Host zu klein; mindestens ~16 MiB oder `mkfs.vfat -C` mit ausreichend Sektoren.

## Fix (Workspace)

- ESP: `mkfs.vfat -C efi.img 32768` → 16 MiB
- Fehlercodes: `RESCUE-UEFI-PATCH-ESP-SIZE-001`, `MKFS-001`, `GRUB-001`, `XORRISO-001`
- `--plan-only` / `--dry-run` für Agent/Operator-Vorschau ohne Mutation

## ISO-Baseline (unverändert bis Operator-Patch)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `d008fb5ed4fbc0836a08d489434930bbbe3141b9b164b6a101a6eb438d11f94a` |
| UEFI Validator | Exit **34** (isolinux_only) |
| BOOTX64.EFI | **no** |
| EFI El Torito | **no** |

## Nicht ausgeführt (Agent)

- Kein sudo-Patch (root-owned ISO)
- Kein USB-Write
- Kein Windows-Inspect

**Next Prompt:** `RESCUE_ISO_UEFI_PATCH_OPERATOR_RUN`
