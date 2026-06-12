# DCC Direct Aggregation Usage — Phase F.2

**HEAD:** nach F.2 Migration

## Entfernt aus HTTP-Schicht (app.py / status service)

| Datei | Funktion | Vorher | Nachher |
|-------|----------|--------|---------|
| `app.py` | `dev_dashboard_roadmap` | `build_dashboard_status` + `load_roadmap_registry_bundle` | `build_dcc_roadmap_api_bundle` |
| `app.py` | `dev_dashboard_control_center_summary` | `build_dashboard_status` | `build_dcc_control_center_summary_api` |
| `app.py` | `dev_dashboard_prompt_findings` | `build_dashboard_status` | `build_dcc_prompt_findings_api` |
| `app.py` | `dev_dashboard_cursor_meta_prompt` | `build_dashboard_status` | `build_dcc_cursor_meta_prompt_api` |
| `app.py` | `dev_dashboard_project_overview` | `build_project_overview_dashboard_state` | `build_dcc_project_overview_body` |
| `dev_dashboard_status_service.py` | `build_dev_dashboard_status` | `build_dashboard_status` | `build_dashboard_status_body` |

## Verbleibende Direktzugriffe (Migration offen)

| Datei | Funktion / Kontext | Direktzugriff | Empfehlung |
|-------|-------------------|---------------|------------|
| `app.py` | `ai_prompt_generate_stub` | `build_dashboard_status` | F.3 oder Facade-API |
| `api/routes/dev_dashboard_roadmap.py` | Subroutes (areas, milestones, …) | `load_roadmap_registry_bundle` | OK ohne dashboard_context |
| `core/dev_control_center_summary.py` | intern | `load_roadmap_registry_bundle` | Core-intern, kein HTTP |
| `core/deploy_job_state.py` | Deploy-Job-State | `build_dashboard_status` | Deploy-Domäne, nicht DCC-HTTP |
| `core/dcc_status_facade.py` | Facade-Owner | `build_dashboard_status`, `load_roadmap_registry_bundle` | **kanonisch** |

## Notification / Backend-Health

Keine Direktzugriffe in migrierten Aggregations-Routen — E.8 Router delegiert weiter an Core (nicht Facade-Sections, read-only index).
