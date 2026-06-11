# Deploy Runner API Facade — Quick Reference (KB)

**Phase:** C.3 | **Module:** `runner_api_facade.py`

- Read-only GET under `/api/deploy/runners/*`
- Uses registry (C.1) + result contract (C.2)
- No `runner_*.py` imports, no execution
- 112 legacy imports in `routes.py` unchanged

**Next step:** C.4 risk gate
