> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/DCC_STATUS_ROUTER_MIGRATION_EN.md`). Bitte bei Release manuell gegenlesen.

# DCC Status Router Migration — Phase F.2 (EN)

**HEAD:** `3c98105` · **Status:** done

## Migrated routes (6)

| Route | Facade function |
|-------|-----------------|
| `GET /api/dev-dashboard/status` | `build_dashboard_status_body` (via `dev_dashboard_status_service`) |
| `GET /api/dev-dashboard/roadmap` | `build_dcc_roadmap_api_bundle` |
| `GET /api/dev-dashboard/control-center-summary` | `build_dcc_control_center_summary_api` |
| `GET /api/dev-dashboard/project-overview` | `build_dcc_project_overview_body` |
| `GET /api/dev-dashboard/prompt-findings` | `build_dcc_prompt_findings_api` |
| `GET /api/dev-dashboard/cursor-meta-prompt` | `build_dcc_cursor_meta_prompt_api` |

## Guarantees

- Non API path/method/response changes
- Profile gate unchanged in `dev_dashboard_status_service`
- Non new aggregation/traffic-light logic

## Suivant step

**F.3** — DCC aggregation audit & duplicate status analysis
