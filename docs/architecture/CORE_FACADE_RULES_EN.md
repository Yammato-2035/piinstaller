# Core Facade Rules (Phase A.1 — Freeze)

**Status:** ACTIVE — caller migration A.2–A.4 (safety) complete; boundary still warn-only globally.

## Goal

Future modules (backup, restore, rescue stick, partition helper, malware scanner, cloud server, provisioning) must **not** implement parallel storage/mount/safety logic. They use only the three core facades.

## Canonical facades

| Facade | Module | Responsibility |
|--------|--------|----------------|
| Storage | `backend/core/storage_facade.py` | Block devices, blkid excerpts, classification, external targets |
| Mount | `backend/core/mount_facade.py` | findmnt inventory, readonly plans, mount safety (plan-only) |
| Safety | `backend/core/safety_facade.py` | Backup/restore/partition target validation, safety decisions |

**Contract version:** `FACADE_CONTRACT_VERSION = 1` in each facade module.

## Forbidden for new modules (direct use)

New files under `backend/modules/`, `backend/api/`, `backend/rescue/`, backend routes **must not**:

- call `subprocess.run` / `Popen` with `lsblk`, `findmnt`, `blkid`
- `from core.safe_device import validate_write_target` (except inside facade implementation)
- `from safety.write_guard import evaluate_write_target` (except in `safety_facade.py`)
- duplicate mount planners (`plan_readonly_*` outside `mount_facade`)

**Instead:**

```python
from core.storage_facade import get_block_devices, classify_storage_target
from core.mount_facade import build_readonly_mount_plan, validate_not_live_root
from core.safety_facade import validate_backup_target, SafetyContext
```

## Documented exceptions (legacy — migrate later)

| Area | Reason | Sunset |
|------|--------|--------|
| `backend/app.py` | Monolith routes | Router extraction phase B |
| `backend/core/safe_device.py` | Implementation core | Behind facades internally |
| `backend/modules/storage_detection.py` | Inspect pipeline | Delegate to `storage_facade` |
| `backend/safety/write_guard.py` | Pure logic from inspect | Only via `safety_facade` |
| Rescue FAT32/ESP (`rescue_fat32_esp_*`) | Hardware write path with evidence | Dedicated rescue exception |
| `backend/deploy/runner_*.py` | Test/runbook artifacts | Not product API path |
| `backend/inspect/collector.py` | Inspect collector | Migrate with inspect refactor |

## Migrated callers (A.2–A.4 safety)

- `backend/preflight/backup.py`
- `backend/modules/backup_engine.py`
- `backend/modules/restore_engine.py`

Direct legacy import again → `facade_boundary_migrated_caller_blocked`.

Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`

## Migrated callers (B.1 storage)

- `backend/core/backup_target_auto_prepare.py` — `storage_facade` + `safety_facade`
- `backend/inspect/collector.py` — `storage_facade` + `safety_facade`
- `backend/core/partition_storage_facade.py` — `safety_facade`

Direct blkid/lsblk/findmnt outside facades → `facade_boundary_migrated_storage_blocked`.

Details: `docs/architecture/CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`

## Safety contexts

`SafetyContext` in `safety_facade.py`:

- `live` — running Setuphelfer system
- `rescue` — rescue stick / live ISO
- `partition_helper` — partition workbench
- `cloudserver_future` — reserved for cloud server edition

Every `validate_*` / `build_safety_decision` call must set context explicitly.

## Boundary check

`scripts/check-module-boundaries.sh` reports **warnings** (no CI fail yet) for:

- direct `subprocess` + `lsblk` / `findmnt` / `blkid` outside allowlist
- direct import of `safe_device.validate_write_target` or `write_guard.evaluate_write_target` outside facades/legacy core

## Not in A.1

- No API changes
- No runtime migration
- No removal of legacy code
- No moving logic into facades (contracts + thin delegation only)

## Next step (after B.1)

Phase B.2 — `app.py` storage helpers, `inspect_storage.py`, deploy runner registry.
