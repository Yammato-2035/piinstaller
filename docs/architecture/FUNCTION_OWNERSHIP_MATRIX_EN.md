# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANONICAL owners:** … deploy sub-routers, app sub-routers (E.1–E.6 incl. `dev_dashboard_readonly`, `dev_dashboard_roadmap`).

**CANDIDATE (E.7 audit):** System Status Facade, Network Info Facade, DCC Status Facade, Dev Dashboard Aggregation Facade — block extraction of `/api/status`, `/api/system/network`, `/api/dev-dashboard/status`, `/api/dev-dashboard/roadmap`.

**E.8 safe slice (3 GET):** backend-health, notifications/status, notifications/events → extend `dev_dashboard_readonly.py`.

**PARTIAL:** `safe_device`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, backup/restore state.

**LEGACY:** `routes.py` execute/rescue routes until D.15.

**MISSING:** Notification events (D.9 no_safe_slice).

Do not reimplement capabilities marked CANONICAL in another module.
