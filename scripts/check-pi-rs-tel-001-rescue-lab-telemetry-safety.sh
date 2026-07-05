#!/usr/bin/env bash
# PI-RS-TEL-001 rescue stick lab telemetry safety gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

fail() {
  echo "check-pi-rs-tel-001-rescue-lab-telemetry-safety FAIL: $*" >&2
  exit 1
}

SCOPE="backend/core/rescue_lab_telemetry_*.py backend/api/routes/rescue_lab_telemetry.py backend/tests/test_pi_rs_tel001_* docs/evidence/pi_rs_tel_001* docs/telemetry/PI_RS_TEL_001* docs/faq/PI_RS_TEL_001* docs/kb/PI_RS_TEL_001*"

# No production URLs hardcoded
if grep -R -E 'https://telemetrie\.|https://beta\.setuphelfer\.|https://setuphelfer\.de/api' \
  ${SCOPE} 2>/dev/null | grep -q .; then
  fail "production URL in PI-RS-TEL-001 artifacts"
fi

# No real secrets in repo files (allow placeholders)
if grep -R -E 'BEGIN PRIVATE KEY|sk_live_' \
  backend/core/rescue_lab_telemetry_* backend/api/routes/rescue_lab_telemetry.py \
  docs/evidence/pi_rs_tel_001* 2>/dev/null \
  | grep -v placeholder | grep -v replace-with | grep -v test-secret | grep -q .; then
  fail "secret pattern in PI-RS-TEL-001 files"
fi

# No hardcoded secret values for rescue stick lab client
if grep -R -E 'SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET=[^$\s]' \
  backend/core docs/evidence/pi_rs_tel_001* 2>/dev/null \
  | grep -v replace-with | grep -v test-secret | grep -v 'not configured' | grep -q .; then
  fail "literal rescue stick lab secret value"
fi

# Evidence: no MAC/IP/hostname/email
if grep -R -E '([0-9a-f]{2}:){5}[0-9a-f]{2}|@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' \
  docs/evidence/pi_rs_tel_001* 2>/dev/null | grep -q .; then
  fail "PII pattern in PI-RS-TEL-001 evidence"
fi

# production_ready must stay false in evidence/examples
if grep -R 'production_ready.*true' docs/evidence/pi_rs_tel_001* backend/core/rescue_lab_telemetry_* 2>/dev/null \
  | grep -v 'production_ready.*false' | grep -v 'production_ready_must_be_false' | grep -v '# ' | grep -q .; then
  fail "production_ready true in PI-RS-TEL-001 scope"
fi

# No automatic send on startup
if grep -R -E 'send_rescue_lab_telemetry\(' backend/core/rescue_lab_telemetry_*.py backend/app.py 2>/dev/null \
  | grep -v 'def send_rescue_lab_telemetry' | grep -v rescue_lab_telemetry.py | grep -q .; then
  fail "automatic rescue lab telemetry send outside API route"
fi

# No backup/restore/usb-write paths touched in new modules
for forbidden in backup_execute restore_usb 'dd ' mkfs 'mount('; do
  if grep -R -E "${forbidden}" backend/core/rescue_lab_telemetry_*.py backend/api/routes/rescue_lab_telemetry.py 2>/dev/null | grep -q .; then
    fail "forbidden keyword ${forbidden} in PI-RS-TEL-001 modules"
  fi
done

# Synthetic example must not contain forbidden fields
EXAMPLE="${ROOT}/docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow/rescue_lab_payload_synthetic_example.redacted.json"
if [[ -f "${EXAMPLE}" ]]; then
  for field in mac mac_address ip ip_address hostname email raw_log serial serial_number; do
    if grep -q "\"${field}\"" "${EXAMPLE}"; then
      fail "forbidden field ${field} in synthetic example"
    fi
  done
fi

echo "check-pi-rs-tel-001-rescue-lab-telemetry-safety: ok"
