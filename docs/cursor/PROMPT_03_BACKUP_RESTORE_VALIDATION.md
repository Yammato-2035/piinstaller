# Prompt 03 – Backup/Restore-Validierung (Vorbereitung)

## PHASE 0 – Mandatory Runtime Version Gate (Pflicht)

1. `./scripts/check-runtime-deploy-gate.sh` (Exit **0**), falls vorhanden; sonst `./scripts/check-backend-version-gate.sh` und `GET /api/dev-dashboard/status` (`deploy_drift`) manuell.
2. Bei Exit **≠ 0**: **STOP** — kein Backup-/Restore-Test; Abschlussbericht mit Gate-Ergebnis und bei Altstand **`blocked_runtime_outdated`**; siehe `docs/developer/CURSOR_WORK_RULES.md`, `docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md` / `_EN.md`.

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
