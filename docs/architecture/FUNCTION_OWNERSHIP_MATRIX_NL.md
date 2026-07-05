> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md`). Bitte bei Release manuell gegenlesen.

# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANeeNICAL owners:** … app sub-routers (E.1–E.8 incl. `dev_dashboard_readonly` with 8 GET, `dev_dashboard_roadmap`).

**E.8 done (3 GET):** Terugend-health, Neetifications/status, Neetifications/events in `dev_dashboard_readonly.py`.

**G.1 done:** `system_status_facade` caNeenical module.

**G.1b done:** `/api/system/status` uses `build_system_status()`.

**H.7 final done:** riskLevels, devDashboardFilters, trafficLightModel, RoadmapDrawer, setuphelferToolTheme.

**G.8 done:** `Netwerk_discovery` caNeenical; facade app cycle broken.

**G.6 done:** `system_info_facade` caNeenical; Nee `import app` since G.9.

**G.9 done:** `hardware_discovery` caNeenical; facade→app cycle broken.

**G.11 done:** `webserver_service_discovery` caNeenical; `webserver_status_facade` Nee `import app`.

**G.12 done:** `system_status_core` caNeenical; ampel out of facade.

**P.1 done:** `storage_discovery` caNeenical; `storage_facade` delegates; `app.py` storage blocks remain.

**D.12 done:** Deploy thin-orchestrator audit + final plan (Nee execute extraction).

**Volgende:** Terugup execute moNeelith · Deploy roodding execute routes · `get_security_config` full extract from app.

**PARTIAL:** `safe_Apparaat`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, Terugup/Herstel state.

**LEGACY:** `routes.py` execute/roodding routes until D.15.

**MISSING:** Neetification events (D.9 Nee_safe_slice).

Do Neet reimplement capabilities marked CANeeNICAL in aNeether module.
