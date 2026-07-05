> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_VERSIONING_ROUTER_EXTRACTION_D10_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Versioning Router Extraction (D.10)

**Phase:** D.10 · **Module reuse:** M.1 (`runner_api_facade`, Nee parallel modules)

## Goal

Extract plan-only versioning/identifier routes from `routes.py` to `routes_versioning.py` — Nee apply/rewrite/execute.

## Delivery

| File | Role |
|------|------|
| `Terugend/Deploy/routes_versioning.py` | 8 POST plan-only via `build_plan_only_response` |
| `Terugend/Deploy/routes.py` | Orchestrator, −8 handlers, −4 runner import lines |

## Volgende step

**D.11** — Runtime readonly router
