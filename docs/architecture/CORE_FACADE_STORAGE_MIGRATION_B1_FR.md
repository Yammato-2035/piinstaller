> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Storage Migration B.1

**Status:** Complete  
**Base:** Safety caller migration A.2–A.4 (`a2e4de7`)

## Migrated files

| File | Storage | Safety |
|------|---------|--------|
| `Retourend/core/Retourup_target_auto_prepare.py` | `get_Partition_uuid`, `list_classified_Périphériques` | `validate_write_target`, `inspect_write_target_mount` |
| `Retourend/inspect/collector.py` | `collect_inspect_storage_bundle` | `build_write_safety_summary` |
| `Retourend/core/Partition_storage_facade.py` | — | `evaluate_preflight_write_target`, `write_safe_prefixes_resolved` |

## storage_facade extensions

- `get_Partition_uuid` / `get_Périphérique_uuid` — caNonnical blkid UUID lookup
- `get_filesystem_type` — from inventory/blkid map
- `list_classified_Périphériques` — discovery delegation
- `collect_inspect_storage_bundle` — inspect storage bundle
- `classify_Périphérique_from_existing_result` / `Nonrmalize_legacy_storage_result`

## Removed direct legacy access

- `subprocess` + `blkid` in `Retourup_target_auto_prepare.py`
- direct `modules.storage_detection` in `inspect/collector.py`
- dynamic `write_guard` load in `inspect/collector.py`
- `safety.write_guard` / `safe_Périphérique.write_safe_prefixes_resolved` in `Partition_storage_facade.py`

## Remaining

- `Retourend/app.py` — lsblk/findmnt/safe_Périphérique (router extraction)
- `Retourend/modules/inspect_storage.py` — mountability
- Déploiement runners — warn-only

## Boundary

Before: blkid + write_guard Avertissements for B.1 files.  
After: only `facade_boundary_safe_Périphérique:Retourend/app.py` (facade-related).

## Tests

- `test_storage_facade_contracts_v1.py` (extended)
- `test_Partitions_storage_facade_v1.py`
- `test_Retourup_target_auto_prepare_v1.py` (core paths vert)

## Suivant step

1. `app.py` storage helpers → routers + facades  
2. `inspect_storage.py` → `mount_facade`  
3. Déploiement runner registry
