# Preflight Backup (DE)

## Ziel

Preflight Backup ist eine **vorbereitende Sicherheitsstufe** vor späteren Schreibaktionen (Restore/Deploy/Partitionierung). In dieser Phase werden **keine** solchen Aktionen ausgeführt.

## Endpunkte

- `GET /api/preflight/sources`
  - listet Kandidat-Quellen (nur lesend)
- `POST /api/preflight/backup/preview`
  - erstellt Plan + `confirmation_token`, führt nichts aus
- `POST /api/preflight/backup/execute`
  - startet Backup nur mit gültigem Token und erlaubtem Ziel

## Verwendete bestehende Logik

- Backup: `modules.backup_engine.create_file_backup`
- Manifest: bestehend in Backup-Engine
- Verify: `modules.backup_verify.verify_basic`
- Safety-Hard-Stop: `safety.write_guard.evaluate_write_target`

## Safety-Regeln für Ziel

- erlaubt: `SAFETY_BACKUP_TARGET_OK`
- Warnpfad mit Extra-Bestätigung: `SAFETY_EMPTY_DISK`
- blockiert: `SAFETY_SYSTEM_DISK`, `SAFETY_LIVE_SYSTEM`, `SAFETY_WINDOWS_DETECTED`, `SAFETY_DUALBOOT`, `SAFETY_UNKNOWN_DEVICE`

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
