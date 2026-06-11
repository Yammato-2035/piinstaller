# Storage Discovery Inventory (Phase A.1 — Facade Freeze)

**Stand:** Core Facade Freeze Phase A.1  
**Zweck:** Kartierung aller Storage-/Device-Erkennung vor Migration auf kanonische Facades.  
**Keine Migration in diesem Lauf** — nur Inventar und Ziel-Facade-Zuordnung.

## Legende

| Spalte | Bedeutung |
|--------|-----------|
| Duplikat? | `ja` = parallele lsblk/findmnt/blkid- oder Klassifikationslogik außerhalb Facade |
| Ziel-Facade | `storage_facade`, `mount_facade`, `safety_facade` oder `legacy` (später migrieren) |

## Kern-Inventar

| Funktion | Datei | Verantwortlichkeit | Duplikat? | Ziel-Facade |
|----------|-------|-------------------|-----------|-------------|
| `build_storage_inventory_snapshot` | `backend/core/storage_facade.py` | Kanonische lsblk/blkid-Inventur, Kandidaten | nein | `storage_facade` |
| `get_block_devices` / `classify_storage_target` | `backend/core/storage_facade.py` | Phase-A.1-Contract-API | nein | `storage_facade` |
| `detect_block_devices` / `detect_filesystems` | `backend/modules/storage_detection.py` | Blockgeräte + blkid-Map, delegiert safe_device | ja | `storage_facade` |
| `classify_devices` | `backend/modules/storage_detection.py` | Geräteklassifikation für Inspect | ja | `storage_facade` |
| `list_classified_devices` / `validate_write_target` | `backend/core/safe_device.py` | Allowlist, Schreibziel-Schutz, lsblk/findmnt | ja | `safety_facade` + `storage_facade` |
| `classify_storage_role` (v2) | `backend/core/storage_role_classification.py` | Rollen (backup_target, system_disk, …) | ja | `storage_facade` |
| `build_partition_storage_snapshot` | `backend/core/partition_storage_facade.py` | Partitionshelfer-Storage-Envelope | ja | `storage_facade` |
| `build_mount_inventory_snapshot` | `backend/core/mount_facade.py` | findmnt-Inventur (read-only) | nein | `mount_facade` |
| `plan_readonly_source_mount` | `backend/core/mount_facade.py` | Readonly-Mount-Plan (plan-only) | nein | `mount_facade` |
| `evaluate_write_target` | `backend/safety/write_guard.py` | Hard-Stop aus Inspect-Daten | ja | `safety_facade` |
| `validate_backup_target` / `build_safety_decision` | `backend/core/safety_facade.py` | Kanonische Safety-Contracts | nein | `safety_facade` |
| `_lsblk_tree` / `_findmnt_mounts` | `backend/app.py` | Monolith: USB/Clone/Backup-Pfade | ja | `storage_facade` + `mount_facade` |
| `devices_for_api` | `backend/app.py` → `safe_device` | API-Geräteliste | ja | `storage_facade` |
| `collect_storage` | `backend/inspect/collector.py` | Inspect-Sammlung | ja | `storage_facade` |
| `inspect_storage` Modul | `backend/modules/inspect_storage.py` | Mountability, findmnt | ja | `mount_facade` |
| `backup_engine` Zielprüfung | `backend/modules/backup_engine.py` | Backup-Ziel via safe_device | ja | `safety_facade` |
| `restore_engine` Zielprüfung | `backend/modules/restore_engine.py` | Restore-Ziel via safe_device | ja | `safety_facade` |
| `preflight/backup` | `backend/preflight/backup.py` | evaluate_write_target vor Backup | ja | `safety_facade` |
| `rescue/orchestrator` | `backend/rescue/orchestrator.py` | write_guard bei Rescue | ja | `safety_facade` |
| `rescue_hardstop` | `backend/core/rescue_hardstop.py` | Rescue Hard-Stop, lsblk/findmnt | ja | `safety_facade` |
| `device_identity` | `backend/core/device_identity.py` | Geräte-IDs, lsblk | ja | `storage_facade` |
| `backup_target_auto_prepare` | `backend/core/backup_target_auto_prepare.py` | Mount-Vorbereitung, findmnt | ja | `mount_facade` |
| `rescue_fat32_esp_usb_verify` | `backend/core/rescue_fat32_esp_usb_verify.py` | lsblk/blkid für USB-ESP | ja | `storage_facade` (Rescue-Ausnahme) |
| `rescue_usb_operator_selection` | `backend/core/rescue_usb_operator_selection.py` | USB-Auswahl via safe_device | ja | `storage_facade` |
| `lsblk_field` (Rescue Acceptance) | `backend/rescue/rescue_stick_acceptance.py` | Stick-Akzeptanz-Probes | ja | `storage_facade` (Rescue-Ausnahme) |
| `runner_rescue_storage_discovery` | `backend/deploy/runner_rescue_storage_discovery.py` | Deploy-Runner Inventur | ja | `storage_facade` |
| `runner_rescue_readonly_mount_orchestrator` | `backend/deploy/runner_rescue_readonly_mount_orchestrator.py` | Mount-Plan-Orchestrierung | ja | `mount_facade` |
| `runner_rescue_restore_preview_orchestrator` | `backend/deploy/runner_rescue_restore_preview_orchestrator.py` | Restore-Preview Storage | ja | `storage_facade` |
| Weitere Deploy-Runner (17 Dateien) | `backend/deploy/runner_*.py` | Testpläne, Runbooks, HW-Gates | ja | `storage_facade` / `mount_facade` |
| `backup_evidence_collector` | `backend/tools/backup_evidence_collector.py` | Evidence lsblk | ja | `storage_facade` |
| Partitions API | `backend/api/routes/partitions.py` | write_guard-Query-Flag | ja | `safety_facade` |

## Duplikat-Cluster (Priorität Migration)

1. **Monolith `app.py`** — `_lsblk_tree`, `_findmnt_mounts`, `_find_lsblk_by_*` (~15 Aufrufer) → CRITICAL  
2. **`safe_device.py`** — zentrale aber parallele Engine zu `storage_detection` → CRITICAL  
3. **`storage_detection` + `storage_role_classification`** — zwei Klassifikationspfade → HIGH  
4. **Rescue FAT32/ESP Module** — eigene lsblk/blkid-Probes → MEDIUM (documented exception)  
5. **Deploy-Runner** — dokumentierte Test-/Runbook-Duplikate → LOW (kein Produktpfad)

## Kanonische Ziel-API (Freeze A.1)

Neue Module **nur** über:

- `backend/core/storage_facade.py` — `get_block_devices`, `get_mounts`, `classify_storage_target`, `is_external_target`
- `backend/core/mount_facade.py` — `build_readonly_mount_plan`, `validate_mount_readonly`, `validate_source_not_target`, `validate_not_live_root`
- `backend/core/safety_facade.py` — `validate_backup_target`, `validate_restore_target`, `validate_partition_target`, `build_safety_decision`

Siehe `docs/architecture/CORE_FACADE_RULES.md`.
