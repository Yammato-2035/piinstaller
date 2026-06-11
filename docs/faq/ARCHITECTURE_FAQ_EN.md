# Architecture FAQ — Core Facades (EN)

Short answers on storage/mount/safety facades (Phase A.1 + caller migration A.2–A.4). No marketing copy.

## What are core facades?

Three modules under `backend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. They are the **canonical interface** for device discovery, mount plans, and write-target checks.

## Why do they exist?

The monolith audit found many duplicates (`lsblk` in `app.py`, `safe_device`, rescue, deploy runners). Facades stop each new module from reimplementing the same logic.

## What changed in A.1?

- Public contracts (types + functions)
- Documentation and inventory
- Warn-only boundary check
- Unit tests for contracts

**Not** changed: existing APIs, runtime behavior, legacy imports.

## Can I still import `safe_device` directly?

**Legacy:** yes, existing code stays. **New modules:** no — use facades only (see `CORE_FACADE_RULES_EN.md`).

## Does the mount facade execute real mounts?

No. `build_readonly_mount_plan` and validators are **plan-only** / analysis.

## Which safety contexts exist?

`live`, `rescue`, `partition_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## When does the boundary check block?

Currently **warnings only** in `check-module-boundaries.sh`. CI blocking is planned for a later phase.

## What was migrated in A.2–A.4?

`preflight/backup.py`, `backup_engine.py`, and `restore_engine.py` import safety only via `core.safety_facade`. Error codes and behavior are unchanged (delegation).

## Why is `app.py` not split immediately?

~18k lines, ~213 routes — router extraction needs its own phase B with OpenAPI parity. Engine safety migration was isolated and low risk.

## Why is the boundary guard still partly warn-only?

`app.py`, deploy runners, and storage legacy are not migrated yet. Stricter checks already apply to the three migrated safety callers.

## Does backup or restore behavior change?

**No** — same `safe_device`/`write_guard` logic, only a central import path. No new target paths, no weakened gates.

## Why is this safer?

Fewer scattered imports → less risk that new modules reimplement safety. The boundary guard detects regressions in migrated files.

## Next step?

Phase B.1: storage callers (`backup_target_auto_prepare`, `inspect/collector`, `partition_storage_facade`).

## Further reading

- `docs/knowledge-base/architecture/CORE_FACADES_EN.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`
