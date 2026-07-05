> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_F4_RESTORE_TEST_PROMPT_DRAFT_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_F4_Herstel_TEST_PROMPT_DRAFT_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI F.4 — Herstel Test (Prompt-Entwurf)

**Voraussetzung:** F.3 Geslaagd

## Regeln

- Nur freigegebenes **Testziel** (niemals Original-MSI-Systemdisk)
- Operator-Doppelbestätigung
- Bootstruktur prüfen (EFI, Windows Boot Manager)
- Windows-Login **nicht** erforderlich
- Kein Wipe auf Original ohne separate Freigabe

## Abnahme

Partitieen plausibel; Boot bis Login/Recovery/Lockscreen.
