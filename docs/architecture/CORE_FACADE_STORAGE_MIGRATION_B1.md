# Core Facade Storage Migration B.1

**Status:** Abgeschlossen  
**Basis:** Safety-Caller-Migration A.2–A.4 (`a2e4de7`)

## Migrierte Dateien

| Datei | Storage | Safety |
|-------|---------|--------|
| `backend/core/backup_target_auto_prepare.py` | `get_partition_uuid`, `list_classified_devices` | `validate_write_target`, `inspect_write_target_mount` |
| `backend/inspect/collector.py` | `collect_inspect_storage_bundle` | `build_write_safety_summary` |
| `backend/core/partition_storage_facade.py` | — | `evaluate_preflight_write_target`, `write_safe_prefixes_resolved` |

## storage_facade Erweiterungen

- `get_partition_uuid` / `get_device_uuid` — kanonischer blkid-UUID-Pfad
- `get_filesystem_type` — aus Inventar/blkid-Map
- `list_classified_devices` — Discovery-Delegation
- `collect_inspect_storage_bundle` — Inspect-Storage-Bündel
- `classify_device_from_existing_result` / `normalize_legacy_storage_result`

## Entfernte direkte Legacy-Zugriffe

- `subprocess` + `blkid` in `backup_target_auto_prepare.py`
- `modules.storage_detection` direkt in `inspect/collector.py`
- Dynamisches `write_guard`-Laden in `inspect/collector.py`
- `safety.write_guard` / `safe_device.write_safe_prefixes_resolved` in `partition_storage_facade.py`

## Verbleibend

- `backend/app.py` — lsblk/findmnt/safe_device (Router-Extraktion)
- `backend/modules/inspect_storage.py` — Mountability
- Deploy-Runner — warn-only

## Boundary

Vorher: blkid + write_guard Warnungen für B.1-Dateien.  
Nachher: nur `facade_boundary_safe_device:backend/app.py` (Facade-relevant).

## Tests

- `test_storage_facade_contracts_v1.py` (erweitert)
- `test_partitions_storage_facade_v1.py`
- `test_backup_target_auto_prepare_v1.py` (Kernpfade grün)

## Nächster Schritt

1. `app.py` Storage-Hilfen → Router + Facades  
2. `inspect_storage.py` → `mount_facade`  
3. Deploy Runner Registry
