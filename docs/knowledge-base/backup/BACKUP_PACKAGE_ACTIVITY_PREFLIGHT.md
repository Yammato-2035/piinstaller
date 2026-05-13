# Backup Package Activity Preflight (Knowledge Base)

**Kurz:** Vorbereitende Prüfung und Betreiberführung, damit lange Full-Backups nicht durch **APT/dpkg/Timer**-Kollisionen abbrechen (`UPDATE-CONFLICT-041`).

## Primärdokumente

| Sprache | Pfad |
|---------|------|
| Deutsch | `docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md` |
| English | `docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_EN.md` |

## Betrieb / Evidence

- Fehlerfall Produktion: `docs/evidence/backup-restore/BR-001_package_activity_failure_2026-05-13.md`
- Operator-Runbook (Timer temp. stop/start): `docs/evidence/backup-restore/BR-001_package_activity_retry_runbook_2026-05-13.md`
- Retry-Versuch Dokumentation: `docs/evidence/backup-restore/BR-001_package_timer_paused_retry_2026-05-13.md`

## Produktcode (Ist)

- `backend/app.py`: `_detect_active_package_operations`, `POST /api/backup/create` Preflight, `_run_tar` Laufzeit-Überwachung
- `backend/tools/backup_runner.py`: Preflight vor Inhibit, Laufzeit-Loop während Tar

## Testmatrix

- `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md` — Zeile **BR-011**

## Nächster Implementierungsschritt (nicht Teil dieses Prompts)

API-Endpunkt Preflight, UI-Checkliste, i18n-Keys, Konsolidierung Erkennungslogik, pytest **BR-011**.
