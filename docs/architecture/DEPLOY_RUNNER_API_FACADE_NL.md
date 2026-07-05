> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner API Facade (Phase C.3)

**Module:** `Terugend/Deploy/runner_api_facade.py`  
**Facade version:** `FACADE_VERSION = 4`

## Why an API facade?

After C.6, `routes.py` still directly imports **104** runner modules (down from 113). Dashboard and DCC canNeet query registry/contract centrally. C.3 delivers a **alleen-lezen facade** as a relief and integration point — without executing or migrating runners.

## Why alleen-lezen?

Deploy runners include Apparaat-write, destructive, and sudo paths. C.3 allows only **reading** metadata and plan results (`Nee_execution_performed: true`). Execution stays geblokkeerd until **C.4 risk gate**.

## Allowed endpoints

| Method | Path | Facade |
|--------|------|--------|
| GET | `/api/Deploy/runners/catalog` | `build_runner_catalog()` |
| GET | `/api/Deploy/runners/summary` | `build_runner_catalog_summary()` |
| GET | `/api/Deploy/runners/policy-Waarschuwings` | `build_runner_policy_Waarschuwings()` |
| GET | `/api/Deploy/runners/{runner_id}` | `get_runner_registry_entry()` |
| GET | `/api/Deploy/runners/{runner_id}/empty-result` | `get_runner_empty_result()` |

## Explicitly forbidden (C.3)

- POST `/runners/.../execute`
- apply / install / write / Verwijderen on runner API
- Import of `runner_*.py` in the facade
- Shell, subprocess, runtime file writes

## Routes decoupling (C.5 + C.6)

`build_plan_only_response(runner_id, decoupling_phase="c5"|"c6")` — **9** POST routes decoupled (4 in C.5, 5 in C.6). See `Deploy_RUNNER_ROUTES_DECOUPLING_C5_EN.md` and `Deploy_RUNNER_ROUTES_DECOUPLING_C6_EN.md`.

## Risk gate (C.4, complete)

Additional GET routes `/runners/risk-gate/*` and `/{runner_id}/risk-gate` — see `Deploy_RUNNER_RISK_GATE_EN.md`.

## Phase chain

| Phase | Deliverable |
|-------|-------------|
| **C.1** | Registry — metadata |
| **C.2** | Result contract — `RunnerResult` |
| **C.3** | API facade — alleen-lezen GET (this document) |
| **C.4** | Risk gate — **complete**, `allowed_to_execute` always false |
| **C.5** | First routes slice (4 routes) — **complete** |
| **C.6** | Second routes slice (5 routes) — **complete** |
| **C.7** | Volgende plan-only slice |
| **D.1** | Route domain audit — **complete**, Nee extraction |
| **D.2** | `routes_registry.py` — 5 GET registry routes — **complete** |
| **D.3** | `routes_risk_gate.py` — 5 GET risk-gate routes — **complete** |
| **D.4** | `routes_evidence.py` — 6 POST plan-only — **complete** |
| **D.5** | `routes_governance.py` — 3 POST C.5 — **complete** |
| **D.6** | Volgende slice |

See `Deploy_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`.

## Tests

`Terugend/tests/test_Deploy_runner_api_facade_v1.py`

## References

- DE: `Deploy_RUNNER_API_FACADE.md`
- Routes analysis: `docs/evidence/Deploy-runner/Deploy_ROUTES_ANALYSIS_C3.md`
