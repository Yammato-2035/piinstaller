# BVR Core Freeze – PI-RS-BVR-GUI-DCC-001

## Frozen (do not change unless strictly required)

- `backend/core/rescue_physical_e2e_unattended.py`
- `backend/core/rescue_physical_e2e_orchestrator.py` (and backup/verify/restore workflow helpers used by it)
- `backend/core/rescue_physical_e2e_destructive_target.py`
- `backend/core/rescue_physical_e2e_run_control.py` (SABRENT identity defaults)
- `scripts/rescue-live/image/setuphelfer-rescue-auto-physical-e2e`
- `scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-physical-e2e.service`

## GUI / runtime layer (allowed)

- `scripts/rescue-live/image/setuphelfer-rescue-ui-launch`
- `scripts/rescue-live/image/setuphelfer-rescue-ui-http-server` (new)
- `scripts/rescue-live/image/auto-e2e-progress.html` (+ locale assets)
- `scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh`
- `scripts/rescue-live/image/setuphelfer-rescue-kiosk-start`
- `backend/core/rescue_auto_e2e_gui_status.py`
- DCC/version/drift contracts and docs
- i18n locale files for rescue GUI progress

## Requires explicit justification

Any edit to frozen BVR-core files must be documented in the final report with regression tests.
