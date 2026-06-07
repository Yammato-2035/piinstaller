# RESCUE USB FAT32 ESP Writer — Implementation

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_USB_FAT32_ESP_WRITER_IMPLEMENTATION`  
**Version:** `1.7.8.0`  
**HEAD:** vor Commit siehe Abschlussbericht

## Architekturentscheidung

| Punkt | Entscheidung |
|-------|--------------|
| ISO 1.7.7.0 | **bleibt valide** (deep UEFI-Validator grün) |
| dd/isohybrid-Modus | **bleibt erhalten** — kein Entfernen |
| MSI-Bootfehler | Rechtfertigt **alternative Writer-Strategie** FAT32-ESP |
| Ziel | UEFI-Firmware-kompatibler Stick (GPT + FAT32 ESP + BOOTX64.EFI) |
| Agent/Cursor | **Keine echte Schreibausführung** auf Blockgeräten |

## Neue Komponenten

| Artefakt | Zweck |
|----------|-------|
| `backend/core/rescue_fat32_esp_usb_writer.py` | Staging, GRUB-Gen, Safety, Dry-run-Plan |
| `scripts/rescue-live/build-fat32-esp-usb-layout.sh` | ISO → Staging (read-only) |
| `scripts/rescue-live/write-fat32-esp-rescue-usb.sh` | Dry-run default; Write nur mit Confirm |
| `scripts/rescue-live/verify-fat32-esp-rescue-usb.sh` | Read-only Verify auf geschriebenem Stick |
| `backend/tests/test_rescue_fat32_esp_usb_v1.py` | Unit-Tests |

## Staging-Struktur (verifiziert)

```
build/rescue/fat32-esp-staging/
  EFI/BOOT/BOOTX64.EFI
  boot/grub/grub.cfg          (7 menuentry aus live.cfg)
  live/vmlinuz, initrd.img, filesystem.squashfs
  setuphelfer/rescue/boot-branding.txt, version.json, evidence.json
```

## GRUB-Bootparameter

Übernommen aus `isolinux/live.cfg` der validierten ISO (`setuphelfer-rescue-*` Labels).

Live-boot findet `filesystem.squashfs` auf derselben FAT-Partition via `search --file /live/filesystem.squashfs`.

## Sicherheit

- Standard: **dry-run**
- Echter Write: `--operator-confirm-write` + Phrase `WRITE SETUPHELFER FAT32 ESP USB`
- Zusätzlich: Operator-Evidence (`usb_operator_selection_latest.json`) mit `write_allowed=true`
- Blockiert: `/dev/sda`, `/dev/nvme*`, Nicht-USB, zu kleine Geräte
- DCC: zeigt Terminal-Befehle, **führt nichts aus**

## DCC

Compact-Status: `rescue.usb_writer_modes` mit `iso_hybrid_dd` und `fat32_esp`.

Developer Toolbox: FAT32-ESP-Befehlsblock bei `fat32_esp.implemented=true`.

## Nächster Schritt

Operator: `RESCUE_USB_FAT32_ESP_WRITE_OPERATOR_RUN`

## Nicht ausgeführt

dd, Partitionieren, Schreiben auf `/dev/sdb`, MSI-Boot, Push.
