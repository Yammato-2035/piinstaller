# Monolith-Repository-Inventar

**Datum:** 2026-06-16  
**Quelle:** `docs/evidence/monolith/repo_file_inventory.txt`, `largest_files.txt`, `FULL_REPOSITORY_STRUCTURE_AUDIT.md`  
**Scope:** Statische Dateizählung; venv/`.venv-ci`/`node_modules` in `largest_files.txt` bei Größenranking ausgeblendet

## Gesamtüberblick

| Kennzahl | Wert |
|----------|------|
| Dateien im Inventar | **5.295** |
| Größte Projektdatei (ohne venv) | `backend/app.py` — **15.142** Zeilen |
| Zweitgrößte Projektdatei | `frontend/src/pages/BackupRestore.tsx` — **3.992** Zeilen |
| Drittgrößte Projektdatei | `backend/deploy/routes.py` — **3.704** Zeilen |

Das Inventar listet Pfade relativ zum Repo-Root. Es enthält Build-Artefakte unter `backend/cache/`, generierte Tauri-Schemas und Evidence-Dateien unter `docs/evidence/`.

## Verteilung nach Top-Level-Bereichen

| Bereich | Dateien (Inventar) | Charakter |
|---------|-------------------|-----------|
| `docs/` | 3.601 | Dokumentation, FAQ, Evidence-Akkumulation |
| `backend/` | 961 | API, Core, Deploy-Runner, Rescue, Tests (Teilmenge) |
| `frontend/` | 437 | React/Vite UI, Locales, `src-tauri/` |
| `scripts/` | 260 | Shell-Gates, Deploy, Rescue-Build |
| `packaging/` | 24 | deb/rpm/Installer-Hilfen |
| `debian/` | 12 | Paket-Metadaten |

**Hinweis `src-tauri`:** Es gibt **kein** Top-Level-Verzeichnis `src-tauri/` im Repo-Root. Tauri liegt unter **`frontend/src-tauri/`** (14 Quell-/Konfigurationsdateien im Inventar, u. a. `src/lib.rs`, `src/main.rs`, `src/dev_dashboard_standalone.rs`). Die Desktop-Shell ist damit an das Frontend gebündelt, nicht als eigenständiger Root-Cluster.

## Schlüsselbereiche (fachlich)

### `backend/`

- **`app.py`** (15.142 Z.) — FastAPI-Hauptanwendung mit ~162 `@app`-Routen; Legacy-God-Object neben `app_bootstrap/` und `api/routes/`.
- **`deploy/`** — `routes.py` (3.704 Z., ~165 `@router`-Routen) plus ~115 `runner_*.py`-Dateien; Deploy-/DCC-Orchestrierung.
- **`core/`** — geteilte Domänenlogik (Storage, Safety, Manifest, Dev-Dashboard, Rescue).
- **`api/routes/`** — schrittweise extrahierte schlanke Router (12 Dateien).
- **`modules/`** — ältere Modul-Schicht (`control_center.py`, `storage_detection.py`, `backup_verify.py`).
- **`tests/`** — breite pytest-Spiegelung (nicht vollständig im Inventar-Pfadpräfix `backend/` enthalten, je nach Scan-Regel).

### `frontend/`

- **`src/pages/`** — UI-Monolithen (`BackupRestore.tsx` 3.992 Z., `ControlCenter.tsx` 2.681 Z., `InspectRun.tsx` 2.385 Z.).
- **`src/components/`** — inkl. `dev-dashboard/*` (~4.000+ Z. DCC-UI).
- **`src/api/`** — dünne API-Wrapper; Zentrale in `api.ts` (244 Z.).
- **`src/viewmodels/`** — Status-Mapping (`statusViewModel.ts`, 510 Z.).
- **`src/locales/`** — `de.json` / `en.json` je **3.379** Zeilen (domänenübergreifende i18n-Monolithen).

### `scripts/`

- 260 Dateien; größte Einzeldatei `check-module-boundaries.sh` (1.976 Z.).
- Cluster: Runtime-Gates (`check-runtime-deploy-gate.sh`, `check-backend-version-gate.sh`), Rescue-Live-Build, `deploy-to-opt.sh`, `release-service.sh`.

## Größte Projektdateien (venv gefiltert)

Aus `largest_files.txt`, nur Repository-eigene Pfade:

| Rang | Datei | Zeilen |
|------|-------|--------|
| 1 | `backend/app.py` | 15.142 |
| 2 | `frontend/src/pages/BackupRestore.tsx` | 3.992 |
| 3 | `backend/deploy/routes.py` | 3.704 |
| 4 | `frontend/src/pages/ControlCenter.tsx` | 2.681 |
| 5 | `frontend/src/pages/InspectRun.tsx` | 2.385 |
| 6 | `frontend/src/pages/Dashboard.tsx` | 2.291 |
| 7 | `frontend/src/pages/Documentation.tsx` | 2.055 |
| 8 | `backend/modules/control_center.py` | 1.990 |
| 9 | `scripts/check-module-boundaries.sh` | 1.976 |
| 10 | `backend/tools/backup_runner.py` | 1.583 |
| 11 | `backend/core/rescue_fat32_esp_usb_writer.py` | 1.475 |
| 12 | `backend/core/dev_dashboard.py` | 1.217 |
| 13 | `backend/core/safe_device.py` | 993 |
| 14 | `backend/core/dev_dashboard_cockpit.py` | 731 |
| 15 | `backend/core/storage_facade.py` | 623 |

## Strukturelle Beobachtungen

1. **Zwei API-Monolithen:** `app.py` und `deploy/routes.py` zusammen >18.800 Zeilen und >320 deklarierte HTTP-Endpunkte.
2. **Page-Monolithen im Frontend:** Fünf Pages >2.000 Zeilen; Backup/Restore und Control Center dominieren.
3. **Dokumentationsmasse:** `docs/` ist mit 68 % der Inventardateien der größte Bereich — inkl. `docs/evidence/` als operatives Wissensarchiv.
4. **Tauri minimal:** Rust-Quellcode ~362 Zeilen (`lib.rs`, `main.rs`, `dev_dashboard_standalone.rs`); Fokus auf Cockpit-Fenster und Dev-Server-Anbindung, keine schwere Backend-Kopplung in Rust.
5. **Migration begonnen:** `app_bootstrap/` (Router-/Middleware-Registry), `api/routes/*`, Core-Facades (`storage_facade`, `safety_facade`, `dcc_status_facade`) — Kernrouten und Legacy-Imports in `app.py` bleiben.

## Referenzdateien (Evidence-Basis)

- `docs/evidence/monolith/repo_file_inventory.txt` — vollständige Pfadliste (5.295 Einträge)
- `docs/evidence/monolith/largest_files.txt` — Zeilenranking (enthält venv-Einträge)
- `docs/evidence/monolith/python_imports.tsv` — Importgraph Backend
- `docs/evidence/monolith/frontend_imports.txt` — Importgraph Frontend
- `docs/evidence/monolith/FULL_REPOSITORY_STRUCTURE_AUDIT.md` — vertiefender Strukturbericht
