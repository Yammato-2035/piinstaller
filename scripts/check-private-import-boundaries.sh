#!/usr/bin/env bash
# Private import boundary gate — public-safe modules must not import private-only paths.
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "${ROOT}"

EXIT_OK=0
EXIT_BLOCKED=10
EXIT_REVIEW=20

status="ok"
exit_code="${EXIT_OK}"
warnings=()

PRIVATE_IMPORT_PATTERNS=(
  "cloudserver_private"
  "cloudserver_edition"
  "telemetry_server"
  "internal_telemetry"
  "diagnostics_server"
  "internal_diagnostics"
  "operator_dashboard"
)

PUBLIC_SAFE_PREFIXES=(
  "backend/core/storage_facade.py"
  "backend/core/mount_facade.py"
  "backend/core/safety_facade.py"
  "backend/core/redaction_contract.py"
  "backend/core/diagnostic_finding_contract.py"
  "backend/core/telemetry_client_contract.py"
  "backend/core/audit_event_contract.py"
  "backend/tests/test_public_private_boundaries_v1.py"
  "backend/tests/test_redaction_contract_v1.py"
  "backend/tests/test_telemetry_client_contract_v1.py"
)

RESCUE_STORAGE_MOUNT_PATTERN='backend/(modules|core)/rescue.*\.py|backend/deploy/runner_rescue.*\.py'

while IFS= read -r py; do
  rel="${py#${ROOT}/}"
  for pat in "${PRIVATE_IMPORT_PATTERNS[@]}"; do
    if grep -qE "(from|import)[[:space:]].*${pat}" "${py}" 2>/dev/null; then
      warnings+=("public_imports_private:${rel}:${pat}")
      status="blocked"
      exit_code="${EXIT_BLOCKED}"
    fi
  done
done < <(find "${ROOT}/backend" -name '*.py' -not -path '*/__pycache__/*' -not -path '*/.venv/*' -not -path '*/venv/*' 2>/dev/null)

# Rescue files should prefer core facades for storage/mount/safety
while IFS= read -r py; do
  rel="${py#${ROOT}/}"
  if grep -qE '\blsblk\b' "${py}" 2>/dev/null && ! grep -q 'storage_facade\|storage_discovery' "${py}" 2>/dev/null; then
    if [[ "${rel}" =~ ${RESCUE_STORAGE_MOUNT_PATTERN} ]]; then
      warnings+=("rescue_direct_lsblk:${rel}")
      status="review_required"
      [[ "${exit_code}" -eq "${EXIT_OK}" ]] && exit_code="${EXIT_REVIEW}"
    fi
  fi
done < <(find "${ROOT}/backend" -name '*.py' -not -path '*/__pycache__/*' 2>/dev/null)

# Frontend: no secret/token operator logic
while IFS= read -r ts; do
  rel="${ts#${ROOT}/}"
  for tok in "JWT_SECRET" "PLESK_API_TOKEN" "OPERATOR_DASHBOARD" "TELEMETRY_SERVER_SECRET"; do
    if grep -q "${tok}" "${ts}" 2>/dev/null; then
      warnings+=("frontend_forbidden_token:${rel}:${tok}")
      status="blocked"
      exit_code="${EXIT_BLOCKED}"
    fi
  done
done < <(find "${ROOT}/frontend/src" \( -name '*.ts' -o -name '*.tsx' \) 2>/dev/null)

# app.py size warning only
if [[ -f "${ROOT}/backend/app.py" ]]; then
  lines=$(wc -l < "${ROOT}/backend/app.py" | tr -d ' ')
  if [[ "${lines}" -gt 12000 ]]; then
    warnings+=("app_py_line_count_high:${lines}")
    [[ "${status}" == "ok" ]] && status="review_required"
    [[ "${exit_code}" -eq "${EXIT_OK}" ]] && exit_code="${EXIT_REVIEW}"
  fi
fi

WARNINGS_JSON="[]"
if [[ ${#warnings[@]} -gt 0 ]]; then
  WARNINGS_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${warnings[@]}")"
fi
python3 - <<PY
import json
warnings = json.loads('''${WARNINGS_JSON}''')
print(json.dumps({"status": "${status}", "exit_code": ${exit_code}, "warnings": warnings}, ensure_ascii=False))
PY

exit "${exit_code}"
