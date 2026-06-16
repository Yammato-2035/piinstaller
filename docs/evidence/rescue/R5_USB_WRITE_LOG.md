# R.5 — USB-Write Log

## Status

**Nicht ausgeführt.**

| Grund | Gate |
|-------|------|
| `OPERATOR_USB_WRITE_FREIGABE=0` | Gate B |
| SquashFS Kiosk-Stack fehlt in aktueller ISO | Phase 5 blocked |
| `OPERATOR_ISO_BUILD_FREIGABE=0` | kein neues ISO |

## Geplanter Ablauf (nach Freigabe)

```bash
export OPERATOR_USB_WRITE_FREIGABE=1
export USB_TARGET=/dev/sdX   # Operator-set
export USB_TARGET_CONFIRMED=1
lsblk -o NAME,SIZE,MODEL,TRAN,TYPE,FSTYPE,LABEL,MOUNTPOINTS
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh ...
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh ...
```

Logs hier appendieren nach Operator-Aktion.
