# MSI Windows Restore-Test — Plan

**Status:** Plan only

## Ziel

Struktureller Restore auf **freigegebenes Testziel** (nicht MSI-Internplatte).

## Abnahme ohne Windows-Passwort

| Kriterium | Erforderlich |
|-----------|--------------|
| Partitionen plausibel | Ja |
| EFI/Boot-Struktur | Ja |
| Windows Boot Manager | Ja |
| Boot bis Login/Lockscreen/Recovery | Ja (Passwort fehlt → erwartet) |
| Interaktiver Login | **Nein** |

## Verboten

- Restore auf MSI-Systemdisk ohne `wipe_release`
- Passwort-Reset, SAM, BitLocker-Bypass

## Evidence

`restore_test.*` in `MSI_WINDOWS_EVIDENCE_SCHEMA.json`
