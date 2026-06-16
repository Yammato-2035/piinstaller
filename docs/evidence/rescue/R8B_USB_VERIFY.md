# R.8B — USB Verify

**Datum:** 2026-06-13

## Status

**Nicht ausgeführt** — kein erfolgreicher Write.

Verify setzt voraus:

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

nach erfolgreichem `--execute-write`.

## Aktueller Stick (read-only, pre-R.8 Inhalt)

| Check | Status |
|-------|--------|
| FAT32 mountable | ja |
| `live/filesystem.squashfs` | vorhanden (SHA `983492b08f…` = **alt**) |
| R.8 ISO Squashfs | **nein** — Write ausstehend |

## Nächster Schritt

Verify nach Operator-Write mit erwarteter ISO-SHA `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390`.
