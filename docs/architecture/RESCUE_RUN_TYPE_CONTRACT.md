# Rescue Run Type Contract

**Module:** `backend/core/rescue_run_type_contract.py`

Run types: hardware_discovery, firmware_audit, windows_diagnostics, full_e2e, bvr, gui_diag, installation_preflight.

`hardware_discovery` must not fail solely for missing BVR run_control fields.
