# Core Facades — Storage, Mount, Safety (Phase A.1)

**Stand:** Facade Freeze A.1  
**Contract-Version:** `FACADE_CONTRACT_VERSION = 1`

## Zweck

Drei kanonische Backend-Facades bündeln Storage-Erkennung, Mount-Planung und Write-Safety. Neue Module (Backup, Restore, Rescue Stick, Partitionshelfer, zukünftige Editionen) sollen **keine parallele** `lsblk`/`findmnt`/`blkid`- oder `write_guard`-Logik implementieren.

Phase A.1 definiert nur **öffentliche Contracts** und dünne Delegation. Legacy-Code (`app.py`, `safe_device.py`, `storage_detection.py`) bleibt unverändert aktiv.

## Facades

| Facade | Modul | Haupt-API |
|--------|-------|-----------|
| Storage | `backend/core/storage_facade.py` | `get_block_devices()`, `get_mounts()`, `classify_storage_target()`, `is_external_target()` |
| Mount | `backend/core/mount_facade.py` | `build_readonly_mount_plan()`, `validate_mount_readonly()`, `validate_source_not_target()`, `validate_not_live_root()` |
| Safety | `backend/core/safety_facade.py` | `validate_backup_target()`, `validate_restore_target()`, `validate_partition_target()`, `build_safety_decision()` |

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

## Nächste Migration (A.2)

Caller schrittweise umstellen, beginnend mit `preflight/backup.py`, dann `backup_engine` / `restore_engine`. Ein Modul pro PR.
