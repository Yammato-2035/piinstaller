# CI Assertion Batch Fix

## Ausgangslage
- **HEAD:** `07437c4`
- **CI Run:** `28037914835` (failure)
- **Primärfehler:** `test_api_consistency_fix9_v1.py::test_backup_list_uses_dedicated_read_validation` — `"diagnosis_id": diagnosis_id` nicht in `app.py`

## Fehlergruppe

| Test | Fehler | Ursache | Entscheidung |
|---|---|---|---|
| `test_backup_list_uses_dedicated_read_validation` | `diagnosis_id`-Literal nur in Handlers | `list_backups` in `core/backup_readonly_handlers.py` ausgelagert; Diagnose-Felder dort vorhanden | Assertion auf `list_fn` (Handlers) statt `app.py` |
| `test_restore_preview_response_exposes_private_tmp_hint` | Private-Tmp-Response-Felder nicht in `app.py` | Restore-Preview-Antwort in `core/backup_execute_handlers.restore_backup` | Helper `_private_tmp_isolation_active` bleibt in `app.py`; Response-Felder in Handler-Block prüfen |

## Fix
- **Geänderte Dateien:** `backend/tests/test_api_consistency_fix9_v1.py`
- **Contract-Entscheidung:** Fix9-Guards bleiben unverändert streng; Prüfziel folgt der B.8/B.9 Handler-Auslagerung (wie `test_backup_list_decouple_fix11_v1.py`).
- **Safety-Auswirkung:** keine — nur Test-Scope-Korrektur, keine API-/Backup-Logik geändert.

## Lokale Checks

| Check | Ergebnis |
|---|---|
| `pytest tests/test_api_consistency_fix9_v1.py` | 4 passed |
| `pytest tests/test_api_consistency_fix9_v1.py tests/test_anti_regression.py tests/test_backup_execute_router_b8_v1.py` | 10 passed |
| `pip-audit` | grün |
| `npm audit --omit=dev --audit-level=high` | grün |

## Ergebnis
- **collection_status:** ok (unverändert)
- **assertion_status:** Fix9-Gruppe lokal grün
- **next_ci_expected:** Fix9 bestanden; nächster möglicher Stopper außerhalb Fix9 (z. B. `test_dev_dashboard_roadmap_registry_v1.py`)
