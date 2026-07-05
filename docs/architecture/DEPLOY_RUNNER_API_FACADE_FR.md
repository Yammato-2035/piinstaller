> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner API Facade (Phase C.3)

**Module:** `Retourend/Déploiement/runner_api_facade.py`  
**Facade version:** `FACADE_VERSION = 4`

## Why an API facade?

After C.6, `routes.py` still directly imports **104** runner modules (down from 113). Dashboard and DCC canNont query registry/contract centrally. C.3 delivers a **lecture seule facade** as a relief and integration point — without executing or migrating runners.

## Why lecture seule?

Déploiement runners include Périphérique-write, destructive, and sudo paths. C.3 allows only **reading** metadata and plan results (`Non_execution_performed: true`). Execution stays bloqué until **C.4 risk gate**.

## Allowed endpoints

| Method | Path | Facade |
|--------|------|--------|
| GET | `/api/Déploiement/runners/catalog` | `build_runner_catalog()` |
| GET | `/api/Déploiement/runners/summary` | `build_runner_catalog_summary()` |
| GET | `/api/Déploiement/runners/policy-Avertissements` | `build_runner_policy_Avertissements()` |
| GET | `/api/Déploiement/runners/{runner_id}` | `get_runner_registry_entry()` |
| GET | `/api/Déploiement/runners/{runner_id}/empty-result` | `get_runner_empty_result()` |

## Explicitly forbidden (C.3)

- POST `/runners/.../execute`
- apply / install / write / Supprimer on runner API
- Import of `runner_*.py` in the facade
- Shell, subprocess, runtime file writes

## Routes decoupling (C.5 + C.6)

`build_plan_only_response(runner_id, decoupling_phase="c5"|"c6")` — **9** POST routes decoupled (4 in C.5, 5 in C.6). See `Déploiement_RUNNER_ROUTES_DECOUPLING_C5_EN.md` and `Déploiement_RUNNER_ROUTES_DECOUPLING_C6_EN.md`.

## Risk gate (C.4, complete)

Additional GET routes `/runners/risk-gate/*` and `/{runner_id}/risk-gate` — see `Déploiement_RUNNER_RISK_GATE_EN.md`.

## Phase chain

| Phase | Deliverable |
|-------|-------------|
| **C.1** | Registry — metadata |
| **C.2** | Result contract — `RunnerResult` |
| **C.3** | API facade — lecture seule GET (this document) |
| **C.4** | Risk gate — **complete**, `allowed_to_execute` always false |
| **C.5** | First routes slice (4 routes) — **complete** |
| **C.6** | Second routes slice (5 routes) — **complete** |
| **C.7** | Suivant plan-only slice |
| **D.1** | Route domain audit — **complete**, Non extraction |
| **D.2** | `routes_registry.py` — 5 GET registry routes — **complete** |
| **D.3** | `routes_risk_gate.py` — 5 GET risk-gate routes — **complete** |
| **D.4** | `routes_evidence.py` — 6 POST plan-only — **complete** |
| **D.5** | `routes_governance.py` — 3 POST C.5 — **complete** |
| **D.6** | Suivant slice |

See `Déploiement_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`.

## Tests

`Retourend/tests/test_Déploiement_runner_api_facade_v1.py`

## References

- DE: `Déploiement_RUNNER_API_FACADE.md`
- Routes analysis: `docs/evidence/Déploiement-runner/Déploiement_ROUTES_ANALYSIS_C3.md`
