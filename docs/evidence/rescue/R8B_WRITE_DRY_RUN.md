# R.8B — Write Dry-Run

**Datum:** 2026-06-13

## Befehl (mit Target)

```bash
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target /dev/sdb \
  --expected-iso-sha256 18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390 \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --dry-run
```

Exit: **0**

## Ergebnis

| Feld | Wert |
|------|------|
| `write_executed` | **false** |
| `iso_sha256` im Plan | `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390` |
| Target | `/dev/sdb` |
| Partition | `/dev/sdb1` |
| `safety.blocked` (dry-run) | false |
| USB-Kandidat selectable | **true** |

## Ohne `--target`

Exit **20** (Usage) — `blocked_usb_target_empty` wenn Operator kein Target übergibt.

## Bewertung

Dry-run **plausibel** — Plan zeigt R.8-ISO, korrektes Gerät, keine Repo-Pfade außerhalb Build-Tree.

**Hinweis:** Dry-run prüft Mount-Status nicht für execute — Mount-Blocker erscheint erst bei `--execute-write`.
