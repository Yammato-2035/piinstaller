# RESCUE USB FAT32 ESP — Stale ISO Signature & Verify Fix

**Datum:** 2026-06-07  
**Version:** `1.7.8.3`  
**Prompt:** `RESCUE_USB_FAT32_ESP_STALE_ISO_SIGNATURE_AND_VERIFY_FIX`

## Symptom (Operator-Lauf)

| Device | Befund |
|--------|--------|
| `/dev/sdb` | `PTTYPE=gpt`, zusätzlich **stale iso9660** von früherem dd |
| `/dev/sdb1` | EFI UUID, `PARTLABEL=SETUPHELFER_RESCUE`, `FSTYPE=vfat`, `LABEL=SETUPHELFER` |
| `sudo blkid -p /dev/sdb1` | `LABEL="SETUPHELFER"` ✓ |
| Verify (alt) | `FAT_LABEL=missing` → Exit 22 ✗ |

## Root Cause Label

`verify-fat32-esp-rescue-usb.sh` rief `blkid -p` **ohne sudo** auf. Auf Block-Devices liefert das oft leer — obwohl `sudo blkid -p /dev/sdb1` korrekt ist. Das Parent-Device wurde **nicht** für Label genutzt; das Problem war fehlende Rechte/Fallback-Reihenfolge, nicht falsches Device.

## Root Cause Stale Signature

Nach dd/isohybrid bleibt **iso9660-Signatur am Parent** (`/dev/sdb`) erhalten, auch wenn GPT + vfat-Partition korrekt ist. Verify darf Partition trotzdem akzeptieren und nur warnen.

## Fixes

### Writer (vor sgdisk)

```bash
sudo wipefs --no-act "$TARGET"    # protokollieren
sudo wipefs -a "$TARGET"          # Voll-Rebuild
sudo sgdisk --zap-all "$TARGET"
# Reparatur (nur stale iso9660): sudo wipefs -a -t iso9660 "$TARGET"
```

### Verify

- Label **nur** von `${TARGET}1` via `sudo blkid -p`, Fallback `sudo fatlabel`/`dosfslabel`
- Stale parent iso9660 + korrekte Partition → **Warnung** `RESCUE-FAT32-WARN-STALE-PARENT-ISO9660-SIGNATURE`, Exit 0
- Reparaturhinweis: `sudo wipefs -a -t iso9660 /dev/sdb`
- Pflichtdatei ergänzt: `setuphelfer/rescue/boot-branding.txt`

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_VERIFY_AND_MSI_BOOT_HANDOFF`

## Nicht ausgeführt

Kein Write, sgdisk, mkfs, dd, MSI-Test, Push.
