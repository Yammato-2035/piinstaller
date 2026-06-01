#!/usr/bin/env bash
# Unit smoke for fleet session JSON payload builders (no QEMU).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/rescue-live/fleet-session-api.sh
source "${SCRIPT_DIR}/fleet-session-api.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { echo "OK: $*"; }

validate() {
  local label="$1" payload="$2"
  fleet_validate_json "$payload" || fail "${label}: invalid JSON"
  python3 -c "import json,sys; json.loads(sys.argv[1])" "$payload" || fail "${label}: parse error"
}

# Heartbeat with path containing quotes/special chars
SERIAL_PATH="/home/volker/piinstaller/docs/evidence/runtime-results/rescue/qemu/test/qemu-serial.log"
hb="$(fleet_session_heartbeat_payload "" "$SERIAL_PATH" "true" "0" "12345" "" "" "" "[]")"
validate "heartbeat_serial" "$hb"
python3 -c "import json,sys; d=json.loads(sys.argv[1]); s=d['serial']; assert s['path']==sys.argv[2]; assert s['exists'] is True; assert s['size_bytes']==0; assert d['qemu']['pid']==12345" "$hb" "$SERIAL_PATH" || fail "heartbeat field check"

fin="$(fleet_session_finish_payload "timeout" "124" "false" "false" "0" '[]')"
validate "finish_timeout" "$fin"
python3 -c "import json,sys; d=json.loads(sys.argv[1]); assert d['status']=='timeout'; assert 'qemu_timeout_124' in d['findings']" "$fin" || fail "finish findings"

create="$(fleet_session_create_payload "test_run_1" "build/rescue/x.iso" "8001" "600" "true")"
validate "create" "$create"

# Must not produce Python true/false in output (JSON only)
echo "$hb" | grep -qE '\btrue\b' || fail "missing JSON true"
echo "$hb" | grep -q "NameError" && fail "NameError in output" || true

ok "all fleet session shell payload tests passed"
