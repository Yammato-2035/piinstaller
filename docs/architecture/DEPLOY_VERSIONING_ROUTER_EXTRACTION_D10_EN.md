# Deploy Versioning Router Extraction (D.10)

**Phase:** D.10 · **Module reuse:** M.1 (`runner_api_facade`, no parallel modules)

## Goal

Extract plan-only versioning/identifier routes from `routes.py` to `routes_versioning.py` — no apply/rewrite/execute.

## Delivery

| File | Role |
|------|------|
| `backend/deploy/routes_versioning.py` | 8 POST plan-only via `build_plan_only_response` |
| `backend/deploy/routes.py` | Orchestrator, −8 handlers, −4 runner import lines |

## Next step

**D.11** — Runtime readonly router
