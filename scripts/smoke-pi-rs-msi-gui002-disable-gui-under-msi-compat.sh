#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "== PI-RS-MSI-GUI-002 Smoke =="

if [ -x ./scripts/check-no-secrets.sh ]; then
  ./scripts/check-no-secrets.sh
fi

if [ -x ./scripts/check-no-dangerous-commands.sh ]; then
  ./scripts/check-no-dangerous-commands.sh
fi

python3 -m pytest \
  backend/tests/test_pi_rs_msi_gui002_disable_gui_under_msi_compat.py \
  backend/tests/test_pi_rs_msi_gui002_tui_menu_guard.py \
  backend/tests/test_pi_rs_msi_gui002_no_chvt_openvt_when_blocked.py \
  backend/tests/test_pi_rs_msi_gui002_tui_rerender_after_gui_failure.py \
  backend/tests/test_pi_rs_msi_gui002_payload_version_1_10_0_15.py

if [ -x ./scripts/run-tests.sh ]; then
  ./scripts/run-tests.sh
fi

echo "PI-RS-MSI-GUI-002 Smoke PASSED"
