# Deploy Registry Router Extraction (Phase D.2)

**Modul:** `backend/deploy/routes_registry.py`  
**Status:** erledigt

## Extrahierte Routen (5 GET)

- `/api/deploy/runners/catalog`
- `/api/deploy/runners/summary`
- `/api/deploy/runners/policy-warnings`
- `/api/deploy/runners/{runner_id}`
- `/api/deploy/runners/{runner_id}/empty-result`

## Warum Registry zuerst?

Niedrigstes Risiko (D.1): nur `runner_api_facade`, keine `runner_*`-Imports, GET-only, keine Ausführung.

## Warum nur GET?

Registry-API ist read-only (C.3). Keine POST-Execute-, Write- oder Apply-Routen.

## Pfade stabil

Subrouter `prefix="/runners"` unter Parent `prefix="/api/deploy"` — identische öffentliche URLs.

## Nächster Schritt D.3

`routes_risk_gate.py` — 5 verbleibende Risk-Gate-GET-Routen aus `routes.py`.
