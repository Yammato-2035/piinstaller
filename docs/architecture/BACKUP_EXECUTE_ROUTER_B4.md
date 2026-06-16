# Backup Execute Router B.4

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.6.0

## Ziel

Erster POST-Slice: Job-Steuerung und Profil-Preview ohne create/restore.

## Extrahiert

| Route | Handler |
|-------|---------|
| `POST /api/backup/jobs/{id}/cancel` | `backup_job_cancel` |
| `POST /api/backup/jobs/{id}/evidence` | `backup_job_evidence_collect` |
| `POST /api/backup/profiles` | `backup_profiles_list_post` |
| `POST /api/backup/profile-preview` | `backup_profile_preview` |

## Module

- `api/routes/backup_execute.py`
- `core/backup_execute_handlers.py`
- Runtime-Erweiterung: `backup_readonly_runtime.py`

## Verbleibend in app.py

settings, create, restore, verify, delete, clone, usb, cloud, target-prepare, schedule

## Tests

- `backend/tests/test_backup_execute_router_b4_v1.py`
- Regression: `test_backup_profiles_v1.py`, `test_backup_job_evidence_api_v1.py`
