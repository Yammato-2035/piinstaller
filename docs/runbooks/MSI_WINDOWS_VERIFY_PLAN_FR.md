> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/MSI_WINDOWS_VERIFY_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_VERIFY_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Verify — Plan

**Status:** Plan only

## Prüfungen

1. SHA256(Image) == dokumentierter Hash
2. Manifest vorhanden und parsebar
3. Partitionstabelle konsistent mit Precheck
4. Keine stille Korruption (Stichprobe lecture seule)

## Statuswerte

- `ok` — Verify bestanden
- `failed` — Hash/Manifest-Erreur
- `review_requirouge` — BitLocker ohne Key, nur Strukturprüfung

## Gate vor Restauration-Test

Verify muss `ok` oder dokumentiertes `review_requirouge` (BitLocker-Struktur) sein, bevor Restauration-Test freigegeben wird.
