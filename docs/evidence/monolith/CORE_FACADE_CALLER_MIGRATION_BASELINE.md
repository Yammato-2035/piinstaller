# Core Facade Caller Migration — Baseline (vor A.2–A.4)

**HEAD (A.1):** `42fb673`  
**Datum:** Phase A.2–A.4 Start

## Boundary-Warnungen (vor Migration)

| Warnung | Datei |
|---------|-------|
| `facade_boundary_write_guard` | `backend/preflight/backup.py` |
| `facade_boundary_safe_device` | `backend/modules/backup_engine.py` |
| `facade_boundary_safe_device` | `backend/modules/restore_engine.py` |
| `facade_boundary_safe_device` | `backend/app.py` |
| `facade_boundary_write_guard` | `backend/core/partition_storage_facade.py` |
| `facade_boundary_blkid` | `backend/core/backup_target_auto_prepare.py` |

Rohausgabe: `BOUNDARY_WARNINGS_BEFORE_PHASE_A2_A4.txt`

## Geplante Migrationsreihenfolge

1. **A.2** `backend/preflight/backup.py` — `write_guard` → `safety_facade.evaluate_preflight_write_target`
2. **A.3** `backend/modules/backup_engine.py` — `safe_device.validate_write_target` → `safety_facade.validate_write_target`
3. **A.4** `backend/modules/restore_engine.py` — gleiche Engine-Delegation

## Bewusst nicht migriert (dieser Lauf)

| Bereich | Grund |
|---------|-------|
| `backend/app.py` | Monolith-Router-Extraktion Phase B — zu groß, API-Risiko |
| `backend/deploy/runner_*.py` | Kein Produktpfad; Runner Registry fehlt |
| `backend/core/partition_storage_facade.py` | Separater Storage/Safety-Pfad (Phase B.1) |
| `backend/core/backup_target_auto_prepare.py` | Storage-Facade-Migration (Phase B.1) |
| `backend/inspect/collector.py` | Inspect-Refactor gebündelt |

## Safety-Facade-Erweiterung (geplant)

Wrapper ohne neue Logik:

- `evaluate_preflight_write_target` / `validate_preflight_backup_target`
- `validate_write_target` / `validate_restore_target_for_write`
- `normalize_legacy_safety_result`
