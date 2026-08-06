# PRE_BUILD_TARGETED_TEST_RESULTS — PI-RS-ASUS-CARRIER-BUILD-WRITE-004

Stand: 2026-08-06T19:50Z  
Workspace: `/home/volker/piinstaller-asus-emergency-linux-telemetry-003`  
Branch: `pi-rs-asus-emergency-linux-telemetry-003`  
Version: Projekt **1.10.2.0**, Payload **1.10.0.17**

## Befehl

```bash
PYTHONPATH=backend python3 -m pytest -q \
  backend/tests/test_asus_boot_sentinels_v1.py \
  backend/tests/test_hardware_baseline_*.py \
  backend/tests/test_hardware_inventory_v1.py \
  backend/tests/test_hardware_discovery_v1.py \
  backend/tests/test_hardware_contracts_v1.py \
  backend/tests/test_hardware_api_readonly_v1.py \
  backend/tests/test_hardware_compat_catalog_v1.py \
  backend/tests/test_hardware_documentation_i18n_v1.py \
  backend/tests/test_hardware_telemetry_redaction_v1.py \
  backend/tests/test_rescue_telemetry_spool_r3.py \
  backend/tests/test_rescue_telemetry_client_contract_v2.py \
  backend/tests/test_rescue_telemetry_*redaction*.py \
  backend/tests/test_pi_rs_payload_telemetry001_*.py \
  backend/tests/test_pi_rs_tel003_version_bump.py \
  backend/tests/test_pi_rs_tel004_version_bump.py \
  backend/tests/test_rescue_fat32_esp_usb*.py \
  backend/tests/test_fat32_esp_writer_execution_mode.py \
  backend/tests/test_safe_device_storage_protection_v1.py \
  backend/tests/test_storage_facade_contracts_v1.py \
  backend/tests/test_storage_discovery_v1.py \
  backend/tests/test_usb_device_detection_v1.py \
  backend/tests/test_rescue_usb_operator_selection_v1.py \
  backend/tests/test_redaction_contract_v1.py \
  backend/tests/test_diagnostics_i18n_consistency_v1.py \
  backend/tests/test_i18n_backup_diag_keys_v1.py \
  backend/tests/test_deploy_runner_permission_boundary_v1.py \
  backend/tests/test_pi_rs_msi_*payload_version*.py \
  backend/tests/test_rescue_payload_msi_gui003_tui_console_isolation.py
```

Log: `pre_build_targeted_pytest.txt`

## Ergebnis

| Metrik | Wert |
|--------|------|
| passed | **316** |
| skipped | 6 |
| failed | **0** |
| exit | 0 |

Gruppenabdeckung: Sentinels/ASUS-Profile, Hardware-Baseline/Inventur, Telemetrie/Redaction,
Carrier/Writer-Safety, Storage-Identity, i18n, Boundaries, Payload-Versionspins.

Status: **passed**
