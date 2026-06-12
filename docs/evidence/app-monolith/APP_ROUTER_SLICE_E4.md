# APP Router Slice E.4 — Festlegung

**HEAD vorher:** `c36c304`  
**Ergebnis:** `safe_app_router_slice_e4` (5 Routen)

## Extrahierte Routen → `dev_dashboard_readonly.py`

| Pfad | Core-Funktion |
|------|---------------|
| `GET /api/dev-dashboard/modules` | `build_modules_list` |
| `GET /api/dev-dashboard/modules/{module_id}` | `build_module_detail` |
| `GET /api/dev-dashboard/evidence-index` | `build_evidence_index` |
| `GET /api/dev-dashboard/manual-command-runs` | `build_manual_command_runs_index` |
| `GET /api/dev-dashboard/recent-evidence` | `build_recent_evidence_feed` |

## Nächster Schritt E.5

Roadmap-Subrouter (`roadmap/areas`, …) — nur `load_roadmap_registry_bundle`, ohne `build_dashboard_status`.
