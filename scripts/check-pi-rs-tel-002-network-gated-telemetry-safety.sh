#!/usr/bin/env bash
# PI-RS-TEL-002 network-gated telemetry safety gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

fail() {
  echo "check-pi-rs-tel-002-network-gated-telemetry-safety FAIL: $*" >&2
  exit 1
}

SCOPE="backend/core/rescue_lab_telemetry_reachability.py backend/core/rescue_lab_telemetry_offline_queue_preview.py backend/core/rescue_lab_telemetry_send_preview_gate.py backend/core/profile_aware_runtime_gate.py backend/api/routes/rescue_lab_telemetry.py backend/tests/test_pi_rs_tel002_* docs/evidence/pi_rs_tel_002* docs/telemetry/PI_RS_TEL_002*"

# PI-RS-TEL-001 gate must still pass
bash "${ROOT}/scripts/check-pi-rs-tel-001-rescue-lab-telemetry-safety.sh"

# No secrets in evidence
if grep -R -E 'BEGIN PRIVATE KEY|sk_live_' docs/evidence/pi_rs_tel_002* docs/evidence/runtime-results/rescue-lab-telemetry 2>/dev/null \
  | grep -v test-secret | grep -q .; then
  fail "secret pattern in PI-RS-TEL-002 evidence"
fi

# No PII patterns
if grep -R -E '([0-9a-f]{2}:){5}[0-9a-f]{2}|@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' \
  docs/evidence/pi_rs_tel_002* docs/evidence/runtime-results/rescue-lab-telemetry 2>/dev/null | grep -q .; then
  fail "PII pattern in PI-RS-TEL-002 evidence"
fi

# production_ready / auto_replay never true
if grep -R -E 'production_ready["[:space:]]*:[[:space:]]*true|auto_replay_enabled["[:space:]]*:[[:space:]]*true' \
  ${SCOPE} docs/evidence/pi_rs_tel_002* docs/evidence/runtime-results/rescue-lab-telemetry 2>/dev/null \
  | grep -v '# ' | grep -v must_be_false | grep -q .; then
  fail "production_ready or auto_replay true"
fi

# No worker/retry/timer for offline queue
for pattern in 'def.*worker' 'retry_loop' 'Timer(' 'schedule.every' 'while True:' 'auto_replay'; do
  if grep -R -E "${pattern}" backend/core/rescue_lab_telemetry_offline_queue_preview.py 2>/dev/null \
    | grep -v auto_replay_enabled | grep -v auto_replay_must | grep -v 'False' | grep -q .; then
    fail "forbidden offline queue pattern: ${pattern}"
  fi
done

# No auto send on import
if grep -R -E 'execute_send_preview\(|send_rescue_lab_telemetry\(' backend/app.py 2>/dev/null | grep -q .; then
  fail "auto send in app startup"
fi

# Default send-preview must not live-send without flags
if ! grep -q 'allow_send_when_reachable=bool(req.get("allow_send_when_reachable", False))' \
  backend/api/routes/rescue_lab_telemetry.py; then
  fail "send-preview default must be allow_send_when_reachable=false"
fi

# Release profile blocks lab routes
if ! grep -q '_feature_disabled_response' backend/api/routes/rescue_lab_telemetry.py; then
  fail "missing feature_disabled response for release"
fi

# Reachability GET must not send payload
if grep -q 'send_rescue_lab_telemetry' backend/api/routes/rescue_lab_telemetry.py; then
  fail "reachability route must not call send_rescue_lab_telemetry"
fi

# No production URLs
if grep -R -E 'https://telemetrie\.|https://beta\.setuphelfer\.' ${SCOPE} 2>/dev/null | grep -q .; then
  fail "hardcoded production URL"
fi

echo "check-pi-rs-tel-002-network-gated-telemetry-safety: ok"
