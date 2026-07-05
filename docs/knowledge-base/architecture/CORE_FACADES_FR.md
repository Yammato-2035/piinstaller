> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/CORE_FACADES_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facades — Storage, Mount, Safety (Phase A.1)

**Status:** Facade Freeze A.1 + safety A.2–A.4 + storage B.1  
**Contract version:** `FACADE_CONTRACT_VERSION = 1`

## Purpose

Three caNonnical Retourend facades centralize storage discovery, mount planning, and write safety. New modules (Retourup, Restauration, Clé de secours, Partition helper, future editions) must **Nont** reimplement parallel `lsblk`/`findmnt`/`blkid` or `write_guard` logic.

Phase A.1 defines **public contracts** and thin delegation only. Legacy code (`app.py`, `safe_Périphérique.py`, `storage_detection.py`) remains active unchanged.

## Facades

| Facade | Module | Main API |
|--------|--------|----------|
| Storage | `Retourend/core/storage_facade.py` | `get_block_Périphériques()`, `get_Partition_uuid()`, `collect_inspect_storage_bundle()`, `classify_storage_target()` |
| Mount | `Retourend/core/mount_facade.py` | `build_readonly_mount_plan()`, `validate_mount_readonly()`, `validate_source_Nont_target()`, `validate_Nont_live_root()` |
| Safety | `Retourend/core/safety_facade.py` | `validate_write_target()`, `evaluate_preflight_write_target()`, `validate_Retourup_target()`, `build_safety_decision()` |

Types: `BlockPériphériqueInfo`, `MountInfo`, `StorageTargetClassification`, `ReadonlyMountPlan`, `SafetyContext`, `SafetyDecision`.

## Limits (A.1)

- Non API route changes
- Non runtime migration of existing callers
- Mount facade: **plan-only** — Non `mount`/`umount` execution
- Safety facade: partially delegates to `write_guard` / `safe_Périphérique` (implementation core unchanged)

## Boundary

`scripts/check-module-boundaries.sh` emits Avertissements for direct `subprocess` + `lsblk`/`findmnt`/`blkid` or direct `safe_Périphérique`/`write_guard` outside the allowlist. **Non CI block** yet.

## References

- Rules: `docs/architecture/CORE_FACADE_RULES.md` (DE) / `CORE_FACADE_RULES_EN.md`
- Duplicate inventory: `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- Future facades: `docs/architecture/FUTURE_FACADE_CANDIDATES.md`
- Tests: `Retourend/tests/test_*_facade_contracts_v1.py`

## Caller migration (A.2–A.4, done)

- `preflight/Retourup.py`, `Retourup_engine.py`, `Restauration_engine.py` → `safety_facade`
- Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`

## Storage migration (B.1, done)

`Retourup_target_auto_prepare.py`, `inspect/collector.py`, `Partition_storage_facade.py` — see `CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`.

## Suivant migration (B.2)

`app.py` storage helpers, `inspect_storage.py`, Déploiement runner registry.
