# APP Router Slice — Kandidaten E.6

**HEAD (Baseline):** `e0e9fac` (nach E.5)

## Ausgewählte E.6-Routen

| Route | Funktion | Core-Modul | nutzt bestehendes Modul | Risiko | E.6 geeignet | Grund |
|-------|----------|------------|-------------------------|--------|--------------|-------|
| `GET /api/dev-dashboard/roadmap/next-prompts` | `dev_dashboard_roadmap_next_prompts` | `load_roadmap_registry_bundle` | ja | low | **ja** | Bundle-Slice, kein dashboard_context |
| `GET /api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}` | `dev_dashboard_roadmap_export_next_prompt` | `export_next_prompt_text` | ja | low | **ja** | Read-only Text-Export aus Registry |

## Ausgeschlossen

| Route | Grund |
|-------|-------|
| `GET /api/dev-dashboard/roadmap` | `build_dashboard_status` |
| `GET /api/dev-dashboard/status` | DCC-Aggregation |
