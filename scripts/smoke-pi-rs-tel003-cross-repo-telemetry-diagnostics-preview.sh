#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "== PI-RS-TEL-003 Cross-Repo Telemetry Diagnostics Preview Smoke =="

if [ -x ./scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh ]; then
  ./scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh
fi

if [ -x ./scripts/check-pi-rs-tel-002-network-gated-telemetry-safety.sh ]; then
  ./scripts/check-pi-rs-tel-002-network-gated-telemetry-safety.sh
fi

PYTHONPATH="$PWD/backend" python3 -m pytest -q \
  backend/tests/test_pi_rs_tel003_cross_repo_contract.py \
  backend/tests/test_pi_rs_tel003_rescue_payload_compatibility.py \
  backend/tests/test_pi_rs_tel003_diagnostics_validate_preview.py \
  backend/tests/test_pi_rs_tel003_findings_preview.py \
  backend/tests/test_pi_rs_tel003_offline_queue_compatibility.py \
  backend/tests/test_pi_rs_tel003_security_negative_cases.py \
  backend/tests/test_pi_rs_tel003_version_bump.py

if [ -x ./scripts/run-tests.sh ]; then
  ./scripts/run-tests.sh
fi

echo "PI-RS-TEL-003 Smoke PASSED"
