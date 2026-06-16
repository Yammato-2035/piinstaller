# R.5 — Operator Gate B (USB-Write)

## Prüfung

```bash
echo "${OPERATOR_USB_WRITE_FREIGABE:-0}"  # 0
echo "${USB_TARGET:-}"                     # (leer)
```

## Status

**`blocked_operator_usb_write_required`**

Zusätzlich: **`blocked_usb_target_required`**

## Voraussetzungen vor Write

1. `OPERATOR_USB_WRITE_FREIGABE=1`
2. `USB_TARGET=/dev/sdX` (exakt, vom Operator bestätigt)
3. `USB_TARGET_CONFIRMED=1`
4. Neues ISO mit **grünem** SquashFS Kiosk-Check (R.5 Phase 5)
5. `lsblk` vor Write dokumentieren

## Bevorzugtes Skript

```text
scripts/rescue-live/write-fat32-esp-rescue-usb.sh
```

Verify: `scripts/rescue-live/verify-fat32-esp-rescue-usb.sh`

## lsblk (read-only, Referenz)

Vor Write vom Operator ausführen und in `R5_USB_WRITE_LOG.md` eintragen — **keine Seriennummern in Git committen unredacted**.
