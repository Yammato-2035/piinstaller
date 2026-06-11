# Core Facades — Storage, Mount, Safety (Phase A.1)

**Status:** Facade Freeze A.1  
**Contract version:** `FACADE_CONTRACT_VERSION = 1`

## Purpose

Three canonical backend facades centralize storage discovery, mount planning, and write safety. New modules (backup, restore, rescue stick, partition helper, future editions) must **not** reimplement parallel `lsblk`/`findmnt`/`blkid` or `write_guard` logic.

Phase A.1 defines **public contracts** and thin delegation only. Legacy code (`app.py`, `safe_device.py`, `storage_detection.py`) remains active unchanged.

## Facades

| Facade | Module | Main API |
|--------|--------|----------|
| Storage | `backend/core/storage_facade.py` | `get_block_devices()`, `get_mounts()`, `classify_storage_target()`, `is_external_target()` |
| Mount | `backend/core/mount_facade.py` | `build_readonly_mount_plan()`, `validate_mount_readonly()`, `validate_source_not_target()`, `validate_not_live_root()` |
| Safety | `backend/core/safety_facade.py` | `validate_backup_target()`, `validate_restore_target()`, `validate_partition_target()`, `build_safety_decision()` |

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

## Next migration (A.2)

Migrate callers incrementally, starting with `preflight/backup.py`, then `backup_engine` / `restore_engine`. One module per PR.
