# Core Facades — Storage, Mount, Safety (Phase A.1)

**Stand:** Facade Freeze A.1 + Safety A.2–A.4 + Storage B.1  
**Contract-Version:** `FACADE_CONTRACT_VERSION = 1`

## Zweck

Drei kanonische Backend-Facades bündeln Storage-Erkennung, Mount-Planung und Write-Safety. Neue Module (Backup, Restore, Rescue Stick, Partitionshelfer, zukünftige Editionen) sollen **keine parallele** `lsblk`/`findmnt`/`blkid`- oder `write_guard`-Logik implementieren.

Phase A.1 definiert nur **öffentliche Contracts** und dünne Delegation. Legacy-Code (`app.py`, `safe_device.py`, `storage_detection.py`) bleibt unverändert aktiv.

## Facades

| Facade | Modul | Haupt-API |
|--------|-------|-----------|
| Storage | `backend/core/storage_facade.py` | `get_block_devices()`, `get_partition_uuid()`, `collect_inspect_storage_bundle()`, `classify_storage_target()` |
| Mount | `backend/core/mount_facade.py` | `build_readonly_mount_plan()`, `validate_mount_readonly()`, `validate_source_not_target()`, `validate_not_live_root()` |
| Safety | `backend/core/safety_facade.py` | `validate_write_target()`, `evaluate_preflight_write_target()`, `validate_backup_target()`, `build_safety_decision()` |

Datentypen: `BlockDeviceInfo`, `MountInfo`, `StorageTargetClassification`, `ReadonlyMountPlan`, `SafetyContext`, `SafetyDecision`.

## Grenzen (A.1)

- Keine API-Routen geändert
- Keine Runtime-Migration bestehender Caller
- Mount-Facade: **plan-only** — keine `mount`/`umount`-Ausführung
- Safety-Facade: delegiert teilweise an `write_guard` / `safe_device` (Implementierungskern bleibt)

## Boundary

`scripts/check-module-boundaries.sh` meldet Warnungen bei direktem `subprocess` + `lsblk`/`findmnt`/`blkid` oder direktem `safe_device`/`write_guard` außerhalb der Allowlist. Noch **kein CI-Block**.

## Verweise

- Regeln: `docs/architecture/CORE_FACADE_RULES.md`
- Inventar Duplikate: `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- Zukünftige Facades: `docs/architecture/FUTURE_FACADE_CANDIDATES.md`
- Tests: `backend/tests/test_*_facade_contracts_v1.py`

## Caller-Migration (A.2–A.4, erledigt)

- `preflight/backup.py`, `backup_engine.py`, `restore_engine.py` → `safety_facade`
- Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4.md`

## Storage-Migration (B.1, erledigt)

`backup_target_auto_prepare.py`, `inspect/collector.py`, `partition_storage_facade.py` — siehe `CORE_FACADE_STORAGE_MIGRATION_B1.md`.

## Nächste Migration (B.2)

`app.py` Storage-Hilfen, `inspect_storage.py`, Deploy Runner Registry.
