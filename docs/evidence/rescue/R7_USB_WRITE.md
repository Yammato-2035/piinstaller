# R.7 — USB Write

**Datum:** 2026-06-10

## Gate

| Variable | Wert |
|----------|------|
| `OPERATOR_USB_WRITE_FREIGABE` | **unset** (≠ 1) |

## Agent-Versuch

```bash
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh
```

Exit **20** — Usage/Plan-Modus, kein `--execute-write`.

## Letzter erfolgreicher Write (Referenz, nicht R.7)

| Feld | Wert |
|------|------|
| Write-ID | `fat32_esp_write_20260613_171403` |
| `write_status` | success |
| `verify_status` | success |
| Label | `SETUPHELFER` |
| GPT-Name | `SETUPHELFER_RESCUE` |
| ISO SHA256 | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| Evidence | `docs/evidence/runtime-results/rescue/fat32_esp_write_20260613_171403/result.json` |

## R.7 USB Write

| Feld | Wert |
|------|------|
| Ausgeführt | **nein** |
| Grund | `OPERATOR_USB_WRITE_FREIGABE=1` nicht gesetzt; zusätzlich `blocked_runtime` (Squashfs ohne R.6) |

## Verify (R.7)

Nicht ausgeführt (kein neuer Write).
