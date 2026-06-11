# Core Facades — Storage, Mount, Safety (Phase A.1)

**Status:** Facade Freeze A.1 + safety A.2–A.4 + storage B.1  
**Contract version:** `FACADE_CONTRACT_VERSION = 1`

## Purpose

Three canonical backend facades centralize storage discovery, mount planning, and write safety. New modules (backup, restore, rescue stick, partition helper, future editions) must **not** reimplement parallel `lsblk`/`findmnt`/`blkid` or `write_guard` logic.

Phase A.1 defines **public contracts** and thin delegation only. Legacy code (`app.py`, `safe_device.py`, `storage_detection.py`) remains active unchanged.

## Facades

| Facade | Module | Main API |
|--------|--------|----------|
| Storage | `backend/core/storage_facade.py` | `get_block_devices()`, `get_partition_uuid()`, `collect_inspect_storage_bundle()`, `classify_storage_target()` |
| Mount | `backend/core/mount_facade.py` | `build_readonly_mount_plan()`, `validate_mount_readonly()`, `validate_source_not_target()`, `validate_not_live_root()` |
| Safety | `backend/core/safety_facade.py` | `validate_write_target()`, `evaluate_preflight_write_target()`, `validate_backup_target()`, `build_safety_decision()` |

Types: `BlockDeviceInfo`, `MountInfo`, `StorageTargetClassification`, `ReadonlyMountPlan`, `SafetyContext`, `SafetyDecision`.

## Limits (A.1)

- No API route changes
- No runtime migration of existing callers
- Mount facade: **plan-only** — no `mount`/`umount` execution
- Safety facade: partially delegates to `write_guard` / `safe_device` (implementation core unchanged)

## Boundary

`scripts/check-module-boundaries.sh` emits warnings for direct `subprocess` + `lsblk`/`findmnt`/`blkid` or direct `safe_device`/`write_guard` outside the allowlist. **No CI block** yet.

## References

- Rules: `docs/architecture/CORE_FACADE_RULES.md` (DE) / `CORE_FACADE_RULES_EN.md`
- Duplicate inventory: `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- Future facades: `docs/architecture/FUTURE_FACADE_CANDIDATES.md`
- Tests: `backend/tests/test_*_facade_contracts_v1.py`

## Caller migration (A.2–A.4, done)

- `preflight/backup.py`, `backup_engine.py`, `restore_engine.py` → `safety_facade`
- Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`

## Storage migration (B.1, done)

`backup_target_auto_prepare.py`, `inspect/collector.py`, `partition_storage_facade.py` — see `CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`.

## Next migration (B.2)

`app.py` storage helpers, `inspect_storage.py`, deploy runner registry.
