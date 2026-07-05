> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner API Fassade — Quick Reference (KB)

**Phase:** C.3 | **Module:** `runner_api_facade.py`

- Read-only GET under `/api/deploy/runners/*`
- Uses registry (C.1) + result contract (C.2)
- No `runner_*.py` imports, no execution
- 112 legacy imports in `routes.py` unchanged

**Next step:** C.4 risk gate
