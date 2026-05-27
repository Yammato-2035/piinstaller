# Dev Dashboard API Test Skip Triage

**Datum:** 2026-05-27  
**HEAD:** `40cde4e`

## Symptom

`PYTHONPATH=backend python3 -m unittest backend.tests.test_dev_dashboard_v1` → **11 skipped** (Klasse `TestDevDashboardApiV1`).

Mit `backend/venv/bin/python3` → **0 skipped**, alle API-Tests **ok**.

## Ursache

| Interpreter | `fastapi` | `TestClient` | `from app import app` |
|---------------|-----------|--------------|------------------------|
| `/usr/bin/python3` (System) | **fehlt** | **fehlt** | **fehlt** |
| `backend/venv/bin/python3` | 0.135.1 | ok | ok |

`test_dev_dashboard_v1.py` setzt `_HAS_APP = False`, wenn der Import am Modulstart scheitert:

```python
@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestDevDashboardApiV1(unittest.TestCase):
```

Das ist **kein** Produktionsfehler — der laufende Dienst nutzt `backend/venv` bzw. `/opt/setuphelfer/backend` mit installierten Abhängigkeiten.

## Empfehlung für CI/Operator

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m unittest backend.tests.test_dev_dashboard_v1 -v
```

## API-Teststatus

| Lauf | passed | skipped | failed |
|------|--------|---------|--------|
| System-`python3` | 23 | **11** | 0 |
| `backend/venv/bin/python3` | **34** | 0 | 0 |

**Bewertung:** API-Teststatus **gelb**, wenn nur System-Python dokumentiert ist; **grün** mit venv-Interpreter.
