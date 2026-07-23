# CAPTURE_IMPLEMENTATION_RESULT

Implemented under `backend/core/asus_lab/`:

- `boot_orchestrator.py` — identity → SETUP_LOGS → run dir → baseline → BIOS inventory → win11 prepare → AUTO_IMPORT markers
- `hardware_capture.py` — best-effort command collectors + manifest
- `windows_capture.py` — prepare/finalize using existing live-capture contract
- `bios_control.py` — capability inventory + change contract
- `redaction_gate.py` — clean/redacted/quarantined/blocked
- `carrier_consistency.py` — build/stick gate
- `auto_import.py` + `scripts/rescue/import-asus-lab-runs`

WIN_DIAG: auto Run-ID wrapper, start-collector, collect-final, README-OPERATOR.
