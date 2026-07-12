# PI-RS-MSI-GUI-003 — Test Results

Stand: 2026-07-12

## Unit / Integration

```bash
PYTHONPATH=backend python3 -m pytest -q \
  backend/tests/test_rescue_payload_msi_gui003_tui_console_isolation.py \
  backend/tests/test_pi_rs_msi_gui002_disable_gui_under_msi_compat.py \
  backend/tests/test_pi_rs_msi_fix001_console_shield.py \
  backend/tests/test_pi_rs_msi_gui003_payload_version_1_10_0_16.py
```

Ergebnis: **32 passed, 1 skipped** (payload content skip wenn SquashFS fehlt — nach Repack grün)

## Content Gate

```bash
./scripts/check-rescue-payload-msi-gui003-content.sh
```

Ergebnis: **content_ok=true**

## Secret Gate

```bash
./scripts/check-rescue-payload-no-secrets.sh build/rescue/filesystem.squashfs.repacked-1.10.0.16
```

Ergebnis: **passed**

## Runtime Gate

`runtime_gate_blocked_static_and_payload_tests_only` — kein Port-8000-Deploy-Smoke.

## Simulierter MSI-Boot

`docs/evidence/pi_rs_msi_gui_003/msi_compat_simulated_boot_result.json` — **ok**, kein `x11_starting`.
