> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner API Facade — Quick Reference (KB)

**Phase:** C.3 | **Module:** `runner_api_facade.py`

- lecture seule GET under `/api/Déploiement/runners/*`
- Uses registry (C.1) + result contract (C.2)
- Non `runner_*.py` imports, Non execution
- 112 legacy imports in `routes.py` unchanged

**Suivant step:** C.4 risk gate
