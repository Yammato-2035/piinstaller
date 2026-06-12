# APP Router Slice — Kandidaten E.5

**HEAD (Baseline):** `7795212` (nach E.4)

## Ausgewählte E.5-Routen

| Route | Funktion | Core-Modul | nutzt bestehendes Modul | Risiko | E.5 geeignet | Grund |
|-------|----------|------------|-------------------------|--------|--------------|-------|
| `GET /api/dev-dashboard/roadmap/areas` | `dev_dashboard_roadmap_areas` | `load_roadmap_registry_bundle` | ja | low | **ja** | Nur Bundle-Slice |
| `GET /api/dev-dashboard/roadmap/milestones` | `dev_dashboard_roadmap_milestones` | `load_roadmap_registry_bundle` | ja | low | **ja** | Nur Bundle-Slice |
| `GET /api/dev-dashboard/roadmap/blockers` | `dev_dashboard_roadmap_blockers` | `load_roadmap_registry_bundle` | ja | low | **ja** | Nur Bundle-Slice |
| `GET /api/dev-dashboard/roadmap/decisions` | `dev_dashboard_roadmap_decisions` | `load_roadmap_registry_bundle` | ja | low | **ja** | Nur Bundle-Slice |
| `GET /api/dev-dashboard/roadmap/next-prompt` | `dev_dashboard_roadmap_next_prompt` | `load_roadmap_registry_bundle` | ja | low | **ja** | Nur Bundle-Slice |

## Explizit ausgeschlossen

| Route | Grund |
|-------|-------|
| `GET /api/dev-dashboard/roadmap` | `build_dashboard_status` + dashboard_context |
| `GET /api/dev-dashboard/roadmap/next-prompts` | E.5 Limit 5; bleibt in app.py |
| `GET /api/dev-dashboard/roadmap/export-next-prompt/{id}` | `export_next_prompt_text` — E.6 Kandidat |
| `GET /api/dev-dashboard/status` | Volle DCC-Aggregation |
| `/api/status`, `/api/system/network` | subprocess |
