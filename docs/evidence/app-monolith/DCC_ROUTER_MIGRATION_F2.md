# DCC Router Migration — Phase F.2

**HEAD:** `3c98105` (vor Migration)

## Migrierte Routen

| Route | Bisherige Funktion | Direkte Core-Abhängigkeiten | Neue Facade-Funktion | Migration |
|-------|-------------------|----------------------------|----------------------|-----------|
| `GET /api/dev-dashboard/status` | `build_dev_dashboard_status` | `build_dashboard_status` (via Service) | `build_dashboard_status_body` (in Service) | **ja** |
| `GET /api/dev-dashboard/roadmap` | `dev_dashboard_roadmap` | `build_dashboard_status` + `load_roadmap_registry_bundle` | `build_dcc_roadmap_api_bundle` | **ja** |
| `GET /api/dev-dashboard/control-center-summary` | `dev_dashboard_control_center_summary` | `build_dashboard_status` + `build_control_center_summary` | `build_dcc_control_center_summary_api` | **ja** |
| `GET /api/dev-dashboard/project-overview` | `dev_dashboard_project_overview` | `build_project_overview_dashboard_state` | `build_dcc_project_overview_body` | **ja** |
| `GET /api/dev-dashboard/prompt-findings` | `dev_dashboard_prompt_findings` | `build_dashboard_status` + `build_prompt_findings` | `build_dcc_prompt_findings_api` | **ja** |
| `GET /api/dev-dashboard/cursor-meta-prompt` | `dev_dashboard_cursor_meta_prompt` | `build_dashboard_status` + Cockpit | `build_dcc_cursor_meta_prompt_api` | **ja** |

## Ausschlüsse / unverändert

- Profil-Gate: `core.dev_dashboard_status_service.build_dcc_profile_block_response` (unverändert)
- API-Pfade, HTTP-Methoden, JSON-Response-Form unverändert
- `POST /api/ai/prompt/generate` — noch direkter `build_dashboard_status` (F.3)

## Service-Migration

`core/dev_dashboard_status_service.py` nutzt `build_dashboard_status_body` statt direktem `build_dashboard_status`.
