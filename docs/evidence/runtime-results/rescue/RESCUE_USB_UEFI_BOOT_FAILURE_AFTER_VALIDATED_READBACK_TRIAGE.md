# RESCUE USB UEFI Boot Failure — Triage nach validiertem Readback

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_USB_UEFI_BOOT_FAILURE_AFTER_VALIDATED_READBACK_TRIAGE`  
**HEAD:** `e5df477` (vor Commit) · **Version:** `1.7.7.0` → `1.7.7.1` (Validator-Fix)  
**Klassifikation:** `RESCUE_USB_BOOT_FAILURE_AFTER_VALIDATED_READBACK`

## Symptom

| Feld | Wert |
|------|------|
| ISO SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |
| USB Readback SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |
| Match | **ja** |
| USB-Gerät | `/dev/sdb` Ultra Line, 59G, Serial `24111412110212` |
| `target_laptop_booted_from_stick` | **false** |

### Sichtbare Bootartefakte (ro-Mount)

- `EFI/BOOT/BOOTX64.EFI` (3,1M)
- `boot/grub/efi.img` (16M, VFAT mit `EFI/BOOT/BOOTX64.EFI`)
- `isolinux/isolinux.bin`, `isolinux.cfg`, `live.cfg`
- `MENU TITLE Setuphelfer Rettungsstick` + alle Custom-Labels

### Operator-Fehlermodus (offen — nicht geraten)

| Unterscheidung | Status |
|----------------|--------|
| `UEFI_MENU_NOT_VISIBLE` | **unbekannt** — Operator muss dokumentieren |
| `UEFI_ENTRY_VISIBLE_BUT_BOOT_FAILS` | **unbekannt** |
| `GRUB_VISIBLE_BUT_LINUX_FAILS` | **unbekannt** |

## Phase 2 — ISO-Struktur (deep, read-only)

| Prüfung | Ergebnis |
|---------|----------|
| `file` | ISO 9660 bootable `SETUPHELFER_RESCUE` |
| El Torito boot catalog | Sektor 532, `/isolinux/boot.cat` |
| xorriso plain UEFI entry | **ja** — img 2 UEFI → `/boot/grub/efi.img` |
| xorriso plain BIOS entry | **ja** — img 1 BIOS → `/isolinux/isolinux.bin` |
| `-isohybrid-gpt-basdat` | **ja** |
| `-append_partition 3 0xef` | **ja** (GPT ESP-Abbild eingebettet) |
| Protective GPT `EFI PART` @ LBA1 | **ja** (Hexdump Offset 0x200) |
| MBR Boot-Signatur `55 AA` | **ja** |
| `efi.img` VFAT bootfähig | **ja** — `BOOTX64.EFI` in `::EFI/BOOT/` |
| GRUB standalone `iso9660` Modul | **ja** (strings in BOOTX64.EFI) |

**Deep-Validator (neu, 1.7.7.1):** Exit **0** — `PLAIN_UEFI=true HYBRID=true EFI_IMG_BOOTABLE=true`

Der alte Validator war **zu flach** (Dateiexistenz + as_mkisofs-Grep). Die ISO besteht aber auch die **verschärfte** Prüfung.

## Phase 3 — USB-Struktur (read-only, ohne sudo-Blockdev)

| Feld | Wert |
|------|------|
| PTTYPE | `dos` (MBR) |
| sdb1 PARTTYPE | `0x17` (Hidden IFS — typisch isohybrid) |
| FSTYPE | `iso9660` |
| Label | `SETUPHELFER_RESCUE` |
| Separate FAT-ESP-Partition (0xEF) sichtbar | **nein** |
| Operator `partprobe` nach dd | „Rekursive Partition auf /dev/sdb“ |

**Bewertung:** Byte-identischer isohybrid-ISO9660-Write. UEFI-Firmware auf MSI sieht vermutlich **keine klassische FAT-ESP-Partition**, sondern muss El-Torito-UEFI aus dem ISO9660-Image laden — das scheitert auf manchen MSI-Geräten trotz korrekter ISO-Metadaten.

## Root Cause (bestätigt / ausgeschlossen)

| Hypothese | Status |
|-----------|--------|
| Fehlende BOOTX64/efi.img | **ausgeschlossen** |
| Fehlender El-Torito-UEFI-Eintrag | **ausgeschlossen** (xorriso plain bestätigt) |
| Post-Patch nur Dateikopie ohne xorriso-Repack | **ausgeschlossen** — Patch nutzt vollständigen xorriso mkisofs |
| USB-Write/Readback korrupt | **ausgeschlossen** (SHA256 Match) |
| Validator Fake-Green (shallow) | **bestätigt historisch** — behoben in 1.7.7.1 |
| ISO strukturell UEFI-defekt | **ausgeschlossen** (deep validator grün) |
| **MSI + isohybrid ISO9660-UEFI inkompatibel** | **wahrscheinlich** (0x17 statt 0xEF, rekursive PT-Warnung) |
| Reine BIOS-Einstellung ohne Layout-Problem | **möglich, unbelegt** |

## Phase 4 — Validator-Änderungen (1.7.7.1)

Neue Fehlercodes:

| Code | Bedeutung |
|------|-----------|
| RESCUE-UEFI-008 | Kein xorriso-plain UEFI-El-Torito-Eintrag / Boot-Catalog fehlt |
| RESCUE-UEFI-009 | Hybrid-USB-Layout unvollständig (GPT/append_partition/isohybrid) |
| RESCUE-UEFI-010 | efi.img kein bootfähiges VFAT mit BOOTX64 |

Tests: `test_rescue_iso_uefi_classify_v1.py` — 7/7 OK.

## Phase 5 — Patch-Pipeline

`patch-rescue-iso-uefi-x64.sh` führt **vollständigen xorriso-Repack** aus:

- `-eltorito-boot isolinux/isolinux.bin` (BIOS)
- `-eltorito-alt-boot -e boot/grub/efi.img` (UEFI)
- `-isohybrid-gpt-basdat -append_partition 2 0xef`
- `-isohybrid-mbr` + `-partition_offset 16`

Kein reiner Dateikopie-Patch. Problem liegt nicht in fehlendem Repack, sondern in **USB-Boot-Kompatibilität des Hybrid-Layouts**.

## Phase 6 — Alternative

Siehe `RESCUE_USB_FAT32_ESP_LAYOUT_PROTOTYPE.md` — GPT + FAT32-ESP-Stick als MSI-robuste Alternative zum isohybrid-dd.

## Entscheidung

| Aktion | Erforderlich |
|--------|--------------|
| ISO-Rebuild mit aktuellem Patch | **nein** (ISO deep-grün) |
| USB-Rewrite gleiche ISO | **nein** (Readback bereits Match) |
| FAT32-ESP-Prototyp | **ja** (empfohlener Fix-Pfad) |
| Operator Boot-Modus dokumentieren | **ja** (offene Unterscheidung) |

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_LAYOUT_PROTOTYPE` — mit paralleler Operator-Dokumentation des MSI-Fehlermodus.

## Nicht ausgeführt

dd, USB-Schreiben, Partitionieren, Windows-Inspect, Backup, Restore, Push.
