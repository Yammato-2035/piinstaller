# R.5B — Operator USB Gate

**Datum:** 2026-06-13  
**Prüfung:** Agent-Shell (kein Operator-TTY)

## Env-Check

```bash
echo "$OPERATOR_USB_WRITE_FREIGABE"   # → leer
echo "$USB_TARGET"                    # → leer
echo "$USB_TARGET_CONFIRMED"          # → leer
```

## Soll-Zustand

| Variable | Erforderlich |
|----------|--------------|
| `OPERATOR_USB_WRITE_FREIGABE` | `1` |
| `USB_TARGET` | `/dev/sdX` (nicht leer) |
| `USB_TARGET_CONFIRMED` | `1` |

## Ergebnis

| Feld | Wert |
|------|------|
| Gate erfüllt | **nein** |
| Status | **`blocked_operator_usb_write_required`** |

## STOPP

Phasen 5–7 (Write, Verify, Stick-Evidence-Preload) **nicht ausgeführt**.

## Operator-Freigabe (TTY)

```bash
cd /home/volker/piinstaller

export OPERATOR_USB_WRITE_FREIGABE=1
export USB_TARGET=/dev/sdX          # physisch verifiziert
export USB_TARGET_CONFIRMED=1

# Gate erneut prüfen:
echo "$OPERATOR_USB_WRITE_FREIGABE" "$USB_TARGET" "$USB_TARGET_CONFIRMED"
```

Danach Phase 4 Dry-Run → Phase 5 Write (siehe `R5B_TARGET_SAFETY_CHECK.md`).
