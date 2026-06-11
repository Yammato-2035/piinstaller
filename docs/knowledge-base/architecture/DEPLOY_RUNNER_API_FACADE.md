# Deploy Runner API Facade — Kurzreferenz (KB)

**Phase:** C.3 | **Modul:** `runner_api_facade.py`

- Read-only GET unter `/api/deploy/runners/*`
- Nutzt Registry (C.1) + Result Contract (C.2)
- Keine `runner_*.py` Imports, keine Ausführung
- 112 Legacy-Imports in `routes.py` unverändert

**Nächster Schritt:** C.4 Risk Gate
