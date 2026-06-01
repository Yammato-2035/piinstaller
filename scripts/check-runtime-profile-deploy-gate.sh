#!/usr/bin/env bash
# Profile-aware runtime gate (read-only). Independent of legacy dev-dashboard gate.
#
# Does NOT require /api/dev-dashboard/status (404 is correct in release profile).
# Legacy gate: scripts/check-runtime-deploy-gate.sh (non_profile_aware, dev-dashboard required).
#
# Exit codes:
#   0  OK
#  10  setuphelfer-backend.service not active
#  12  project_version mismatch (workspace vs API)
#  13  backend_runtime_path unexpected
#  17  install_profile missing or invalid
#  18  profile_manifest_mismatch
#  19  forbidden_api_path_visible / profile_gate_red
#  20  required_api_path_missing
#  21  public_exposure_blocked
#  22  frontend_profile_mismatch
#  24  /api/version failed
#  25  openapi.json failed (when HTTP probe needs it)
#  30  unknown

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVAL_PY="$REPO_ROOT/scripts/runtime_profile_deploy_gate_eval.py"
LEGACY_GATE="$REPO_ROOT/scripts/check-runtime-deploy-gate.sh"
BASE_URL="${SETUPHELFER_VERSION_URL:-http://127.0.0.1:8000}"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"
WS_VER="${BACKEND_GATE_WORKSPACE_VERSION_JSON:-$REPO_ROOT/config/version.json}"

log() { printf '%s\n' "$*" >&2; }

probe_http_code() {
  local url="$1"
  local out_file="$2"
  local code_var="$3"
  local curl_out curl_ec
  set +e
  curl_out="$(curl -sS -o "$out_file" -w '%{http_code}' --connect-timeout 2 --max-time 12 "$url" 2>/dev/null)"
  curl_ec=$?
  set -e
  if [[ "$curl_ec" -eq 0 ]] && [[ -n "$curl_out" ]]; then
    printf -v "$code_var" '%s' "${curl_out:0:3}"
    return 0
  fi
  printf -v "$code_var" '%s' "000"
  return 1
}

if ! command -v curl >/dev/null 2>&1; then
  log "check-runtime-profile-deploy-gate: curl missing"
  exit 30
fi
if ! command -v python3 >/dev/null 2>&1; then
  log "check-runtime-profile-deploy-gate: python3 missing"
  exit 30
fi
if [[ ! -f "$EVAL_PY" ]]; then
  log "check-runtime-profile-deploy-gate: missing $EVAL_PY"
  exit 30
fi

if command -v systemctl >/dev/null 2>&1; then
  if ! systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
    log "check-runtime-profile-deploy-gate: service $SERVICE not active"
    exit 10
  fi
fi

tmp_api="$(mktemp)"
tmp_oa="$(mktemp)"
tmp_health="$(mktemp)"
trap 'rm -f "$tmp_api" "$tmp_oa" "$tmp_health"' EXIT

API_RETRIES="${RUNTIME_GATE_API_RETRIES:-10}"
API_SLEEP="${RUNTIME_GATE_API_SLEEP_SEC:-1}"

http_code="000"
health_code="000"
for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  probe_http_code "${BASE_URL}/health" "$tmp_health" health_code || true
  if [[ "$health_code" == "200" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  probe_http_code "${BASE_URL}/api/version" "$tmp_api" http_code || true
  if [[ "$http_code" == "200" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

if [[ "$http_code" != "200" ]]; then
  log "check-runtime-profile-deploy-gate: /api/version HTTP ${http_code} (nach ${API_RETRIES} Versuchen; health=${health_code}; ggf. journalctl -u $SERVICE -n 40)"
  exit 24
fi

oa_code="000"
for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  probe_http_code "${BASE_URL}/openapi.json" "$tmp_oa" oa_code || true
  if [[ "$oa_code" == "200" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

if [[ "$oa_code" != "200" ]]; then
  log "check-runtime-profile-deploy-gate: /openapi.json HTTP ${oa_code} (nach ${API_RETRIES} Versuchen)"
  exit 25
fi

bind="${SETUPHELFER_BIND_ADDRESS:-127.0.0.1}"
if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | grep -qE '0\.0\.0\.0:8000|\[::\]:8000'; then
    bind="0.0.0.0"
  fi
fi

set +e
python3 "$EVAL_PY" \
  --api-version-file "$tmp_api" \
  --openapi-file "$tmp_oa" \
  --base-url "$BASE_URL" \
  --bind-address "$bind" \
  --workspace-version-file "$WS_VER"
pec=$?
set -e

if [[ "$pec" -ne 0 ]]; then
  log "check-runtime-profile-deploy-gate: profile evaluator exit=$pec"
  exit "$pec"
fi

if [[ -x "$LEGACY_GATE" ]] && [[ "${RUNTIME_PROFILE_GATE_RUN_LEGACY_INFO:-1}" == "1" ]]; then
  set +e
  "$LEGACY_GATE" >/dev/null 2>&1
  legacy_ec=$?
  set -e
  if [[ "$legacy_ec" -ne 0 ]]; then
    log "check-runtime-profile-deploy-gate: legacy_gate_non_profile_aware exit=$legacy_ec (informational only)"
  fi
fi

log "check-runtime-profile-deploy-gate: OK (profile-aware, dev-dashboard independent)"
exit 0
