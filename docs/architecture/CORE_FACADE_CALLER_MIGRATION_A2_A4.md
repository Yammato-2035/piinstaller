# Core Facade Caller Migration A.2–A.4

**Status:** Abgeschlossen (Safety-Caller)  
**Basis-Commit:** `42fb673` (Facade Freeze A.1)

## Migrierte Dateien

| Phase | Datei | Vorher | Nachher |
|-------|-------|--------|---------|
| A.2 | `backend/preflight/backup.py` | `safety.write_guard.evaluate_write_target` | `core.safety_facade.evaluate_preflight_write_target` |
| A.3 | `backend/modules/backup_engine.py` | `core.safe_device.validate_write_target` | `core.safety_facade.validate_write_target` |
| A.4 | `backend/modules/restore_engine.py` | `core.safe_device.validate_write_target` | `core.safety_facade.validate_write_target` |

`WriteTargetProtectionError` wird in Engines weiterhin aus `core.safety_facade` importiert (Re-Export von `safe_device`).

## Safety-Facade-Erweiterungen

Neue Wrapper (delegieren nur, keine neue Logik):

- `evaluate_preflight_write_target` / `validate_preflight_backup_target`
- `validate_write_target` / `validate_restore_target_for_write`
- `normalize_legacy_safety_result` / `build_safety_decision_from_legacy_result`
- `validate_backup_target_for_write` akzeptiert optional `inspect_result`

Fehlercodes (`SAFETY_*`, `WriteTargetProtectionError.diagnosis_id`) unverändert.

## Entfernte direkte Legacy-Zugriffe

- `from safety.write_guard import …` in `preflight/backup.py`
- `from core.safe_device import validate_write_target` in `backup_engine.py` / `restore_engine.py`

## Verbleibende Legacy-Zugriffe (bewusst)

| Datei | Grund |
|-------|-------|
| `backend/app.py` | Monolith — Router-Extraktion Phase B |
| `backend/core/partition_storage_facade.py` | Phase B.1 Storage |
| `backend/core/backup_target_auto_prepare.py` | Phase B.1 Storage/Mount |
| `backend/inspect/collector.py` | Inspect-Refactor |
| `backend/core/safe_device.py` | Implementierungskern hinter Facade |
| `backend/safety/write_guard.py` | Pure Logik hinter Facade |
| Deploy-Runner | Kein Produktpfad |

## Boundary Guard

Vorher: 3 Facade-Warnungen (`preflight`, `backup_engine`, `restore_engine`).  
Nachher: **0** Safety-Warnungen für diese Dateien.

Migrierte Caller: erneuter direkter Import → `facade_boundary_migrated_caller_blocked` (verschärft, noch kein globaler CI-Fail).

Evidence: `docs/evidence/monolith/BOUNDARY_WARNINGS_*_PHASE_A2_A4.txt`

## Tests

- `test_safety_facade_contracts_v1.py` (erweitert)
- `test_preflight_backup_v1.py`
- `test_backup_recovery_engines.py`
- `test_write_guard_v1.py`

Keine Runtime-Smokes (Runtime-Gate Exit 20, statisch + Unit only).

## Risiken

- Semantik hängt weiterhin an `safe_device`/`write_guard` — Facade ist Durchleitung
- `app.py` nutzt weiterhin `safe_device` direkt — größtes verbleibendes Duplikat
- Kein Verhaltenstest gegen Live-Hardware in diesem Lauf

## Nächster Schritt

**Phase B.1 — Storage Caller Migration:** `backup_target_auto_prepare.py`, `inspect/collector.py`, `partition_storage_facade.py`
