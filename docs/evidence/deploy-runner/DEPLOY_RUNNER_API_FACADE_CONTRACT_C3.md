# Deploy Runner API Facade Contract (Phase C.3)

**Modul:** `backend/deploy/runner_api_facade.py`  
**Facade-Version:** `FACADE_VERSION = 1`

## Erlaubte Semantik

| Typ | Erlaubt |
|-----|---------|
| HTTP-Methoden (neu) | **GET only** |
| Facade-Funktionen | list, get, catalog, summary, validate (in-process) |
| Datenquelle | `runner_registry.py`, `runner_result_contract.py` |
| Ausführung | **keine** (`no_execution_performed: true`) |

## Verbotene Semantik

| Typ | Verboten |
|-----|----------|
| HTTP | POST/PUT/PATCH/DELETE auf `/runners/*` |
| Pfade | `execute`, `apply`, `install`, `write`, `delete` |
| Imports | `deploy.runner_*` (außer registry/contract) |
| Runtime | Shell, subprocess, Dateischreiben unter `/opt` |

## Response-Envelope

```json
{
  "status": "ok|review_required|blocked",
  "code": "RUNNER_CATALOG",
  "data": {},
  "warnings": [],
  "errors": []
}
```

## OpenAPI-Auswirkung

- **5 neue GET-Routen** unter `/api/deploy/runners/`
- Keine Request-Bodies
- Responses enthalten Registry-Metadaten und/oder `RunnerResult`-Dicts
- Keine Breaking Changes an bestehenden Routen

## Statische Prüfung (Gate 20)

- Keine Runtime-Smokes gegen Port 8000
- Unit-Tests + `py_compile` + Boundary warn-only
