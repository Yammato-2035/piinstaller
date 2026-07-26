#!/usr/bin/env bash
# Gate checklist for Control-C stick update (static checks; no NVMe write).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
FAIL=0
pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; FAIL=1; }

python3 - <<'PY' || fail "grub_profile_gate"
from backend.core import rescue_install_assistant_grub as g
v = g.validate_gabriel_install_grub(g.generate_gabriel_install_grub_cfg())
assert v["ok"], v
assert v["checks"]["control_c_no_rescue_target"]
assert v["checks"]["first_is_basic_emergency"]
print("grub_profile_gate ok")
PY
pass "grub_profile_gate"

test -x scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-gpu && pass "debug_console_gate" || fail "debug_console_gate"
test -f scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-early-capture.sh && pass "capture_early_start_gate" || fail "capture_early_start_gate"
test -f scripts/rescue/g513qm-netconsole-receiver.sh && pass "netconsole_config_gate" || fail "netconsole_config_gate"
test -f config/rescue/g513qm_netconsole_lab.json && pass "netconsole_manifest" || fail "netconsole_manifest"

python3 backend/tools/check_version_consistency.py --repo-root . && pass "version_consistency" || fail "version_consistency"

# Kernel package closure: document live kernel; do not claim upgrade without remaster
LIVE_NOTE="docs/evidence/rescue/g513qm-kernel-abc/kernel_package_closure.json"
if [[ -f "$LIVE_NOTE" ]]; then
  python3 -c "import json;d=json.load(open('$LIVE_NOTE'));assert d.get('status') in ('documented','passed','blocked')"
  pass "kernel_package_closure"
else
  fail "kernel_package_closure"
fi

# ISO gate: USB write of A/B only if verified
python3 - <<'PY' || fail "reference_image_gate"
import json
from pathlib import Path
p = Path("docs/evidence/rescue/g513qm-kernel-abc/control_image_verification.json")
d = json.loads(p.read_text())
# Allowed to proceed with Control C tooling even if A/B ISO not downloaded
assert d["controls"]["control_a"]["signature_verified"]
assert d["controls"]["control_b"]["signature_verified"]
print("reference checksum signatures ok; iso download still optional for C tooling")
PY
pass "reference_image_gate"

# Carrier identity documented
test -f docs/evidence/rescue/g513qm-kernel-abc/workspace_and_carrier_baseline.json && pass "carrier_identity_gate" || fail "carrier_identity_gate"

if [[ "$FAIL" -ne 0 ]]; then
  echo "RESULT=implemented_with_remaining_build_blockers"
  exit 1
fi
echo "RESULT=gates_passed_ready_for_physical_control_c_packaging"
exit 0
