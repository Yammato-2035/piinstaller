# Core Facade Caller Migration A.2–A.4

**Status:** Complete (safety callers)  
**Base commit:** `42fb673` (Facade Freeze A.1)

## Migrated files

| Phase | File | Before | After |
|-------|------|--------|-------|
| A.2 | `backend/preflight/backup.py` | `safety.write_guard.evaluate_write_target` | `core.safety_facade.evaluate_preflight_write_target` |
| A.3 | `backend/modules/backup_engine.py` | `core.safe_device.validate_write_target` | `core.safety_facade.validate_write_target` |
| A.4 | `backend/modules/restore_engine.py` | `core.safe_device.validate_write_target` | `core.safety_facade.validate_write_target` |

`WriteTargetProtectionError` is still imported from `core.safety_facade` in engines (re-export from `safe_device`).

## Safety facade extensions

New wrappers (delegate only, no new logic):

- `evaluate_preflight_write_target` / `validate_preflight_backup_target`
- `validate_write_target` / `validate_restore_target_for_write`
- `normalize_legacy_safety_result` / `build_safety_decision_from_legacy_result`
- `validate_backup_target_for_write` optionally accepts `inspect_result`

Error codes (`SAFETY_*`, `WriteTargetProtectionError.diagnosis_id`) unchanged.

## Removed direct legacy access

- `from safety.write_guard import …` in `preflight/backup.py`
- `from core.safe_device import validate_write_target` in `backup_engine.py` / `restore_engine.py`

## Remaining legacy access (intentional)

| File | Reason |
|------|--------|
| `backend/app.py` | Monolith — router extraction phase B |
| `backend/core/partition_storage_facade.py` | Phase B.1 storage |
| `backend/core/backup_target_auto_prepare.py` | Phase B.1 storage/mount |
| `backend/inspect/collector.py` | Inspect refactor |
| `backend/core/safe_device.py` | Implementation core behind facade |
| `backend/safety/write_guard.py` | Pure logic behind facade |
| Deploy runners | Not product API path |

## Boundary guard

Before: 3 facade warnings (`preflight`, `backup_engine`, `restore_engine`).  
After: **0** safety warnings for these files.

Migrated callers: direct import again → `facade_boundary_migrated_caller_blocked` (stricter, not yet global CI fail).

Evidence: `docs/evidence/monolith/BOUNDARY_WARNINGS_*_PHASE_A2_A4.txt`

## Tests

- `test_safety_facade_contracts_v1.py` (extended)
- `test_preflight_backup_v1.py`
- `test_backup_recovery_engines.py`
- `test_write_guard_v1.py`

No runtime smokes (runtime gate exit 20, static + unit only).

## Risks

- Semantics still depend on `safe_device`/`write_guard` — facade is passthrough
- `app.py` still uses `safe_device` directly — largest remaining duplicate
- No live hardware behavior test in this run

## Next step

**Phase B.1 — storage caller migration:** `backup_target_auto_prepare.py`, `inspect/collector.py`, `partition_storage_facade.py`
