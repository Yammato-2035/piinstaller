# Prompt 03 – Backup/Restore-Validierung (Vorbereitung)

STRICT MODE – BACKUP RESTORE VALIDATION PREP

ZIEL:
Testmatrix und Evidence-Templates pflegen, **kein** echter Restore.

NICHT ERLAUBT:
- kein echter Restore, dd, mkfs, mount/umount, sudo, Schreibzugriff auf Systempfade

PHASE 1: `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`

PHASE 2: Testfälle BR-001–BR-010 laut Matrix

PHASE 3: `docs/evidence/backup-restore/BR-*.json` befüllen nach Tests

PHASE 4: ohne Evidence = Rot

ABSCHLUSSBERICHT: Matrix-Status, Templates, offene Tests, Risiken.
