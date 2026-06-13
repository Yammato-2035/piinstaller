# Deploy Thin-Orchestrator — Final Plan (D.12)

## Zielbild

`backend/deploy/routes.py` wird zum **dünnen Orchestrator**:

1. Nur `include_router(...)` + wenige Execute-Kernrouten
2. Keine direkten `from deploy.runner_*` (Ziel: 0)
3. Domains über Subrouter (bereits 7/7 extrahiert für plan-only/readonly-Blöcke D.7–D.11)

## Verbleibend in routes.py

### Router-Gruppen (Subrouter bereits extrahiert)

| Router | Status |
|--------|--------|
| registry, risk_gate, evidence, governance, diagnostics, versioning, runtime | extrahiert |

### Verbleibende Domains (inline)

- **rescue** (99) — größter Blocker
- **runner** (47) — Handoff/Execute-Proxies
- **write / real-write / cache** — Execute-Pfade
- **rescue-stick** — Hardware-nah

### Execute-Routen (nicht anfassen in D.12)

- `/execute`, `/write/*`, `/real-write/*`, `/cache/execute`, rescue execute-Proxies

### Risk-Gates (verbleibend)

- `hardware_gate`, `real_write_guard`, `final_confirmation`, runner permission boundary

## Nächste Phase D.13 (Vorschlag)

1. **Rescue-Domain-Router** extrahieren (readonly/plan zuerst)
2. **Runner-Handoff-Block** in `deploy/runner_routes.py`
3. Runner-Import-Count 81 → <40

## Harte Regeln (unverändert)

- Keine Execute-Routen ohne dedizierten Risk-Gate-Review
- Keine API-Shape-Änderungen
