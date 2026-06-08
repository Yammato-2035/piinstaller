# RS-001 Boot-Artefakt-Audit (Phase 1)

**Datum:** 2026-06-08  
**HEAD:** `669adb7`  
**Branch:** `main`  
**Gate-Skript:** `./scripts/check-runtime-profile-deploy-gate.sh`  
**Gate-Ergebnis:** Exit **12** (`project_version_mismatch:1.7.8.4!=1.7.9.0`)  
**Runtime-Aktionen:** **nicht erlaubt** (Gate rot, kein Deploy/USB/Backend-Restart)  
**Statische Analyse / Artefaktprüfung:** **erlaubt und durchgeführt**

---

## Kanonisches ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 683671552 Bytes (652 MiB) |
| SHA256 | `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |
| `file` | ISO 9660 CD-ROM filesystem data (DOS/MBR boot sector) `SETUPHELFER_RESCUE` (bootable) |
| Build-Datum (mtime) | 2026-06-07 16:23 |
| Projektversion (canonical) | `1.7.9.0` (`config/version.json`) |
| Build-Summary | `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json` (Exit 0, 2026-06-07) |

**Hinweis:** Workspace-Version `1.7.9.0` vs. Runtime `1.7.8.4` — ISO stammt aus Build am 2026-06-07, nicht aus frischem Rebuild dieser Phase.

---

## Bootkatalog / El-Torito

### xorriso `as_mkisofs`

- BIOS: `-b /isolinux/isolinux.bin`, `-c /isolinux/boot.cat`, `-no-emul-boot`
- UEFI: `-eltorito-alt-boot -e /boot/grub/efi.img`, `-no-emul-boot`
- Hybrid: `-isohybrid-gpt-basdat`, `-append_partition 3 0xef`, `-isohybrid-mbr`, `-partition_offset 0`, `-iso_mbr_part_type 0x17`

### xorriso `plain`

| Img | Plattform | Pfad |
|-----|-----------|------|
| 1 | BIOS | `/isolinux/isolinux.bin` |
| 2 | UEFI | `/boot/grub/efi.img` |

**isoinfo:** El Torito VD version 1, boot catalog sector 532, Joliet + Rock Ridge.

---

## UEFI-Deep-Validator

```text
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh <ISO>
→ Exit 0
OK: BIOS=true EFI_ELTORITO=true PLAIN_UEFI=true HYBRID=true BOOTX64=true
    EFI_IMG=true EFI_IMG_BOOTABLE=true DEEP=true
```

---

## UEFI-Dateien (7z-Listing)

| Pfad | Größe |
|------|-------|
| `EFI/BOOT/BOOTX64.EFI` | 3158016 |
| `boot/grub/efi.img` | 16777216 |
| `boot/grub/grub.cfg` | 427 |

### `grub.cfg` (extrahiert)

- `search --set=root --file /live/filesystem.squashfs`
- `linux /live/vmlinuz` + `initrd /live/initrd.img`
- Kernel-Cmdline: `boot=live components init=/lib/systemd/systemd quiet splash setuphelfer_rescue=1`

---

## BIOS-Dateien (ISOLINUX)

| Pfad | Größe |
|------|-------|
| `isolinux/isolinux.bin` | 38912 |
| `isolinux/isolinux.cfg` | 159 |
| `isolinux/live.cfg` | 3116 |
| `isolinux/boot.cat` | 2048 |

### Custom-Menüeinträge in `live.cfg`

- Setuphelfer Rettung starten (`setuphelfer_start_assistant=1`)
- Netzwerk-Assistent (`setuphelfer_network_onboarding=1`)
- MSI/NVIDIA-Kompatibilitätsmodus (`pci=noaer nomodeset setuphelfer_msi_compat=1`)
- Diagnosemodus, toram/Media-Check, reboot/poweroff

---

## Live-Dateien

| Pfad | Größe |
|------|-------|
| `live/vmlinuz` | 8230848 |
| `live/initrd.img` | 38688971 |
| `live/filesystem.squashfs` | 555958272 |

**Bewertung:** Kernel, Initrd und Squashfs vorhanden; Pfade in GRUB/ISOLINUX konsistent (`/live/...`).

---

## Erkannte Inkonsistenzen / Risiken

| Punkt | Bewertung |
|-------|-----------|
| ISO-Struktur UEFI/BIOS | **konsistent** — Deep-Validator grün |
| USB isohybrid auf MSI | **wahrscheinliche HW-Inkompatibilität** — Partition `0x17` statt `0xEF` FAT-ESP (siehe Triage) |
| Standard-ISO ohne `console=ttyS0` | **erwartet** — QEMU-Serial-Smoke liefert 0 Bytes ohne developer-qemu-Profil |
| Workspace vs. Stick-Version | **Drift** — 1.7.9.0 Workspace, letzter MSI-Test mit älterer ISO (`3fe6628a...`) |
| ISO-Rebuild in dieser Phase | **nicht ausgeführt** — `run-controlled-iso-build-with-logging.sh` Exit 20 (Operator/sudo erforderlich) |
| Build-Tree-Validator | **WARN** im Build-Preview — „build tree validator not ready“ |

---

## QEMU-Ergebnis (diese Phase)

| Run | Modus | Exit | Serial-Bytes | Ergebnis |
|-----|-------|------|--------------|----------|
| `rs001_phase1_qemu_serial_20260608_213211` | KVM + chardev serial | 124 | 0 | Kein Serial-Output (kein `console=ttyS0` im Standard-Profil) |
| `rs001_phase1_qemu_serial_retry_20260608_213514` | TCG + legacy `-serial file` | 124 | 0 | Gleich |

**Prior-Nachweis (anderes ISO/Profil):** `docs/evidence/rescue/QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` — ISOLINUX → vmlinuz → systemd in Serial (**grün** für developer-qemu-Profil).

Evidence-Pfade dieser Phase:

- `docs/evidence/rescue/rs001_phase1_qemu_serial_20260608_213211/`
- `docs/evidence/rescue/rs001_phase1_qemu_serial_retry_20260608_213514/`

---

## Rebuild-Ergebnis

| Aktion | Ergebnis |
|--------|----------|
| `run-controlled-iso-build-with-logging.sh` (ohne Flag) | Exit **20** — Build nicht gestartet |
| Grund | Policy guard: root OR TTY operator sudo; `lb build noauto` erfordert sudo |
| Empfehlung | Operator-Rebuild nur mit `--operator-confirm-build` in Operator-Terminal |

**Fazit:** Kein neues ISO in Phase 1. Vorhandenes ISO (2026-06-07) ist strukturell bootfähig (Validator); HW-Blocker liegt nicht an fehlendem UEFI-Repack.

---

## HW-Boot-Blocker (eingegrenzt)

Quelle: `docs/evidence/runtime-results/rescue/RESCUE_USB_UEFI_BOOT_FAILURE_AFTER_VALIDATED_READBACK_TRIAGE.md`

| Hypothese | Status |
|-----------|--------|
| Fehlende BOOTX64/efi.img | **ausgeschlossen** |
| USB-Readback korrupt | **ausgeschlossen** (SHA256 Match bei Test-ISO `3fe6628a...`) |
| ISO strukturell UEFI-defekt | **ausgeschlossen** (Deep-Validator) |
| **MSI + isohybrid ISO9660-UEFI** | **wahrscheinlich** — kein sichtbares FAT-ESP `0xEF` auf Stick |
| Operator-Fehlermodus (Menu/GRUB/Kernel) | **unbekannt** — Operator muss dokumentieren |

**Empfohlener Fix-Pfad:** FAT32-ESP-USB-Writer (`scripts/rescue-live/write-fat32-esp-rescue-usb.sh`) statt isohybrid-dd auf MSI.

---

## Offene Punkte

1. Operator-HW-Boot mit aktuellem ISO (`c9de3751...`) oder FAT32-ESP-Layout
2. Operator dokumentiert UEFI-Fehlermodus (Menu sichtbar? GRUB? Kernel-Panic?)
3. RS-001 Evidence (`docs/evidence/rescue-stick/RS-1.json`) — weiterhin Template/rot
4. Optional: developer-qemu-Rebuild für reproduzierbaren Serial-Smoke (nicht HW-Blocker)

---

*Nur lesende Prüfung. Kein sudo, kein USB-Write, kein ISO-Rebuild.*
