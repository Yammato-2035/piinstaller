# Core Facade Rescue Migration B.3

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.2.0

## Ziel

Inspect-/Identity-/Persistence-Pfade delegieren an Core-Facades; verbleibende direkte `lsblk`/`findmnt`-Aufrufe in Rescue-Nähe reduzieren.

## Neue / erweiterte Facade-Einstiegspunkte

| Funktion | Modul |
|----------|-------|
| `probe_block_device_identity` | `storage_facade` |
| `is_block_device_mounted` | `mount_facade` |
| `get_findmnt_json_by_source` | `mount_facade` |

## Migrierte Caller (B.3)

- `backend/modules/inspect_storage.py` — `_parent_disk`, `detect_filesystems`, `check_mountability`, `readonly_fs_check`
- `backend/core/device_identity.py` — `build_device_identity`
- `backend/core/rescue_persistence.py` — `_label_for_mount` via `build_storage_inventory_snapshot`

## Ausnahmen (unverändert)

- `rescue_fat32_esp_usb_writer.py` — Operator-Shell
- `storage_detection.py` / `safe_device.py` — Implementierungskern hinter Facades
- Deploy-Runner mit Readonly-Hardware-Probes (Metadaten/Evidence, kein Produkt-API-Pfad)

## Tests

- `backend/tests/test_core_facade_rescue_migration_b3_v1.py`
- Bestehend: `test_rescue_restore_phase3.py`, `test_rescue_persistence_r3.py`, `test_rescue_analyze.py`
