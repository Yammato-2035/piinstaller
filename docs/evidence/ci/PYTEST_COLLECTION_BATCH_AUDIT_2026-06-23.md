# Pytest Collection Batch Audit — 2026-06-23

**Branch:** main  
**HEAD (vor Fix):** `359a96b`  
**CI-Run (vor Fix):** `28030358055` (failure, Collection stop bei 1/3 Recovery-Importfehlern)

## Collection-Fehler vorher

| Fehlerklasse | Testdatei | Fehlendes Modul/Datei | Ursache | Fix-Strategie |
|---|---|---|---|---|
| falsche Importpfade | `tests/test_recovery_minimal_plan_v1.py` | `recovery.minimal_plan` | `python -m pytest` setzt Repo-Root auf `sys.path[0]`; Legacy-Paket `/recovery/` überschattet `backend/recovery/`. Vorherige `_load()`-Namen (`setuphelfer_recovery_*`) registrierten Submodule nicht unter `recovery.*`; `routes.py` importiert aber `from recovery.minimal_plan import …`. Zusätzlich setzt `import app` in früheren Tests das falsche `recovery`-Paket in `sys.modules`. | `tests/recovery_imports.py`: Backend-Pfad priorisieren, falsches `recovery` aus `sys.modules` entfernen, dann `importlib.import_module`. Drei Recovery-Tests auf Helper umgestellt. |
| falsche Importpfade | `tests/test_recovery_activation_plan_v1.py` | `recovery.activation_plan` | wie oben | wie oben |
| falsche Importpfade | `tests/test_recovery_activation_execute_v1.py` | `recovery.activation_execute` | wie oben | wie oben |

**Vorher (collect-only, `python -m pytest`):** 3498 tests collected, **3 errors**  
**Nachher:** **3530 tests collected, 0 errors**

## Gruppen (vollständige Analyse)

1. **fehlende Python-Packages aus requirements** — keine (jsonschema bereits in `359a96b` behoben)
2. **fehlende interne Module** — keine; `backend/recovery/*.py` existiert und ist versioniert
3. **falsche Importpfade** — **3 Treffer** (alle Recovery-API-Tests mit `routes.py`-Load)
4. **fehlende Testdaten/Evidence-Seeds** — keine Collection-Treffer
5. **Syntax-/Indentation-Fehler** — keine (bereits in `8b23c89` behoben)
6. **Tests erwarten Runtime/Hardware** — keine Collection-Treffer
7. **alte Legacy-Tests ohne gültige Modulstruktur** — keine weiteren Treffer

## Geänderte Dateien (CI-Fix)

- `backend/tests/__init__.py` — Backend-Pfad vor Repo-Root; Schatten-`recovery` bereinigen
- `backend/tests/recovery_imports.py` — neuer Import-Helper für Recovery-Submodule
- `backend/tests/test_recovery_minimal_plan_v1.py`
- `backend/tests/test_recovery_activation_plan_v1.py`
- `backend/tests/test_recovery_activation_execute_v1.py`
- `docs/evidence/ci/PYTEST_COLLECTION_BATCH_AUDIT_2026-06-23.md`

## Dependencies

Keine Änderung an `backend/requirements.txt`.

## Lokale Validierung

```text
python -m pytest --collect-only -q  → 3530 collected, 0 errors
python -m pytest tests/test_recovery_activation_execute_v1.py tests/test_recovery_minimal_plan_v1.py -q  → 23 passed
pip-audit -r backend/requirements.txt  → grün
npm audit --omit=dev --audit-level=high  → grün
```

## Hinweis Root-Cause

Das Legacy-Verzeichnis `recovery/` im Projektroot (Offline-Recovery-Einstieg `recovery/main.py`) kollidiert mit dem API-Paket `backend/recovery/`, sobald CI `python -m pytest` aus `backend/` startet. Ein späterer `import app` in anderen Tests verstärkt die Fehl-Registrierung in `sys.modules`.
