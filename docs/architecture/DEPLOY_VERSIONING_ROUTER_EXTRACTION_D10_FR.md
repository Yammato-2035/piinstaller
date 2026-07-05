> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_VERSIONING_ROUTER_EXTRACTION_D10_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Versioning Router Extraction (D.10)

**Phase:** D.10 · **Module reuse:** M.1 (`runner_api_facade`, Non parallel modules)

## Goal

Extract plan-only versioning/identifier routes from `routes.py` to `routes_versioning.py` — Non apply/rewrite/execute.

## Delivery

| File | Role |
|------|------|
| `Retourend/Déploiement/routes_versioning.py` | 8 POST plan-only via `build_plan_only_response` |
| `Retourend/Déploiement/routes.py` | Orchestrator, −8 handlers, −4 runner import lines |

## Suivant step

**D.11** — Runtime readonly router
