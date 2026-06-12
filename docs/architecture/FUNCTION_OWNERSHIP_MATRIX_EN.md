# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANONICAL owners:** … app sub-routers (E.1–E.8 incl. `dev_dashboard_readonly` with 8 GET, `dev_dashboard_roadmap`).

**E.8 done (3 GET):** backend-health, notifications/status, notifications/events in `dev_dashboard_readonly.py`.

**F.2 done:** 6 DCC aggregation GET routes in `app.py` use `dcc_status_facade` API helpers.

**CANDIDATE (E.7):** System Status Facade, Network Info Facade — block `/api/status`, `/api/system/network`.

**PARTIAL:** `safe_device`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, backup/restore state.

**LEGACY:** `routes.py` execute/rescue routes until D.15.

**MISSING:** Notification events (D.9 no_safe_slice).

Do not reimplement capabilities marked CANONICAL in another module.
