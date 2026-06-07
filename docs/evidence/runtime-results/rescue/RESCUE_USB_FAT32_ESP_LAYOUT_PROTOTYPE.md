# RESCUE USB FAT32 ESP Layout — Prototyp (Planung)

**Status:** Planung only — **kein Schreiben auf /dev/sdb**  
**Auslöser:** MSI-Laptop bootet nicht von isohybrid ISO9660-Stick trotz validiertem Readback und deep-UEFI-ISO.

## Problem mit isohybrid-dd

| Aspekt | isohybrid ISO9660 (aktuell) | MSI-Realität |
|--------|----------------------------|--------------|
| Partitionstyp auf USB | `0x17` Hidden IFS, iso9660 | Viele UEFI-Firmwares erwarten `0xEF` FAT-ESP |
| UEFI-Bootweg | El-Torito → embedded `efi.img` in ISO9660 | Firmware findet keinen bootfähigen ESP-Eintrag |
| GPT auf Stick | Protective GPT im Image, `partprobe` warnt rekursiv | Boot-Menü leer oder Boot schlägt fehl |
| dd-Workflow | Einfach, byte-identisch | Auf MSI unzuverlässig |

## Ziel-Layout: GPT + FAT32 ESP

```
/dev/sdX
├── partition 1: EFI System Partition (FAT32, type EF00)
│   ├── EFI/BOOT/BOOTX64.EFI   (grub-mkstandalone)
│   └── boot/grub/grub.cfg
├── partition 2: ISO9660 oder ext4 data (optional)
│   ├── live/vmlinuz
│   ├── live/initrd.img
│   └── live/filesystem.squashfs
└── (optional) partition 3: persistent logs/config (ext4, label SETUPHELFER_RESCUE_DATA)
```

## Boot-Flow UEFI

1. Firmware lädt `EFI/BOOT/BOOTX64.EFI` von FAT-ESP (Standard UEFI removable media path).
2. GRUB `search --file /live/filesystem.squashfs` auf Partition 2 (oder same-disk ISO9660).
3. Linux + live-boot wie bisher.

## Komponenten (Workspace-Reuse)

| Artefakt | Quelle |
|----------|--------|
| `BOOTX64.EFI` + `grub.cfg` | `patch-rescue-iso-uefi-x64.sh` Logik |
| SquashFS/Kernel/Initrd | `binary/live/` aus live-build |
| ISOLINUX-Menü (BIOS) | optional Partition 2 oder entfallen (MSI nur UEFI) |
| Start-Assistant-Services | unverändert im SquashFS |

## Neues Tooling (vorgeschlagen)

```
scripts/rescue-live/write-rescue-usb-fat32-esp.sh
  --iso binary.hybrid.iso
  --target /dev/sdb
  --dry-run / --plan-only
  --operator-confirm
```

**Phasen:**

1. SquashFS/Kernel/Initrd aus ISO extrahieren (xorriso, read-only).
2. GPT-Partitionstabelle auf Zielgerät schreiben (nur nach Operator-Confirm).
3. FAT32 ESP formatieren, GRUB installieren.
4. Datenpartition mit Live-Artefakten füllen.
5. SHA256 über relevante Bereiche + Mount-Verifikation.
6. **Kein Agent-dd** — Operator-only wie bisher.

## Abgrenzung ISO vs USB

| Artefakt | Zweck |
|----------|-------|
| `binary.hybrid.iso` | QEMU/Lab, BIOS+UEFI El-Torito, Archiv |
| FAT32-ESP-Stick-Writer | MSI/Real-Hardware UEFI-Boot |

## Risiken / offene Punkte

- BIOS-Legacy-Boot entfällt auf ESP-only-Stick (für MSI UEFI akzeptabel).
- Größe: SquashFS ~531M + Kernel/Initrd → ESP allein zu klein; **Daten müssen auf Partition 2**.
- Secure Boot: unsigned GRUB — wie bisher.
- Dual-Boot mit Windows auf nvme — Writer darf nur `/dev/sdb` anfassen.

## Gate-Auswirkung

Erst nach Prototyp + Operator-Write + MSI-Boot-Nachweis:

- `target_laptop_booted_from_stick=true`
- `target_network_telemetry_validated` → Folge-Prompt

## Nächster Implementierungs-Prompt

`RESCUE_USB_FAT32_ESP_WRITER_IMPLEMENTATION`

## Nicht in diesem Schritt

dd, Partitionieren, Schreiben auf `/dev/sdb`, ISO-Rebuild.
