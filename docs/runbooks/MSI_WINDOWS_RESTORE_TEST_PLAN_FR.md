> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/MSI_WINDOWS_RESTORE_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_Restauration_TEST_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Restauration-Test — Plan

**Status:** Plan only

## Ziel

Struktureller Restauration auf **freigegebenes Testziel** (nicht MSI-Interneplatte).

## Abnahme ohne Windows-Passwort

| Kriterium | Erforderlich |
|-----------|--------------|
| Partitionen plausibel | Ja |
| EFI/Boot-Struktur | Ja |
| Windows Boot Manager | Ja |
| Boot bis Login/Lockscreen/Recovery | Ja (Passwort fehlt → erwartet) |
| Interaktiver Login | **Nein** |

## Verboten

- Restauration auf MSI-Systemdisk ohne `wipe_release`
- Passwort-Reset, SAM, BitLocker-Bypass

## Evidence

`Restauration_test.*` in `MSI_Windows_EVIDENCE_SCHEMA.json`
