# Core Facade Rescue Migration B.5

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.4.0

## Ziel

`app.py` Storage-Helfer und Safety-Validierung über Core-Facades delegieren; kein direkter `storage_discovery`/`safe_device`-Import mehr in HTTP-Schicht.

## Neue Facade-Einstiegspunkte

| Funktion | Modul |
|----------|-------|
| `get_lsblk_json_tree` | `storage_facade` |
| `find_lsblk_node_by_mountpoint` | `storage_facade` |
| `find_lsblk_node_by_name` | `storage_facade` |
| `find_disk_by_name` | `storage_facade` |
| `disk_has_system_mount` | `storage_facade` |
| `get_device_fstype` | `storage_facade` |
| `list_devices_for_api` | `storage_facade` |
| `flatten_findmnt_filesystems` | `mount_facade` |
| `discover_mountpoints_for_disk` | `mount_facade` |

## Migrierte Caller (B.5)

- `backend/app.py` — Legacy-Wrapper `_lsblk_*`, `_findmnt_mounts`, `_mountpoints_for_disk`, `_disk_is_system`
- `backend/app.py` — `GET /api/system/devices` via `list_devices_for_api`
- `backend/app.py` — `_validate_backup_dir`, `_validate_restore_target_dir`, Backup-Settings-Fehlerpfad via `safety_facade`

## Ausnahmen

- `storage_discovery.py` / `safe_device.py` — Implementierungskern hinter Facades
- `app.py` — verbleibende ~15k Zeilen Fachlogik (Router-Extraktion E.8+ separat)
- `inspect/collector.py` — nutzt bereits `collect_inspect_storage_bundle` (B.4)

## Tests

- `backend/tests/test_core_facade_rescue_migration_b5_v1.py`
- Regression: `test_backup_findmnt_mount_flatten_v1.py`, B.4-Tests
