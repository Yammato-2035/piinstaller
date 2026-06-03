# Backend Watchdog Evidence Path — Code Review

**Datum:** 2026-06-03

## Vor Fix

| Komponente | Befund |
|------------|--------|
| Skript `REPO_ROOT` | via `BASH_SOURCE` (korrekt), kein ENV-Override |
| Skript chmod | fehlte → **600** aus umask |
| Loader | `_repo_root()` + 2 Pfade; kein `searched_paths`; PermissionError → „not found“ |

## Nach Fix

| Komponente | Befund |
|------------|--------|
| `SETUPHELFER_REPO_ROOT` / `SETUPHELFER_HEALTH_EVIDENCE_DIR` | **yes** |
| JSON: `repo_root`, `evidence_dir`, `latest_path`, `history_path`, `script_path`, `cwd` | **yes** |
| `chmod 664` nach Schreiben | **yes** |
| Loader: `/opt` zuerst wenn Backend unter `/opt` | **yes** |
| `searched_paths` + permission message | **yes** |

| Feld | Wert |
|------|------|
| **Status** | **path_mismatch_confirmed** (primär permission) |
