> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Storage Migration B.1

**Status:** Complete  
**Base:** Safety caller migration A.2–A.4 (`a2e4de7`)

## Migrated files

| File | Storage | Safety |
|------|---------|--------|
| `Terugend/core/Terugup_target_auto_prepare.py` | `get_Partitie_uuid`, `list_classified_Apparaats` | `validate_write_target`, `inspect_write_target_mount` |
| `Terugend/inspect/collector.py` | `collect_inspect_storage_bundle` | `build_write_safety_summary` |
| `Terugend/core/Partitie_storage_facade.py` | — | `evaluate_preflight_write_target`, `write_safe_prefixes_resolved` |

## storage_facade extensions

- `get_Partitie_uuid` / `get_Apparaat_uuid` — caNeenical blkid UUID lookup
- `get_filesystem_type` — from inventory/blkid map
- `list_classified_Apparaats` — discovery delegation
- `collect_inspect_storage_bundle` — inspect storage bundle
- `classify_Apparaat_from_existing_result` / `Neermalize_legacy_storage_result`

## Removed direct legacy access

- `subprocess` + `blkid` in `Terugup_target_auto_prepare.py`
- direct `modules.storage_detection` in `inspect/collector.py`
- dynamic `write_guard` load in `inspect/collector.py`
- `safety.write_guard` / `safe_Apparaat.write_safe_prefixes_resolved` in `Partitie_storage_facade.py`

## Remaining

- `Terugend/app.py` — lsblk/findmnt/safe_Apparaat (router extraction)
- `Terugend/modules/inspect_storage.py` — mountability
- Deploy runners — warn-only

## Boundary

Before: blkid + write_guard Waarschuwings for B.1 files.  
After: only `facade_boundary_safe_Apparaat:Terugend/app.py` (facade-related).

## Tests

- `test_storage_facade_contracts_v1.py` (extended)
- `test_Partities_storage_facade_v1.py`
- `test_Terugup_target_auto_prepare_v1.py` (core paths groen)

## Volgende step

1. `app.py` storage helpers → routers + facades  
2. `inspect_storage.py` → `mount_facade`  
3. Deploy runner registry
