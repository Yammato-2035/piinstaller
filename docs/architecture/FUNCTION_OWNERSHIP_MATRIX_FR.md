> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md`). Bitte bei Release manuell gegenlesen.

# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANonNICAL owners:** … app sub-routers (E.1–E.8 incl. `dev_dashboard_readonly` with 8 GET, `dev_dashboard_roadmap`).

**E.8 done (3 GET):** Retourend-health, Nontifications/status, Nontifications/events in `dev_dashboard_readonly.py`.

**G.1 done:** `system_status_facade` caNonnical module.

**G.1b done:** `/api/system/status` uses `build_system_status()`.

**H.7 final done:** riskLevels, devDashboardFilters, trafficLightModel, RoadmapDrawer, setuphelferToolTheme.

**G.8 done:** `Réseau_discovery` caNonnical; facade app cycle broken.

**G.6 done:** `system_info_facade` caNonnical; Non `import app` since G.9.

**G.9 done:** `hardware_discovery` caNonnical; facade→app cycle broken.

**G.11 done:** `webserver_service_discovery` caNonnical; `webserver_status_facade` Non `import app`.

**G.12 done:** `system_status_core` caNonnical; ampel out of facade.

**P.1 done:** `storage_discovery` caNonnical; `storage_facade` delegates; `app.py` storage blocks remain.

**D.12 done:** Déploiement thin-orchestrator audit + final plan (Non execute extraction).

**Suivant:** Retourup execute moNonlith · Déploiement Secours execute routes · `get_security_config` full extract from app.

**PARTIAL:** `safe_Périphérique`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, Retourup/Restauration state.

**LEGACY:** `routes.py` execute/Secours routes until D.15.

**MISSING:** Nontification events (D.9 Non_safe_slice).

Do Nont reimplement capabilities marked CANonNICAL in aNonther module.
