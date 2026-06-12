# DCC / Deploy Core Coupling — Phase F.3

**HEAD:** `8bb910c`

## Kopplungsmatrix

| Quelle | Ziel | Mechanismus | Akzeptabel? | Empfehlung |
|--------|------|-------------|-------------|------------|
| `core/deploy_job_state.py` | `build_dashboard_status` | `_runtime_gate_from_dashboard` | **teilweise** | Facade-Hook `build_dashboard_status_body` |
| `core/deploy_job_state.py` | `dev_dashboard._compute_deploy_drift` | Drift-Slice | **ja** | Core-intern, kein HTTP |
| `core/dev_control_center_summary.py` | `load_roadmap_registry_bundle` | `build_roadmap_section` | **ja** | Core-intern; HTTP über Facade (F.2) |
| `core/dev_control_center_summary.py` | `build_evidence_index` | Summary-Evidence | **ja** | Core-intern |
| `backend/deploy/*` | `dev_dashboard` | nur Runner-Registry-Klassifikation | **ja** | keine direkte DCC-Aggregation |
| `backend/deploy/routes.py` | `runner_api_facade` | plan-only | **ja** | kanonisch |
| `app.py` DCC GETs | `dcc_status_facade` | F.2 migriert | **ja** | kanonisch |

## Deploy → DCC (kritisch)

`deploy_job_state._runtime_gate_from_dashboard`:

- Importiert `build_dashboard_status` **direkt** (nicht Facade).
- Liest `runtime_gate`, `deploy_drift` aus Dashboard-Body.
- Exit-Codes 10–20 für Deploy-Gates.

**Risiko:** Deploy und HTTP-DCC teilen dieselbe Low-Level-Aggregation — Änderungen an `build_dashboard_status` betreffen beide.

**Empfehlung F.4+:** `build_dashboard_status_body(frontend_runtime_source="build")` aus Facade; optional später **System Status Facade** für Runtime-Gate.

## DCC → Deploy

- Project Overview (`build_dcc_project_overview_body`) liest `build_deploy_job_state` — **akzeptabel** (Overview aggregiert Deploy-Status read-only).
- Kein Deploy-Runner-Execute aus DCC-Facade.

## Runner-Facades

| Facade | Nutzung in Deploy-Routen |
|--------|--------------------------|
| `runner_registry` | ja (Metadaten) |
| `runner_api_facade` | ja (plan-only) |
| `runner_risk_gate` | ja (Policy) |

**Keine parallele Runner-Liste in DCC-Modulen.**
