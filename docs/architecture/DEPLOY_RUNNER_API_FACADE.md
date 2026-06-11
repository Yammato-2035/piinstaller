# Deploy Runner API Facade (Phase C.3)

**Modul:** `backend/deploy/runner_api_facade.py`  
**Facade-Version:** `FACADE_VERSION = 4`

## Warum API Facade?

`routes.py` importiert nach C.6 noch **104** Runner-Module direkt (von ursprünglich 113). Dashboard und DCC können Registry/Contract nicht zentral abfragen. C.3 liefert eine **read-only Facade** als Entlastungs- und Integrationspunkt — ohne Runner auszuführen oder zu migrieren.

## Warum read-only?

Deploy-Runner umfassen device-write, destructive und sudo-Pfade. C.3 erlaubt nur **Lesen** von Metadaten und Plan-Results (`no_execution_performed: true`). Ausführung bleibt gesperrt bis **C.4 Risk Gate**.

## Erlaubte Endpunkte

| Methode | Pfad | Facade |
|---------|------|--------|
| GET | `/api/deploy/runners/catalog` | `build_runner_catalog()` |
| GET | `/api/deploy/runners/summary` | `build_runner_catalog_summary()` |
| GET | `/api/deploy/runners/policy-warnings` | `build_runner_policy_warnings()` |
| GET | `/api/deploy/runners/{runner_id}` | `get_runner_registry_entry()` |
| GET | `/api/deploy/runners/{runner_id}/empty-result` | `get_runner_empty_result()` |

## Ausdrücklich verboten (C.3)

- POST `/runners/.../execute`
- apply / install / write / delete auf Runner-API
- Import von `runner_*.py` in der Facade
- Shell, subprocess, Runtime-Schreibzugriffe

## Routes Decoupling (C.5 + C.6)

`build_plan_only_response(runner_id, decoupling_phase="c5"|"c6")` — **9** POST-Routen decoupled (4 in C.5, 5 in C.6). Siehe `DEPLOY_RUNNER_ROUTES_DECOUPLING_C5.md` und `DEPLOY_RUNNER_ROUTES_DECOUPLING_C6.md`.

## Risk Gate (C.4, erledigt)

Zusätzliche GET-Routen `/runners/risk-gate/*` und `/{runner_id}/risk-gate` — siehe `DEPLOY_RUNNER_RISK_GATE.md`.

## Phasen-Kette

| Phase | Lieferung |
|-------|-----------|
| **C.1** | Registry — Metadaten |
| **C.2** | Result Contract — `RunnerResult` |
| **C.3** | API Facade — read-only GET (dieses Dokument) |
| **C.4** | Risk Gate — **erledigt**, `allowed_to_execute` immer false |
| **C.5** | Erster Routes-Slice (4 Routen) — **erledigt** |
| **C.6** | Zweiter Routes-Slice (5 Routen) — **erledigt** |
| **C.7** | Nächster plan-only Slice |
| **D.1** | Route-Domain-Audit — **erledigt**, keine Extraktion |
| **D.2** | `routes_registry.py` — 5 GET Registry-Routen — **erledigt** |
| **D.3** | `routes_risk_gate.py` — 5 GET Risk-Gate-Routen — **erledigt** |
| **D.4** | `routes_evidence.py` — 6 POST plan-only — **erledigt** |
| **D.5** | `routes_governance.py` — 3 POST C.5 — **erledigt** |
| **D.6** | weiterer Slice |

Siehe `DEPLOY_ROUTE_TARGET_ARCHITECTURE_D1.md`.

## Tests

`backend/tests/test_deploy_runner_api_facade_v1.py`

## Verweise

- EN: `DEPLOY_RUNNER_API_FACADE_EN.md`
- Routes-Analyse: `docs/evidence/deploy-runner/DEPLOY_ROUTES_ANALYSIS_C3.md`
