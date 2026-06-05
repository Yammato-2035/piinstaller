# Rescue ISO UEFI-x64 Rebuild — Operator Handoff

**Track:** `RESCUE_ISO_UEFI_X64_REBUILD_OPERATOR_RUN`
**Status:** Fix im Workspace vorbereitet — **kein Build/Patch in Agent-Lauf**
**Baseline ISO SHA256:** `1899f5cabf9d40c9581805def9a765557a2168fc11ac181b0f71bfc0b1ff0691`
**Klassifikation:** `iso_bios_hybrid_bootable_only`, `uefi_boot_path_missing`, `efi_boot_files_missing`, `msi_uefi_boot_failed_confirmed`

## Preflight

1. `git status --short` — nur Rescue-UEFI-Änderungen committen.
2. `./scripts/check-backend-version-gate.sh` (optional, kein Deploy/Restart in diesem Track).
3. Temp-Runtime-Bundle validieren:
   ```bash
   ./scripts/rescue-live/validate-temp-runtime-bundle.sh build/rescue/temp-runtime/setuphelfer-rescue-runtime
   ```
4. Build-Tree neu materialisieren:
   ```bash
   ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
   ./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
   ```
5. Erwartete Build-Tree-Marker:
   - `config/package-lists/setuphelfer.list.binary` enthält `grub-efi-amd64-bin`, `grub-common`
   - `config/bootloaders/grub-efi/setuphelfer-grub-efi-note.txt`
   - `auto/config` mit `LB_COMMON` + `--bootloaders syslinux,grub-efi` wenn live-build es unterstützt

## Erwarteter Rebuild (Operator-Terminal, Root/sudo)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
# bei stale root-owned Artefakten:
sudo /home/volker/piinstaller/scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
/home/volker/piinstaller/scripts/rescue-live/prepare-controlled-live-build-tree.sh
./auto/config
cd /home/volker/piinstaller
sudo env PATH="/home/volker/piinstaller/build/rescue/tool-compat/bin:$PATH" \
  ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

**Hinweis live-build 3.0 (Ubuntu):** `--bootloaders` fehlt — ISO bleibt isolinux-only bis Post-Patch.

## UEFI-x64 Post-Patch (Pflicht auf live-build 3.0)

```bash
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place "$ISO"
```

## Validator-Kommandos (read-only)

```bash
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso

# Squashfs/Runtime (bestehend)
./scripts/rescue-live/validate-rescue-iso-squashfs.sh "$ISO"

# UEFI-x64 (neu, muss Exit 0)
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"
sha256sum "$ISO"
```

## Erwartete xorriso-Prüfung (nach erfolgreichem Fix)

```bash
xorriso -indev "$ISO" -report_el_torito as_mkisofs | tee /tmp/rescue-eltorito.txt
grep -E 'isolinux\.bin|efi\.img|append_partition.*0xef' /tmp/rescue-eltorito.txt
xorriso -osirrox on -indev "$ISO" -find /EFI/BOOT -name BOOTX64.EFI
```

**Grün wenn:**
- BIOS: `-b '/isolinux/isolinux.bin'` (oder äquivalent)
- EFI: `-e boot/grub/efi.img` oder `-eltorito-alt-boot` + `append_partition … 0xef`
- Datei: `/EFI/BOOT/BOOTX64.EFI` auf ISO vorhanden

## USB-Write-Folge (erst nach UEFI-Validator grün)

**Nicht** in diesem Handoff ausführen, solange `validate-rescue-iso-uefi-boot.sh` rot ist.

Reihenfolge danach:
1. `RESCUE_USB_WRITE_OPERATOR_HANDOFF_FOR_WINDOWS_INSPECT.md`
2. MSI-Laptop UEFI-Boot-Test (separater Schritt)
3. Erst dann Windows-Inspect

## MSI UEFI-Boot-Test (separater Operator-Schritt)

1. Secure Boot **off**, UEFI-Modus, USB-Stick als Boot-Device.
2. Boot erfolgreich → Evidence `rescue_iso_uefi_boot_baseline_latest.json` / Gate-Status aktualisieren (`target_uefi_boot_validated: true`).
3. Boot fehlgeschlagen → `RESCUE-UEFI-004`, kein Windows-Inspect.

## Verboten in Agent-Session

- USB schreiben, `dd`, Backup, Restore, Partitionieren, Windows-Inspect, `apt install/upgrade`, Deploy, Backend-Restart.

## Evidence-Ziele nach Operator-Lauf

- `docs/evidence/runtime-results/rescue/rescue_iso_uefi_boot_baseline_latest.json` (neue SHA256, validator exit 0)
- `docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json` (`uefi_boot_ready: true` vor USB-Prompt)
