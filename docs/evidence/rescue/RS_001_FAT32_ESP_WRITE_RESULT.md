# RS-001 FAT32-ESP USB Write Result

**Status:** Template — wird nach erstem Operator-`--execute-write`-Lauf automatisch aktualisiert.

---

## Summary

| Field | Value |
|-------|-------|
| target_device | *(pending operator run)* |
| write_executed | `false` |
| write_status | `not_run` |
| verify_status | `not_run` |
| rs001_status | `red` |

**rs001_reason:** USB written but hardware boot not yet proven

---

## Operator command (destructive — Cursor must not run)

```bash
export USB_DEVICE=/dev/sdb

./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_DEVICE" \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --execute-write

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_DEVICE"
```

---

## Artifacts (after run)

- `docs/evidence/runtime-results/rescue/fat32_esp_write_<timestamp>/`
- `docs/evidence/runtime-results/rescue/fat32_esp_write_latest.json`

---

## Hardware boot

RS-001 remains **red** until operator documents UEFI boot to Setuphelfer menu/TUI on reference hardware.
