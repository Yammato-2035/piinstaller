# Core Facade Rescue Migration B.2

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.1.0

## Ziel

Rescue-Restore-Pipeline und nahe Module delegieren Storage-/Mount-Abfragen an Core-Facades statt direkter `lsblk`/`findmnt`-Duplikate.

## Neue Facade-Einstiegspunkte

| Funktion | Modul | Verwendung |
|----------|-------|------------|
| `get_parent_block_device` | `storage_facade` | PKNAME → Whole-Disk |
| `get_block_device_size_bytes` | `storage_facade` | Zielgröße Restore |
| `get_root_block_parent` | `storage_facade` | Systemplatte Gate |
| `list_disk_blockdevice_nodes` | `storage_facade` | USB-Operator-Auswahl |
| `get_lsblk_field` / `get_device_label` | `storage_facade` | FAT32-Verify |
| `get_mount_source_for_path` | `mount_facade` | findmnt SOURCE |

## Migrierte Caller (B.2)

- `backend/core/rescue_hardstop.py`
- `backend/modules/rescue_restore_gate.py`
- `backend/modules/rescue_restore_execute.py`
- `backend/modules/rescue_target_assessment.py`
- `backend/core/rescue_usb_operator_selection.py`
- `backend/core/rescue_msi_diagnostics.py`
- `backend/core/rescue_fat32_esp_usb_verify.py` (teilweise — fatlabel/wipefs bleiben Rescue-spezifisch)

## Dokumentierte Ausnahmen (unverändert)

| Datei | Grund |
|-------|-------|
| `rescue_fat32_esp_usb_writer.py` | Operator-Shell-Handoff mit eingebetteten `lsblk`-Zeilen |
| `rescue_fat32_esp_payload_update.py` | Reine Probe-Validierung (kein subprocess) |
| `modules/rescue_restore_execute.py` / `rescue_*` Hardware-Pfade | Weitere FAT32/ESP-Runner in Set 3 |

## Tests

- `backend/tests/test_core_facade_rescue_migration_b2_v1.py`
- Bestehende Rescue-Tests: `test_rescue_restore_phase3.py`, `test_rescue_usb_operator_selection_v1.py`, `test_rescue_msi_diagnostics_r3.py`, `test_rescue_fat32_esp_usb_verify_v1.py`

## Nächster Schritt (Set 3)

- `modules/rescue_restore_execute.py` Mount-Execution-Pfade (falls noch Low-Level)
- `modules/rescue_target_assessment` → `inspect_storage` Parent-Disk delegieren
- Deploy-Runner Rescue-Emulation (nur Metadaten)
