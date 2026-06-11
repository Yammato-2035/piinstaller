# Deploy routes.py Analysis (Phase C.3)

**Datei:** `backend/deploy/routes.py`  
**HEAD-Basis:** `86676cb`

## Kennzahlen

| Metrik | Wert |
|--------|------|
| Zeilen | **5003** (+ C.3 read-only Block) |
| Router-Deklarationen (`@router.*`) | **~227** |
| Davon `POST` | **226** |
| Davon `GET` | **1** (+ **5** C.3 Runner-GETs) |
| Direkte `from deploy.runner_*` Imports | **112** |

## Route-Gruppen (bestehend)

| Gruppe | Beispiele | C.3 |
|--------|-----------|-----|
| Deploy Kern | `/plan`, `/execute`, `/session` | **nicht angefasst** |
| Cache | `/cache/plan`, `/cache/execute` | **nicht angefasst** |
| Write / Real-Write | `/write/*`, `/real-write/*` | **nicht angefasst** |
| Runner Audit/Sandbox | `/runner/audit/*`, `/runner/sandbox/*` | **nicht angefasst** |
| Runner Install | `/runner/install/*` | **nicht angefasst** |
| Manual Runtime / Laptop | `/runner/manual-runtime/*` | **nicht angefasst** |
| Rescue | `/rescue/*` | **nicht angefasst** |
| **C.3 Runner Facade** | `GET /runners/*` | **neu, read-only** |

## Gefährliche Routen (unverändert, ausgeschlossen)

`POST /execute`, `/write/execute`, `/cache/execute`, `/real-write/*`, Rescue-Build/Execute, Apply-Rewrite — **keine Änderung in C.3**.

## Read-only Kandidaten (C.3 umgesetzt)

| Endpunkt | Funktion |
|----------|----------|
| `GET /api/deploy/runners/catalog` | `build_runner_catalog()` |
| `GET /api/deploy/runners/summary` | `build_runner_catalog_summary()` |
| `GET /api/deploy/runners/policy-warnings` | `build_runner_policy_warnings()` |
| `GET /api/deploy/runners/{runner_id}` | `get_runner_registry_entry()` |
| `GET /api/deploy/runners/{runner_id}/empty-result` | `get_runner_empty_result()` |

## Entlastung routes.py

- **112 direkte Runner-Imports bleiben** (keine Migration in C.3)
- Neue Facade kapselt Registry + Contract **ohne** weitere Runner-Imports
- Vollständige Entlastung → C.5 schrittweise Migration

Rohscan: `deploy_routes_scan_c3.txt`
