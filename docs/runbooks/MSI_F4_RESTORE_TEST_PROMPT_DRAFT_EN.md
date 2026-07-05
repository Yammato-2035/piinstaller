> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_F4_RESTORE_TEST_PROMPT_DRAFT_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI F.4 — Restore Test (Prompt-Entwurf)

**Voraussetzung:** F.3 success

## Regeln

- Nur freigegebenes **Testziel** (niemals Original-MSI-Systemdisk)
- Operator-Doppelbestätigung
- Bootstruktur prüfen (EFI, Windows Boot Manager)
- Windows-Login **nicht** erforderlich
- Kein Wipe auf Original ohne separate Freigabe

## Abnahme

Partitionen plausibel; Boot bis Login/Recovery/Lockscreen.
