# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANONICAL owners:** … app sub-routers (E.1–E.8 incl. `dev_dashboard_readonly` with 8 GET, `dev_dashboard_roadmap`).

**E.8 done (3 GET):** backend-health, notifications/status, notifications/events in `dev_dashboard_readonly.py`.

**G.1 done:** `system_status_facade` canonical module.

**G.1b done:** `/api/system/status` uses `build_system_status()`.

**H.7 final done:** riskLevels, devDashboardFilters, trafficLightModel, RoadmapDrawer, setuphelferToolTheme.

**G.8 done:** `network_discovery` canonical; facade app cycle broken.

**G.6 done:** `system_info_facade` canonical; no `import app` since G.9.

**G.9 done:** `hardware_discovery` canonical; facade→app cycle broken.

**G.11 done:** `webserver_service_discovery` canonical; `webserver_status_facade` no `import app`.

**G.12 done:** `system_status_core` canonical; ampel out of facade.

**P.1 done:** `storage_discovery` canonical; `storage_facade` delegates; `app.py` storage blocks remain.

**D.12 done:** Deploy thin-orchestrator audit + final plan (no execute extraction).

**Next:** Backup execute monolith · deploy rescue execute routes · `get_security_config` full extract from app.

**PARTIAL:** `safe_device`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, backup/restore state.

**LEGACY:** `routes.py` execute/rescue routes until D.15.

**MISSING:** Notification events (D.9 no_safe_slice).

Do not reimplement capabilities marked CANONICAL in another module.
