# Preflight backup (EN)

## Goal

Preflight backup is a **preparatory safety stage** before later write actions (restore/deploy/partitioning). This stage itself does **not** perform those actions.

## Endpoints

- `GET /api/preflight/sources`
  - lists candidate sources (read-only)
- `POST /api/preflight/backup/preview`
  - creates plan + `confirmation_token`, no execution
- `POST /api/preflight/backup/execute`
  - executes backup only with valid token and allowed target

## Existing logic reused

- Backup: `modules.backup_engine.create_file_backup`
- Manifest: existing in backup engine
- Verify: `modules.backup_verify.verify_basic`
- Safety hard-stop: `safety.write_guard.evaluate_write_target`

## Target safety policy

- allowed: `SAFETY_BACKUP_TARGET_OK`
- warning + extra confirmation: `SAFETY_EMPTY_DISK`
- blocked: `SAFETY_SYSTEM_DISK`, `SAFETY_LIVE_SYSTEM`, `SAFETY_WINDOWS_DETECTED`, `SAFETY_DUALBOOT`, `SAFETY_UNKNOWN_DEVICE`

## Codes

- `PREFLIGHT_SOURCE_FOUND`
- `PREFLIGHT_SOURCE_UNREADABLE`
- `PREFLIGHT_TARGET_BLOCKED`
- `PREFLIGHT_TARGET_REQUIRES_CONFIRMATION`
- `PREFLIGHT_PLAN_CREATED`
- `PREFLIGHT_TOKEN_INVALID`
- `PREFLIGHT_BACKUP_STARTED`
- `PREFLIGHT_BACKUP_FAILED`
- `PREFLIGHT_BACKUP_VERIFIED`
- `PREFLIGHT_BACKUP_VERIFY_FAILED`
