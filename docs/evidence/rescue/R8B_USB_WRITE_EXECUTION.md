# R.8B — USB Write Execution

**Datum:** 2026-06-13

## Ausgeführt?

**Nein** (kein erfolgreicher Write)

## Versuch nach Gate-Freigabe (Diagnose)

Nach Unmount waren Gates `blocked=false`. `--execute-write` gestartet in Agent-Shell.

| Feld | Wert |
|------|------|
| Evidence-Dir | `docs/evidence/runtime-results/rescue/fat32_esp_write_20260613_211315/` |
| Erster Failed Step | `wipefs_probe` |
| Grund | `sudo: Ein Passwort ist notwendig` |
| Alle sudo-Schritte | **fehlgeschlagen** |
| Exit | **29** / **32** |

## Stick-Zustand nach Versuch

| Check | Wert |
|-------|------|
| Partition sdb1 | weiterhin vfat, Label SETUPHELFER, 4G |
| Squashfs SHA auf Stick | `983492b08f…` ( **alt**, pre-R.8) |
| Destructive Änderung | **keine** (sudo blockierte alle Schritte) |

## Operator-Write (ausstehend)

```bash
udisksctl unmount -b /dev/sdb1   # falls gemountet

export OPERATOR_USB_WRITE_FREIGABE=1
export USB_TARGET=/dev/sdb
export USB_TARGET_CONFIRMED=1

./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target /dev/sdb \
  --expected-iso-sha256 18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390 \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --execute-write
```

Im **interaktiven Operator-Terminal** mit sudo.
