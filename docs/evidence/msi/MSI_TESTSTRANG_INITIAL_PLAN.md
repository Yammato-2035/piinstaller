# MSI Teststrang — Initial Plan

**Datum:** 2026-06-16  
**HEAD:** 94c91f1  
**Status:** `planned` — keine Hardware-Aktion

## Scope dieses Laufs

| Aktion | Ausgeführt |
|--------|------------|
| Dokumentation / Contracts | Ja |
| Boundary-Gate verschärft | Ja |
| MSI Read-only Precheck | **Nein** |
| Backup / Restore / Verify | **Nein** |
| Wipe / Linux-Install | **Nein** |

## Nächster Prompt

`STRICT MODE – MSI WINDOWS READ-ONLY PRECHECK RUNTIME`

Erlaubt dann: lsblk, blkid, findmnt (read-only)  
Weiterhin verboten: Backup, Restore, Write, Wipe, Passwortreset

## Verweise

- `docs/hardware-tests/MSI_WINDOWS_TO_LINUX_TEST_PLAN_DE.md`
- `docs/runbooks/MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_DE.md`
- `docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json`
