# Backup Execute Router B.5

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.7.0

## Ziel

Settings-, Schedule- und Cloud-POST-Routen aus `app.py` extrahieren.

## Extrahiert

| Route | Handler |
|-------|---------|
| `POST /api/backup/settings` | `backup_set_settings` |
| `POST /api/backup/schedule/run-now` | `backup_run_now` |
| `POST /api/backup/cloud/test` | `backup_cloud_test` |
| `POST /api/backup/cloud/delete` | `backup_cloud_delete` |
| `POST /api/backup/cloud/verify` | `backup_cloud_verify` |

## Router gesamt (B.4 + B.5)

**9** POST-Routen in `backup_execute.py`

## Tests

- `backend/tests/test_backup_execute_router_b5_v1.py`
