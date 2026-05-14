# KB — Backup performance, profiles, progress

- **Code:** `backend/core/backup_archive_options.py`, `backend/core/backup_progress.py`, `backend/tools/backup_runner.py`
- **Evidence auto-collect:** `backend/tools/backup_evidence_collector.py` (siehe `BACKUP_EVIDENCE_COLLECTOR_DE.md`); **API:** `GET`/`POST /api/backup/jobs/{job_id}/evidence` in `app.py`
- **UI:** `BackupJobProgressSection`, `BackupJobEvidencePanel`, `RunningBackupModal`, `BackupRestore.tsx`; i18n `runningBackup.progress.*`, `runningBackup.evidence.*`
- **Tests:** `test_backup_archive_options_v1.py`, `test_backup_progress_merge_v1.py`, `test_backup_job_evidence_api_v1.py`; Frontend Vitest `backupJobProgressDisplay.test.ts`

Zielpfad-Politik unverändert: nur freigegebene externe Pfade (z. B. `/media/gabriel/setuphelfer-back`).
