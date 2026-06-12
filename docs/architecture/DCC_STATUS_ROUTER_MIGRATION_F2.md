# DCC Status Router Migration — Phase F.2

**HEAD:** `8bb910c` · **Status:** erledigt

## Migrierte Routen (6)

| Route | Facade-Funktion |
|-------|-----------------|
| `GET /api/dev-dashboard/status` | `build_dashboard_status_body` (via `dev_dashboard_status_service`) |
| `GET /api/dev-dashboard/roadmap` | `build_dcc_roadmap_api_bundle` |
| `GET /api/dev-dashboard/control-center-summary` | `build_dcc_control_center_summary_api` |
| `GET /api/dev-dashboard/project-overview` | `build_dcc_project_overview_body` |
| `GET /api/dev-dashboard/prompt-findings` | `build_dcc_prompt_findings_api` |
| `GET /api/dev-dashboard/cursor-meta-prompt` | `build_dcc_cursor_meta_prompt_api` |

## Garantien

- Keine API-Pfad-/Methoden-/Response-Änderung
- Profil-Gate unverändert in `dev_dashboard_status_service`
- Keine neue Aggregations-/Ampel-Logik

## Evidence

- [DCC_ROUTER_MIGRATION_F2.md](../evidence/app-monolith/DCC_ROUTER_MIGRATION_F2.md)
- [DCC_DIRECT_AGGREGATION_USAGE_F2.md](../evidence/app-monolith/DCC_DIRECT_AGGREGATION_USAGE_F2.md)

## Nächster Schritt

**F.3** — abgeschlossen (Audit). **F.4** — ai_prompt_generate_stub + readonly Facade-Sections.

Siehe [DCC_AGGREGATION_AUDIT_F3.md](DCC_AGGREGATION_AUDIT_F3.md) · [DCC_NEXT_MIGRATIONS_F3.md](DCC_NEXT_MIGRATIONS_F3.md)
