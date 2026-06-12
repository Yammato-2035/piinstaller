# Deploy Routes Thin Orchestrator — Zielbild (Phase D.6)

**Status:** Zieldefinition — **kein Refactoring in D.6**

## Ist-Zustand (nach D.2–D.5)

`backend/deploy/routes.py` ist **Orchestrator + Legacy-Monolith**:

- 4× `include_router(...)` für Registry, Risk Gate, Evidence, Governance
- 4821 Zeilen, 218 direkte Routen, 103 Runner-Imports
- Execute/Rescue/Write-Pfade verbleiben hier

## Zielbild

`routes.py` soll langfristig **nur**:

1. `APIRouter(prefix="/api/deploy")` erzeugen
2. Subrouter importieren und `include_router` aufrufen
3. Wenige Legacy-Kompatibilitätsanker (0–10 Routen) optional
4. **Keine** direkten `runner_*.py`-Imports
5. **Keine** Businesslogik / Runner-Ausführung

## D.9 Update (no_safe_slice)

Keine Notification-Routen in Deploy-API — `routes_notifications.py` nicht angelegt.

## D.10 Update (versioning)

`routes_versioning.py` — 8 plan-only Routen. `routes.py`: **4324** Zeilen, **89** Runner-Imports.

## D.11 Update (runtime)

`routes_runtime.py` — 8 read-only/status Routen. `routes.py`: **4120** Zeilen, **81** Runner-Imports.

## Zielmetriken

| Metrik | Ist (D.11) | Ziel |
|--------|----------:|-----:|
| `routes.py` Zeilen | 4120 | **< 500** |
| direkte Runner-Imports | 81 | **0** |
| Routen direkt in routes.py | 218 | **0–10** Legacy |
| Subrouter | 7 | **10–14** |
| Execute-Routen ohne Risk-Gate | offen | **0** (nach Execute-Gate) |

## Warum Guard statt Blind-Migration?

D.2–D.5 haben sichere Facade-Routen extrahiert. Weitere Moves ohne Guard riskieren API-Drift und Execute-Leaks. D.6 führt **Messung + Ownership + D.7+-Reihenfolge** ein.

## Subrouter heute

| Modul | Routen |
|-------|--------|
| `routes_registry.py` | 5 GET |
| `routes_risk_gate.py` | 5 GET |
| `routes_evidence.py` | 12 POST |
| `routes_diagnostics.py` | 6 POST |
| `routes_versioning.py` | 8 POST (D.10) |
| `routes_runtime.py` | 8 POST (D.11) |
| `routes_notifications.py` | — (D.9 übersprungen) |
| `routes_governance.py` | 3 POST |

Siehe `DEPLOY_ROUTE_EXTRACTION_SEQUENCE_D7_PLUS.md`.
