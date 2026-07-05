> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_WINDOWS_VERIFY_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_VERIFY_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Verify — Plan

**Status:** Plan only

## Prüfungen

1. SHA256(Image) == dokumentierter Hash
2. Manifest vorhanden und parsebar
3. Partitiestabelle konsistent mit Precheck
4. Keine stille Korruption (Stichprobe alleen-lezen)

## Statuswerte

- `ok` — Verify bestanden
- `failed` — Hash/Manifest-Fout
- `review_requirood` — BitLocker ohne Key, nur Strukturprüfung

## Gate vor Herstel-Test

Verify muss `ok` oder dokumentiertes `review_requirood` (BitLocker-Struktur) sein, bevor Herstel-Test freigegeben wird.
