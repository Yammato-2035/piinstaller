# Deploy Registry Router Extraction (Phase D.2)

**Datum:** 2026-06-10  
**HEAD vorher:** `9d10f08`  
**Modus:** Router-Extraktion, keine Runner-Ausführung

## Extrahierte Routen

| Zeilen (alt routes.py) | Route | Facade-Funktion |
|------------------------|-------|-----------------|
| 4994–4996 | `GET /runners/catalog` | `build_runner_catalog()` |
| 4999–5001 | `GET /runners/summary` | `build_runner_catalog_summary()` |
| 5004–5006 | `GET /runners/policy-warnings` | `build_runner_policy_warnings()` |
| 5029–5031 | `GET /runners/{runner_id}` | `get_runner_registry_entry()` |
| 5034–5036 | `GET /runners/{runner_id}/empty-result` | `get_runner_empty_result()` |

**Öffentliche Pfade (unverändert):** `/api/deploy/runners/*` (Parent-Prefix `/api/deploy` + Subrouter `/runners`)

## Imports

| Modul | Imports |
|-------|---------|
| `routes_registry.py` | nur `deploy.runner_api_facade` |
| `routes.py` (entfernt) | `build_runner_catalog`, `build_runner_catalog_summary`, `build_runner_policy_warnings`, `get_runner_empty_result`, `get_runner_registry_entry` |

**Keine** `runner_*.py`-Imports in `routes_registry.py`.

## Response-Semantik

Stabil — 1:1 Facade-Delegation, identische Handler-Logik.

## Risk-Gate-Routen

Verbleiben in `routes.py` (Zeilen ~5009–5041): `/runners/risk-gate/*`, `/runners/{runner_id}/risk-gate`

## Einbindung

```python
from deploy.routes_registry import router as deploy_registry_router
router.include_router(deploy_registry_router)
```

Route-Reihenfolge: Registry-Subrouter vor Risk-Gate-Routen; `{runner_id}/empty-result` vor `{runner_id}` im Subrouter.
