# Routes Decoupling D.2–D.6 — KB

| Phase | Module | Routes |
|-------|--------|--------|
| D.2 | `routes_registry.py` | 5 GET |
| D.3 | `routes_risk_gate.py` | 5 GET |
| D.4 | `routes_evidence.py` | 6 POST |
| D.5 | `routes_governance.py` | 3 POST |
| D.6 | — (analysis) | thin orchestrator target |

`routes.py`: 4821 lines, 218 routes, 103 imports. Target <500 / 0 imports.

Next step: **D.7** evidence plan-only.

See `DEPLOY_ROUTES_THIN_ORCHESTRATOR_EN.md`.
