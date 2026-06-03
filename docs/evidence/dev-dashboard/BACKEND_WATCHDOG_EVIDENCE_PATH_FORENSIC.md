# Backend Watchdog Evidence Path — Forensic

**Datum:** 2026-06-03

## Befund

| Schreibquelle | Zielpfad |
|---------------|----------|
| Workspace-Skript (`BASH_SOURCE`) | `/home/volker/piinstaller/docs/evidence/dev-dashboard/` |
| `/opt`-Skript (Repo-Root aus Skriptpfad) | `/opt/setuphelfer/docs/evidence/dev-dashboard/` |
| `/opt`-Skript mit `SETUPHELFER_REPO_ROOT=/opt/setuphelfer` | `/opt/setuphelfer/docs/evidence/dev-dashboard/` |

**Datei in `/opt` existierte**, aber:

- Modus **600**, Owner **gabriel:setuphelfer**
- Backend-Dienst läuft als User **setuphelfer** → **kein Leserecht** (nicht Path-Mismatch allein)

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Mismatch bestätigt | **yes** (Lesbarkeit + Loader ohne `searched_paths`) |
| **Klassifikation** | **`permission_denied`** + **`loader_search_gap`** |

Log: `backend_watchdog_path_after_latest.log`
