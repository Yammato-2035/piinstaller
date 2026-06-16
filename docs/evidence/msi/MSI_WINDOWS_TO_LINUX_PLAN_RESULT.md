# MSI Windows → Linux — Plan Result

**Datum:** 2026-06-16  
**Status:** `planned`

## Erstellte Dokumente

- `docs/hardware-tests/MSI_WINDOWS_TO_LINUX_TEST_PLAN_DE.md`
- `docs/hardware-tests/MSI_WINDOWS_BACKUP_RESTORE_RUNBOOK_DE.md`
- `docs/hardware-tests/MSI_LINUX_BLUEPRINT_TEST_PLAN_DE.md`
- `docs/runbooks/MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_DE.md`
- `docs/runbooks/MSI_WINDOWS_IMAGE_BACKUP_PLAN_DE.md`
- `docs/runbooks/MSI_WINDOWS_VERIFY_PLAN_DE.md`
- `docs/runbooks/MSI_WINDOWS_RESTORE_TEST_PLAN_DE.md`
- `docs/api/msi_windows_precheck_contract.yaml`
- `docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json`
- `docs/evidence/msi/MSI_TESTSTRANG_INITIAL_PLAN.md`

## Nicht ausgeführt

- Kein MSI-Zugriff
- Kein Backup/Restore/Verify/Wipe
- Kein Windows-Passwortreset
- Kein BitLocker-Bypass
- Kein Linux-Install

## Regeln dokumentiert

Passwort fehlt → Login kein Abnahmekriterium. BitLocker ohne Key → nur Struktur/Rohimage.

## Nächster Schritt

`STRICT MODE – MSI WINDOWS READ-ONLY PRECHECK RUNTIME`
