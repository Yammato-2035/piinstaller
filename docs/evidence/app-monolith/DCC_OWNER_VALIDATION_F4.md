# DCC Owner Validation — Phase F.4

**HEAD:** nach F.4 Delegation

| Datei | Funktion | Owner | Erlaubt | Migration offen |
|-------|----------|-------|---------|-----------------|
| `core/dcc_status_facade.py` | alle API-Helper | Facade | `allowed_canonical` | nein |
| `core/dev_dashboard.py` | `build_dashboard_status`, `build_evidence_index` | Core Owner | `allowed_canonical` | nein |
| `core/deploy_job_state.py` | `build_dashboard_status` | Deploy Gate | `allowed_internal` | F.5 Facade-Hook |
| `core/dev_dashboard_roadmap.py` | `load_roadmap_registry_bundle` | Roadmap Owner | `allowed_canonical` | nein |
| `api/routes/dev_dashboard_roadmap.py` | Registry-Slices | Subrouter | `allowed_internal` | nein |
| `api/routes/dev_dashboard_readonly.py` | E.8 + evidence | Facade API | `allowed_canonical` | **erledigt F.4** |
| `app.py` | `ai_prompt_generate_stub` | Facade API | `allowed_canonical` | **erledigt F.4** |
| `tests/*` | Core direkt | Test | `allowed_internal` | nein |

## HTTP-Direktzugriffe nach F.4

**Keine** verbleibenden `build_dashboard_status()`-Aufrufe in HTTP-Routern oder `app.py`-Handlern.

Verbleibend (erlaubt):
- `deploy_job_state` (Core-intern, nicht HTTP)
- Facade-Delegation zu Core-Ownern
