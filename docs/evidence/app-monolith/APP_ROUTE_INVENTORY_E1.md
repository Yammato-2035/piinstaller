# APP Route Inventory — Phase E.1

**Baseline HEAD:** `5a8a54c` (vor Extraktion)  
**Quelle:** `backend/app.py` (statischer Scan)  
**Gesamt:** 213 `@app.*` Routen

## Domänenverteilung

| Domäne | Anzahl |
|--------|--------|
| unknown | 106 |
| dev_dashboard | 41 |
| backup | 32 |
| runtime | 22 |
| frontend_support | 7 |
| diagnostics | 2 |
| health | 2 |
| version | 1 |

## E.1-Kandidaten (`candidate=yes_e1`)

| Zeile | Methode | Pfad | Funktion |
|-------|---------|------|----------|
| 2611 | GET | `/api/init/status` | `init_status` |
| 2863 | GET | `/api/logs/path` | `logs_path` |
| 4081 | GET | `/api/version` | `get_version` |
| 6805 | GET | `/health` | `health_check` |

## CSV

Vollständiges Inventar: [APP_ROUTE_INVENTORY_E1.csv](./APP_ROUTE_INVENTORY_E1.csv)

Pflichtfelder: line, method, path, function_name, domain, risk, uses_storage, uses_safety, uses_mount, uses_subprocess, uses_runtime_write, candidate.
