> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_WINDOWS_RESTORE_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_Herstel_TEST_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Herstel-Test — Plan

**Status:** Plan only

## Ziel

Struktureller Herstel auf **freigegebenes Testziel** (nicht MSI-Internplatte).

## Abnahme ohne Windows-Passwort

| Kriterium | Erforderlich |
|-----------|--------------|
| Partitieen plausibel | Ja |
| EFI/Boot-Struktur | Ja |
| Windows Boot Manager | Ja |
| Boot bis Login/Lockscreen/Recovery | Ja (Passwort fehlt → erwartet) |
| Interaktiver Login | **Nein** |

## Verboten

- Herstel auf MSI-Systemdisk ohne `wipe_release`
- Passwort-Reset, SAM, BitLocker-Bypass

## Evidence

`Herstel_test.*` in `MSI_Windows_EVIDENCE_SCHEMA.json`
