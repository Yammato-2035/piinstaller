# Prompt 03 – Backup/Restore-Validierung (Vorbereitung)

## PHASE 0 – BACKEND VERSION GATE (Pflicht)

`scripts/check-backend-version-gate.sh` (Exit **0**), `curl -i http://127.0.0.1:8000/api/version` (**HTTP 200**, `status":"success"`), `systemctl status setuphelfer-backend.service --no-pager`. Wenn nicht grün: **stoppen** — kein Backup/Restore-Test; siehe `docs/operations/BACKEND_VERSION_UPDATE_GATE_DE.md` / `_EN.md`.

---

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
