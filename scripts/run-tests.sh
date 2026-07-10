#!/usr/bin/env bash
# Aggregate test runner for DCC-VIS-001 and core gates.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== DCC-VIS-001 frontend tests =="
cd frontend && npm test -- --run \
  src/dcc/visibility/runtimeStatusModel.test.ts \
  src/dcc/visibility/changelogModel.test.ts \
  src/lib/devDashboard/loadDevDashboard.test.ts \
  src/lib/devDashboard/governanceMatrix.test.ts \
  src/components/AppLanguageSwitcher.test.ts
cd "$ROOT"

echo "== DCC-VIS-001 safety gate =="
bash "$ROOT/scripts/check-dcc-vis-001-safety.sh"

echo "== version consistency =="
python3 "$ROOT/backend/tools/check_version_consistency.py" --repo-root "$ROOT"

echo "== PI-RS-TEL-001 pytest =="
python3 -m pytest \
  "$ROOT/backend/tests/test_pi_rs_tel001_rescue_lab_telemetry_model.py" \
  "$ROOT/backend/tests/test_pi_rs_tel001_rescue_lab_telemetry_signing.py" \
  "$ROOT/backend/tests/test_pi_rs_tel001_rescue_lab_telemetry_client.py" \
  "$ROOT/backend/tests/test_pi_rs_tel001_rescue_lab_telemetry_api.py"

echo "== PI-RS-TEL-001 safety gate =="
bash "$ROOT/scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh"

echo "== PI-RS-TEL-002 pytest =="
PYTHONPATH="$ROOT/backend" python3 -m pytest \
  "$ROOT/backend/tests/test_pi_rs_tel002_profile_aware_runtime_gate_contract.py" \
  "$ROOT/backend/tests/test_pi_rs_tel002_reachability_model.py" \
  "$ROOT/backend/tests/test_pi_rs_tel002_reachability_api.py" \
  "$ROOT/backend/tests/test_pi_rs_tel002_send_preview_network_gate.py" \
  "$ROOT/backend/tests/test_pi_rs_tel002_offline_queue_preview.py"

echo "== PI-RS-TEL-002 safety gate =="
bash "$ROOT/scripts/check-pi-rs-tel-002-network-gated-telemetry-safety.sh"

echo "== PI-RS-TEL-003 pytest =="
PYTHONPATH="$ROOT/backend" python3 -m pytest \
  "$ROOT/backend/tests/test_pi_rs_tel003_cross_repo_contract.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_rescue_payload_compatibility.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_diagnostics_validate_preview.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_findings_preview.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_offline_queue_compatibility.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_security_negative_cases.py" \
  "$ROOT/backend/tests/test_pi_rs_tel003_version_bump.py"

echo "run-tests.sh: ok"
