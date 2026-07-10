#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "== PI-RS-TEL-004 Cloud Payload v2 Endpoint Auth Gate Smoke =="

python3 -m pytest -q \
  backend/tests/test_pi_rs_tel004_endpoint_config.py \
  backend/tests/test_pi_rs_tel004_payload_v2_contract.py \
  backend/tests/test_pi_rs_tel004_cloud_path_style.py \
  backend/tests/test_pi_rs_tel004_auth_gate.py \
  backend/tests/test_pi_rs_tel004_reachability_gate.py \
  backend/tests/test_pi_rs_tel004_security_negative_cases.py \
  backend/tests/test_pi_rs_tel004_version_bump.py

if [ -x ./scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh ]; then
  ./scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh
fi

if [ -x ./scripts/check-pi-rs-tel-002-network-gated-telemetry-safety.sh ]; then
  ./scripts/check-pi-rs-tel-002-network-gated-telemetry-safety.sh
fi

if [ -x ./scripts/run-tests.sh ]; then
  ./scripts/run-tests.sh
fi

echo "PI-RS-TEL-004 Smoke PASSED"
