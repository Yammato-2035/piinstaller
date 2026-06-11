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

## D.7 Update (erledigt)

6 weitere plan-only POST-Routen nach `routes_evidence.py` (12 gesamt). `routes.py`: 4671 Zeilen, 99 Imports.

## Zielmetriken

| Metrik | Ist (D.7) | Ziel |
|--------|----------:|-----:|
| `routes.py` Zeilen | 4671 | **< 500** |
| direkte Runner-Imports | 99 | **0** |
| Routen direkt in routes.py | 218 | **0–10** Legacy |
| Subrouter | 4 | **10–14** |
| Execute-Routen ohne Risk-Gate | offen | **0** (nach Execute-Gate) |

## Warum Guard statt Blind-Migration?

D.2–D.5 haben sichere Facade-Routen extrahiert. Weitere Moves ohne Guard riskieren API-Drift und Execute-Leaks. D.6 führt **Messung + Ownership + D.7+-Reihenfolge** ein.

## Subrouter heute

| Modul | Routen |
|-------|--------|
| `routes_registry.py` | 5 GET |
| `routes_risk_gate.py` | 5 GET |
| `routes_evidence.py` | 12 POST |
| `routes_governance.py` | 3 POST |

Siehe `DEPLOY_ROUTE_EXTRACTION_SEQUENCE_D7_PLUS.md`.
