# Devserver Agent ISO Report Fix — Repo Module Review

**Status:** `module_path_confirmed`

| Feld | Wert |
|------|------|
| Modulpfad | `backend/devserver_agent/` (Bundle: `/opt/setuphelfer-rescue/backend/devserver_agent/`) |
| Python-Modulname | `devserver_agent` (interne Imports) |
| Korrekter Aufruf | `PYTHONPATH=/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue` + `python3 -m devserver_agent.cli` |
| Fehler im alten ISO | `PYTHONPATH=/opt/setuphelfer-rescue` + `-m backend.devserver_agent.cli` → `ModuleNotFoundError` |
| Top-level `devserver_agent` im Repo | **yes** (unter `backend/`) |
| `backend.devserver_agent` | **yes** (mit dual PYTHONPATH) |

## Entscheidung

**Modulaufruf + PYTHONPATH korrigieren** (kein Top-Level-Shim nötig).

Workspace-Importtests: `IMPORT_OK devserver_agent`, `IMPORT_OK devserver_agent.cli`.

Artefakte: `devserver_agent_iso_report_fix_repo_files_latest.log`, `devserver_agent_iso_report_fix_import_tests_latest.log`
