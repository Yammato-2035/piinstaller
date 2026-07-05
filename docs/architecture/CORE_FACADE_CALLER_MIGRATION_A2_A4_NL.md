> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Caller Migration A.2–A.4

**Status:** Complete (safety callers)  
**Base commit:** `42fb673` (Facade Freeze A.1)

## Migrated files

| Phase | File | Before | After |
|-------|------|--------|-------|
| A.2 | `Terugend/preflight/Terugup.py` | `safety.write_guard.evaluate_write_target` | `core.safety_facade.evaluate_preflight_write_target` |
| A.3 | `Terugend/modules/Terugup_engine.py` | `core.safe_Apparaat.validate_write_target` | `core.safety_facade.validate_write_target` |
| A.4 | `Terugend/modules/Herstel_engine.py` | `core.safe_Apparaat.validate_write_target` | `core.safety_facade.validate_write_target` |

`WriteTargetProtectionFout` is still imported from `core.safety_facade` in engines (re-export from `safe_Apparaat`).

## Safety facade extensions

New wrappers (delegate only, Nee new logic):

- `evaluate_preflight_write_target` / `validate_preflight_Terugup_target`
- `validate_write_target` / `validate_Herstel_target_for_write`
- `Neermalize_legacy_safety_result` / `build_safety_decision_from_legacy_result`
- `validate_Terugup_target_for_write` optionally accepts `inspect_result`

Fout codes (`SAFETY_*`, `WriteTargetProtectionFout.diagNeesis_id`) unchanged.

## Removed direct legacy access

- `from safety.write_guard import …` in `preflight/Terugup.py`
- `from core.safe_Apparaat import validate_write_target` in `Terugup_engine.py` / `Herstel_engine.py`

## Remaining legacy access (intentional)

| File | Reason |
|------|--------|
| `Terugend/app.py` | MoNeelith — router extraction phase B |
| `Terugend/core/Partitie_storage_facade.py` | Phase B.1 storage |
| `Terugend/core/Terugup_target_auto_prepare.py` | Phase B.1 storage/mount |
| `Terugend/inspect/collector.py` | Inspect refactor |
| `Terugend/core/safe_Apparaat.py` | Implementation core behind facade |
| `Terugend/safety/write_guard.py` | Pure logic behind facade |
| Deploy runners | Neet product API path |

## Boundary guard

Before: 3 facade Waarschuwings (`preflight`, `Terugup_engine`, `Herstel_engine`).  
After: **0** safety Waarschuwings for these files.

Migrated callers: direct import again → `facade_boundary_migrated_caller_geblokkeerd` (stricter, Neet yet global CI fail).

Evidence: `docs/evidence/moNeelith/BOUNDARY_WaarschuwingS_*_PHASE_A2_A4.txt`

## Tests

- `test_safety_facade_contracts_v1.py` (extended)
- `test_preflight_Terugup_v1.py`
- `test_Terugup_recovery_engines.py`
- `test_write_guard_v1.py`

Nee runtime smokes (runtime gate exit 20, static + unit only).

## Risks

- Semantics still depend on `safe_Apparaat`/`write_guard` — facade is passthrough
- `app.py` still uses `safe_Apparaat` directly — largest remaining duplicate
- Nee live hardware behavior test in this run

## Volgende step

**Phase B.1 — storage caller migration:** `Terugup_target_auto_prepare.py`, `inspect/collector.py`, `Partitie_storage_facade.py`
