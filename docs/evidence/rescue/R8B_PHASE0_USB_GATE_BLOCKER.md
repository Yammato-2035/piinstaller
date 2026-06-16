# R.8B — Phase 0 USB Gate Blocker

**Datum:** 2026-06-13

## Git / Version

| Feld | Wert |
|------|------|
| HEAD | `d62b4a1` |
| Branch | `main` |
| Version | `1.7.18.0` |
| ISO SHA256 | `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390` |

## Blockierender Write-Befehl

```bash
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target /dev/sdb \
  --expected-iso-sha256 18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390 \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --execute-write
```

## Fehlermeldung

```
ERROR: execute-write blocked — see gates JSON
Exit: 28
```

## Env zum Diagnosezeitpunkt

| Variable | Wert |
|----------|------|
| `OPERATOR_USB_WRITE_FREIGABE` | **unset** |
| `USB_TARGET` | **unset** |
| `USB_TARGET_CONFIRMED` | **unset** |

Hinweis: `write-fat32-esp-rescue-usb.sh` prüft diese Env-Variablen **nicht direkt** — Gates laufen über `validate_fat32_execute_write_gates()` (Python).

## Write ausgeführt?

**Nein** (vollständig) — Gates blockierten zunächst; nach Test-Unmount schlugen alle `sudo`-Schritte fehl (kein TTY/Passwort). **Kein** `wipefs`/`sgdisk`/`mkfs` erfolgreich.
