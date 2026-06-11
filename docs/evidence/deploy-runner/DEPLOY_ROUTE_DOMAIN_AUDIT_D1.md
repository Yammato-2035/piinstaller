# Deploy Route Domain Audit (Phase D.1)

**Datum:** 2026-06-10  
**HEAD:** `1b24669` (nach C.6)  
**Modul:** `backend/deploy/routes.py`  
**Modus:** rein statisch — kein Refactoring, keine Runtime-Smokes (Gate Exit 20)

## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Gesamtzeilen | **5041** |
| Gesamtanzahl Routen | **237** |
| GET | **11** |
| POST | **226** |
| PUT | **0** |
| DELETE | **0** |
| PATCH | **0** |
| Direkte Runner-Imports (`from deploy.runner_*`) | **104** |
| Registry-Zugriffe (direkt in routes.py) | **0** (nur via Facade) |
| Risk-Gate-Zugriffe (direkt) | **0** (nur via Facade) |
| Facade-Zugriffe (`runner_api_facade`) | **1 Import-Block**, **20** Handler-Aufrufe |

### Facade-Aufrufe (Detail)

| Funktion | Aufrufe |
|----------|---------|
| `build_plan_only_response` | 9 (C.5+C.6 decoupled) |
| `build_runner_catalog` | 1 |
| `build_runner_catalog_summary` | 1 |
| `build_runner_policy_warnings` | 1 |
| `build_runner_risk_gate_summary` | 1 |
| `list_runner_operator_required` | 1 |
| `list_runner_never_auto` | 1 |
| `list_runner_plan_allowed` | 1 |
| `get_runner_registry_entry` | 1 |
| `get_runner_empty_result` | 1 |
| `get_runner_risk_gate_decision` | 1 |

## Kontext C.1–C.6

Vor D.1 existieren bereits:

- `runner_registry.py` (C.1) — 115 Runner-Metadaten
- `runner_result_contract.py` (C.2)
- `runner_api_facade.py` (C.3/C.5/C.6) — read-only + `build_plan_only_response`
- `runner_risk_gate.py` (C.4) — `allowed_to_execute` immer false
- 9 decoupled POST-Routen (C.5+C.6), 104 verbleibende direkte Imports

## Größter Monolith-Block

`routes.py` bleibt der größte Deploy-Monolith: **237 Routen**, **5041 Zeilen**, dominiert von **Rescue** (84 Routen) und **Evidence** (40 Routen).

## Inventar

Vollständige Route-Liste: `DEPLOY_ROUTE_INVENTORY_D1.csv` (237 Zeilen).

## Methodik

- Route-Erkennung: `@router.(get|post|put|delete|patch)("…")`
- Runner-Zuordnung: Import-Symbol-Nutzung im Handler-Body oder `build_plan_only_response(runner_id)`
- Risk-Level / Execution Policy: `runner_registry` + `evaluate_runner_risk_gate`
- Domain: Pfad-Heuristik + Registry-`category` (siehe `DEPLOY_ROUTE_DOMAIN_MATRIX_D1.md`)

## Phase 0 Gate

| Gate | Ergebnis |
|------|----------|
| Runtime | Exit **20** (release-Profil) |
| Boundary | `review_required` (warn-only) |
| Dirty Tree | ja — fremde Änderungen außerhalb D.1 |
