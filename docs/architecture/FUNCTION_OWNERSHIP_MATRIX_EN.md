# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 37 capability rows.

**CANONICAL owners:** … deploy sub-routers, app sub-routers (`health`, `version` E.1; `settings`, `status` E.2; `capabilities`, `catalog` E.3).

**PARTIAL:** `safe_device`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, backup/restore state.

**LEGACY:** `routes.py` execute/rescue routes until D.15.

**MISSING:** Notification events (D.9 no_safe_slice).

Do not reimplement capabilities marked CANONICAL in another module.
