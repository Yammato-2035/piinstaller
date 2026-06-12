# Function Ownership Matrix (EN)

Same ownership as [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md) — 31 capability rows.

**CANONICAL owners:** `storage_facade`, `mount_facade`, `safety_facade`, `runner_registry`, `runner_result_contract`, `runner_api_facade`, `runner_risk_gate`, deploy sub-routers (`routes_registry` … `routes_runtime`).

**PARTIAL:** `safe_device`, `write_guard`, `storage_detection`, DCC aggregation, frontend clients, backup/restore state.

**LEGACY:** `routes.py` execute/rescue routes until D.15.

**MISSING:** Notification events (D.9 no_safe_slice).

Do not reimplement capabilities marked CANONICAL in another module.
