# Deploy Versioning Router Extraction (D.10)

**Phase:** D.10 · **Module-Reuse:** M.1 (runner_api_facade, keine parallelen Module)

## Ziel

Plan-only Versioning-/Identifier-Routen aus `routes.py` nach `routes_versioning.py` — ohne Apply/Rewrite/Execute.

## Lieferung

| Datei | Rolle |
|-------|-------|
| `backend/deploy/routes_versioning.py` | 8 POST plan-only via `build_plan_only_response` |
| `backend/deploy/routes.py` | Orchestrator, −8 Handler, −4 Runner-Import-Zeilen |

## Extrahierte Routen

Siehe `docs/evidence/deploy-runner/DEPLOY_VERSIONING_ROUTER_SLICE_D10.md`.

## Nicht extrahiert (bewusst)

- `*-apply`, `controlled-rewrite-apply`
- cleanup-cycle/hotspot (nächste Slices)
- branding-guard (Slice-Limit 8)

## Tests

`backend/tests/test_deploy_routes_versioning_v1.py` — 124 Deploy-Tests grün.

## Nächster Schritt

**D.11** — Runtime Readonly Router
