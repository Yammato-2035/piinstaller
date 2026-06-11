# Core Facade Storage Migration B.1

**Status:** Complete  
**Base:** Safety caller migration A.2–A.4 (`a2e4de7`)

## Migrated files

| File | Storage | Safety |
|------|---------|--------|
| `backend/core/backup_target_auto_prepare.py` | `get_partition_uuid`, `list_classified_devices` | `validate_write_target`, `inspect_write_target_mount` |
| `backend/inspect/collector.py` | `collect_inspect_storage_bundle` | `build_write_safety_summary` |
| `backend/core/partition_storage_facade.py` | — | `evaluate_preflight_write_target`, `write_safe_prefixes_resolved` |

## storage_facade extensions

- `get_partition_uuid` / `get_device_uuid` — canonical blkid UUID lookup
- `get_filesystem_type` — from inventory/blkid map
- `list_classified_devices` — discovery delegation
- `collect_inspect_storage_bundle` — inspect storage bundle
- `classify_device_from_existing_result` / `normalize_legacy_storage_result`

## Removed direct legacy access

- `subprocess` + `blkid` in `backup_target_auto_prepare.py`
- direct `modules.storage_detection` in `inspect/collector.py`
- dynamic `write_guard` load in `inspect/collector.py`
- `safety.write_guard` / `safe_device.write_safe_prefixes_resolved` in `partition_storage_facade.py`

## Remaining

- `backend/app.py` — lsblk/findmnt/safe_device (router extraction)
- `backend/modules/inspect_storage.py` — mountability
- deploy runners — warn-only

## Boundary

Before: blkid + write_guard warnings for B.1 files.  
After: only `facade_boundary_safe_device:backend/app.py` (facade-related).

## Tests

- `test_storage_facade_contracts_v1.py` (extended)
- `test_partitions_storage_facade_v1.py`
- `test_backup_target_auto_prepare_v1.py` (core paths green)

## Next step

1. `app.py` storage helpers → routers + facades  
2. `inspect_storage.py` → `mount_facade`  
3. deploy runner registry
