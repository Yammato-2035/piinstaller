# Backup Readonly Router B.3

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.5.0

## Ziel

Letzte Backup-GET-Route `target-check` aus `app.py` in den `backup_readonly`-Router extrahieren.

## Extrahiert

- `GET /api/backup/target-check` → `api/routes/backup_readonly.py`
- Handler: `core/backup_target_check_handler.py`
- Runtime-Adapter: `validate_backup_dir`, `sudo_password`, `backup_target_err_to_api`

## Metriken

| Kategorie | Anzahl |
|-----------|--------|
| Backup-GET im Router | **13** (B.2: 12 + B.3: 1) |
| Backup-GET in `app.py` | **0** |

## Bewusst in app.py

Backup POST/Execute: create, restore, clone, usb mount/prepare/eject, verify, delete, settings write.

## Tests

- `backend/tests/test_backup_readonly_router_b3_v1.py`
- Regression: `test_backup_target_permission_diagnostics_v1.py`
