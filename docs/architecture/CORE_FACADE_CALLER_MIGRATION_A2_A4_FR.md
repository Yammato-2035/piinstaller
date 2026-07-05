> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Caller Migration A.2–A.4

**Status:** Complete (safety callers)  
**Base commit:** `42fb673` (Facade Freeze A.1)

## Migrated files

| Phase | File | Before | After |
|-------|------|--------|-------|
| A.2 | `Retourend/preflight/Retourup.py` | `safety.write_guard.evaluate_write_target` | `core.safety_facade.evaluate_preflight_write_target` |
| A.3 | `Retourend/modules/Retourup_engine.py` | `core.safe_Périphérique.validate_write_target` | `core.safety_facade.validate_write_target` |
| A.4 | `Retourend/modules/Restauration_engine.py` | `core.safe_Périphérique.validate_write_target` | `core.safety_facade.validate_write_target` |

`WriteTargetProtectionErreur` is still imported from `core.safety_facade` in engines (re-export from `safe_Périphérique`).

## Safety facade extensions

New wrappers (delegate only, Non new logic):

- `evaluate_preflight_write_target` / `validate_preflight_Retourup_target`
- `validate_write_target` / `validate_Restauration_target_for_write`
- `Nonrmalize_legacy_safety_result` / `build_safety_decision_from_legacy_result`
- `validate_Retourup_target_for_write` optionally accepts `inspect_result`

Erreur codes (`SAFETY_*`, `WriteTargetProtectionErreur.diagNonsis_id`) unchanged.

## Removed direct legacy access

- `from safety.write_guard import …` in `preflight/Retourup.py`
- `from core.safe_Périphérique import validate_write_target` in `Retourup_engine.py` / `Restauration_engine.py`

## Remaining legacy access (intentional)

| File | Reason |
|------|--------|
| `Retourend/app.py` | MoNonlith — router extraction phase B |
| `Retourend/core/Partition_storage_facade.py` | Phase B.1 storage |
| `Retourend/core/Retourup_target_auto_prepare.py` | Phase B.1 storage/mount |
| `Retourend/inspect/collector.py` | Inspect refactor |
| `Retourend/core/safe_Périphérique.py` | Implementation core behind facade |
| `Retourend/safety/write_guard.py` | Pure logic behind facade |
| Déploiement runners | Nont product API path |

## Boundary guard

Before: 3 facade Avertissements (`preflight`, `Retourup_engine`, `Restauration_engine`).  
After: **0** safety Avertissements for these files.

Migrated callers: direct import again → `facade_boundary_migrated_caller_bloqué` (stricter, Nont yet global CI fail).

Evidence: `docs/evidence/moNonlith/BOUNDARY_AvertissementS_*_PHASE_A2_A4.txt`

## Tests

- `test_safety_facade_contracts_v1.py` (extended)
- `test_preflight_Retourup_v1.py`
- `test_Retourup_recovery_engines.py`
- `test_write_guard_v1.py`

Non runtime smokes (runtime gate exit 20, static + unit only).

## Risks

- Semantics still depend on `safe_Périphérique`/`write_guard` — facade is passthrough
- `app.py` still uses `safe_Périphérique` directly — largest remaining duplicate
- Non live hardware behavior test in this run

## Suivant step

**Phase B.1 — storage caller migration:** `Retourup_target_auto_prepare.py`, `inspect/collector.py`, `Partition_storage_facade.py`
