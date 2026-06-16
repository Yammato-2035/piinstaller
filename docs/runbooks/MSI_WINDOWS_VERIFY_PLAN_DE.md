# MSI Windows Verify — Plan

**Status:** Plan only

## Prüfungen

1. SHA256(Image) == dokumentierter Hash
2. Manifest vorhanden und parsebar
3. Partitionstabelle konsistent mit Precheck
4. Keine stille Korruption (Stichprobe read-only)

## Statuswerte

- `ok` — Verify bestanden
- `failed` — Hash/Manifest-Fehler
- `review_required` — BitLocker ohne Key, nur Strukturprüfung

## Gate vor Restore-Test

Verify muss `ok` oder dokumentiertes `review_required` (BitLocker-Struktur) sein, bevor Restore-Test freigegeben wird.
