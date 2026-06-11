# Architecture FAQ — Core Facades (EN)

Short answers on storage/mount/safety facades (Phase A.1). No marketing copy.

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

## Next step?

Phase A.2: caller migration (e.g. `preflight/backup.py`) — one module per PR.

## Further reading

- `docs/knowledge-base/architecture/CORE_FACADES_EN.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
