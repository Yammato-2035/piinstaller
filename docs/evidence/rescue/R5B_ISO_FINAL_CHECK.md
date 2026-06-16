# R.5B — ISO Final Check

**Datum:** 2026-06-13

## Befehl

```bash
sha256sum build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

## Ergebnis

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 1,3G (1 348 468 736 B) |
| **SHA256** | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| Erwartet | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |

## Bewertung

**SHA256 bestätigt: ja** — Abweichung → STOPP nicht ausgelöst.

## Writer-Gate

Beim USB-Write `--expected-iso-sha256` auf denselben Wert setzen (Script-Default ist veraltet).
