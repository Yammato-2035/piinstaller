# Core Facade Rescue Migration B.4

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.3.0

## Ziel

Vollständige Facade-Delegation für Inspect-Listen (`list_block_devices`, `list_physical_disks`), Rescue-Persistence-Mount-Scan und Deploy-Runner-Metadaten.

## Neue Facade-Einstiegspunkte

| Funktion | Modul |
|----------|-------|
| `list_classified_block_devices_for_inspect` | `storage_facade` |
| `list_physical_disk_paths` | `storage_facade` |
| `get_readonly_storage_probe_contract` | `storage_facade` |
| `discover_mounts_flat` | `mount_facade` |

## Migrierte Caller (B.4)

- `backend/modules/inspect_storage.py` — keine direkten `detect_block_devices`-Imports mehr
- `backend/core/rescue_persistence.py` — `detect_rescue_stick_mount` via `discover_mounts_flat`
- `backend/deploy/runner_rescue_storage_discovery.py` — Plan enthält `facade_contract`

## Ausnahmen

- `storage_detection.py` — Implementierungskern hinter Facades
- `rescue_fat32_esp_usb_writer.py` — Operator-Shell
- `app.py` — Monolith (eigene Router-Extraktion)

## Tests

- `backend/tests/test_core_facade_rescue_migration_b4_v1.py`
- Regression: B.2/B.3 Rescue-Tests
