# Routes Decoupling D.2–D.6 — KB

| Phase | Modul | Routen |
|-------|-------|--------|
| D.2 | `routes_registry.py` | 5 GET |
| D.3 | `routes_risk_gate.py` | 5 GET |
| D.4 | `routes_evidence.py` | 6 POST |
| D.5 | `routes_governance.py` | 3 POST |
| D.6 | — (Analyse) | Thin-Orchestrator-Ziel |

`routes.py`: 4821 Zeilen, 218 Routen, 103 Imports. Ziel <500 / 0 Imports.

Nächster Schritt: **D.7** Evidence plan-only.

Siehe `DEPLOY_ROUTES_THIN_ORCHESTRATOR.md`.
