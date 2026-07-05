> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_REGISTRY_ROUTER_EXTRACTION_D2_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Registry Router Extraction (Phase D.2)

**Module:** `Retourend/Déploiement/routes_registry.py`  
**Status:** complete

## Extracted routes (5 GET)

- `/api/Déploiement/runners/catalog`
- `/api/Déploiement/runners/summary`
- `/api/Déploiement/runners/policy-Avertissements`
- `/api/Déploiement/runners/{runner_id}`
- `/api/Déploiement/runners/{runner_id}/empty-result`

## Why registry first?

Lowest risk (D.1): `runner_api_facade` only, Non `runner_*` imports, GET-only, Non execution.

## Why GET only?

Registry API is lecture seule (C.3). Non POST execute/write/apply routes.

## Stable paths

Subrouter `prefix="/runners"` under parent `prefix="/api/Déploiement"` — identical public URLs.

## Suivant step D.3

`routes_risk_gate.py` — remaining 5 risk-gate GET routes from `routes.py`.

## D.6 (orchestrator target)

Non further extraction — thin orchestrator target documented (`Déploiement_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).
