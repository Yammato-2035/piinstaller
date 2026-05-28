# ROADMAP_BACKEND_STARTUP_AVAILABILITY_DELTA

## Anlass

Backend kann in Hang-Zustand geraten (Service aktiv, Port offen, HTTP Timeout). Dieser Zustand wurde als harter Blocker in Runtime/Governance verankert.

## Delta

- Neuer Blocker in Runtime-Governance:
  - `backend_hanging_active_port_but_http_timeout`
- Runtime-Bereich bleibt `blocked`, bis `/health` und `/api/version` wieder stabil HTTP 200 liefern.
- Standalone-Fallback bleibt getrennt bewertet; kein Runtime-Fake-Green.
- Next Prompt bleibt kurzfristig:
  - `BACKEND_RUNTIME_OPERATOR_RESTART_HANDOFF`
- Zusätzlicher verfügbarer Folgeprompt:
  - `BACKEND_WATCHDOG_IMPLEMENTATION_MVP`

## Verknüpfte Dateien

- `docs/roadmap/setuphelfer_roadmap.json`
- `docs/roadmap/setuphelfer_next_prompts.json`
- `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.json`
- `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.md`
