> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner API Facade — Quick Reference (KB)

**Phase:** C.3 | **Module:** `runner_api_facade.py`

- alleen-lezen GET under `/api/Deploy/runners/*`
- Uses registry (C.1) + result contract (C.2)
- Nee `runner_*.py` imports, Nee execution
- 112 legacy imports in `routes.py` unchanged

**Volgende step:** C.4 risk gate
