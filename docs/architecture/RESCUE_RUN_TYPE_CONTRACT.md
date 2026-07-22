# Rescue Run Type Contract

**Module:** `backend/core/rescue_run_type_contract.py`

Run types: hardware_discovery, firmware_audit, windows_diagnostics, full_e2e, bvr, gui_diag, installation_preflight.

`hardware_discovery` must not fail solely for missing BVR run_control fields.

## PI-RS-ASUS-PHYSICAL-DIAG-003

- `hardware_discovery` requires no BVR run_control.
- NVMe identity: model + serial_hash + EUI/NGUID + nsid + PCI (never `/dev/nvmeXn1` alone).
- Write authorization stays false after provisional role_binding.
