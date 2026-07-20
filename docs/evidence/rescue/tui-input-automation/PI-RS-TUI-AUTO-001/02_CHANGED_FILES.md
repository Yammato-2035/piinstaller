# 02 Changed Files

## Created

- `backend/core/rescue_tui_input_diagnostic*.py` (contract, evdev, inventory, evidence, evaluate, main)
- `backend/tests/test_rescue_tui_input_diagnostic_v1.py`
- `scripts/rescue-live/image/setuphelfer-rescue-tui-input-diagnostic`
- `scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-input-diagnostic.service`
- `scripts/rescue/import-tui-input-diagnostic-runs.sh`
- Docs under `docs/rescue-stick`, `docs/operator`, `docs/knowledge-base/rescue`
- This evidence directory

## Modified

- `backend/core/rescue_msi_lab_auto_boot.py` — append-only diag menuentry
- `backend/core/rescue_fat32_esp_usb_writer.py` — include diag entry (not default)
- `scripts/rescue-live/image/setuphelfer-rescue-tui.sh` — read-only guard
- `scripts/rescue/inject-gui-bvr-fixes-into-stick-squashfs.sh` — inject CLI/unit + all version carriers
- `config/rescue_payload_version.json` → **1.10.0.59** + `pi_rs_tui_auto_001`
