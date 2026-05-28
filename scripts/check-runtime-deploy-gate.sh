#!/usr/bin/env bash
# Runtime + Deploy Drift Gate (nur lesend). Kein apt, kein Restart, kein Backup.
#
# Exit-Codes:
#   0  OK
#  10  setuphelfer-backend.service nicht aktiv
#  11  /api/version nicht erreichbar oder HTTP != 200 oder Payload ungueltig
#  12  project_version API != Workspace config/version.json
#  13  backend_runtime_path unplausibel (release/opt)
#  14  deploy_drift: deploy_backend_files empfohlen
#  15  deploy_drift: restart_backend_manual empfohlen (ohne deploy_backend_files)
#  16  Deploy-Manifest-Mismatch (manifest_match false)
#  17  backend_hanging_active_port_but_http_timeout
#  18  backend_version_endpoint_timeout (/health OK, /api/version timeout)
#  20  deploy_drift gray ohne RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY=1 / Dashboard fehlt / unklar
#
# Umgebung (optional):
#   SETUPHELFER_VERSION_URL   Basis-URL (Default http://127.0.0.1:8000)
#   SETUPHELFER_BACKEND_SERVICE  systemd-Unit (Default setuphelfer-backend.service)
#   BACKEND_GATE_WORKSPACE_VERSION_JSON  Workspace version.json
#   RUNTIME_GATE_SKIP_DEPLOY_DRIFT=1      nur Version/Pfad/Dienst (Dev-CI)
#   RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY=1 deploy_drift status gray erlauben

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"
BASE_URL="${SETUPHELFER_VERSION_URL:-http://127.0.0.1:8000}"
WS_VER="${BACKEND_GATE_WORKSPACE_VERSION_JSON:-$REPO_ROOT/config/version.json}"
EVAL_PY="$REPO_ROOT/scripts/runtime_deploy_gate_eval.py"

log() { printf '%s\n' "$*" >&2; }

need_cmd() { command -v "$1" >/dev/null 2>&1; }

probe_http_code() {
  local url="$1"
  local out_file="$2"
  local code_var="$3"
  local kind_var="$4"
  local curl_out curl_ec
  set +e
  curl_out="$(curl -sS -o "$out_file" -w '%{http_code}' --connect-timeout 2 --max-time 8 "$url" 2>/dev/null)"
  curl_ec=$?
  set -e
  if [[ "$curl_ec" -eq 0 ]]; then
    printf -v "$code_var" '%s' "$curl_out"
    printf -v "$kind_var" '%s' "ok"
    return 0
  fi
  printf -v "$code_var" '%s' "000"
  if [[ "$curl_ec" -eq 28 ]]; then
    printf -v "$kind_var" '%s' "timeout"
  elif [[ "$curl_ec" -eq 7 ]]; then
    printf -v "$kind_var" '%s' "unreachable"
  else
    printf -v "$kind_var" '%s' "curl_error_${curl_ec}"
  fi
  return 0
}

if ! need_cmd systemctl; then
  log "check-runtime-deploy-gate: systemctl nicht gefunden"
  exit 20
fi
if ! systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
  log "check-runtime-deploy-gate: Dienst $SERVICE nicht aktiv"
  exit 10
fi

if ! need_cmd curl; then
  log "check-runtime-deploy-gate: curl fehlt"
  exit 11
fi
if ! need_cmd python3; then
  log "check-runtime-deploy-gate: python3 fehlt"
  exit 20
fi
if [[ ! -f "$EVAL_PY" ]]; then
  log "check-runtime-deploy-gate: $EVAL_PY fehlt"
  exit 20
fi

tmp_api="$(mktemp)"
tmp_health="$(mktemp)"
tmp_dd="$(mktemp)"
trap 'rm -f "$tmp_api" "$tmp_health" "$tmp_dd"' EXIT

# Nach systemctl restart: kurz active/ss, aber Uvicorn noch nicht bereit (curl 7).
API_RETRIES="${RUNTIME_GATE_API_RETRIES:-8}"
API_SLEEP="${RUNTIME_GATE_API_SLEEP_SEC:-1}"

http_code="000"
http_kind="unreachable"
port_8000_open=0
if need_cmd ss && ss -ltn 2>/dev/null | grep -Eq '127\.0\.0\.1:8000|:8000'; then
  port_8000_open=1
fi
health_code="000"
health_kind="unreachable"
for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  probe_http_code "${BASE_URL}/health" "$tmp_health" health_code health_kind
  if [[ "$health_code" == "200" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  probe_http_code "${BASE_URL}/api/version" "$tmp_api" http_code http_kind
  if [[ "$http_code" != "000" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

if [[ "$port_8000_open" -eq 1 ]] && [[ "$health_code" == "200" ]] && [[ "$http_kind" == "timeout" ]]; then
  log "check-runtime-deploy-gate: backend_version_endpoint_timeout (health=ok api_version=$http_kind)"
  exit 18
fi
if [[ "$port_8000_open" -eq 1 ]] && [[ "$health_kind" == "timeout" ]]; then
  log "check-runtime-deploy-gate: backend_hanging_active_port_but_http_timeout (health=$health_kind api_version=$http_kind)"
  exit 17
fi
if [[ "$port_8000_open" -eq 1 ]] && [[ "$http_kind" == "timeout" ]]; then
  log "check-runtime-deploy-gate: backend_hanging_active_port_but_http_timeout (health=$health_kind api_version=$http_kind)"
  exit 17
fi

if [[ "$http_code" == "000" ]]; then
  log "check-runtime-deploy-gate: /api/version nicht erreichbar (${http_kind}; nach ${API_RETRIES} Versuchen; health=${health_kind}; ggf. Dienst-Log: journalctl -u $SERVICE -n 30)"
  exit 11
fi
if [[ "$health_code" != "200" ]]; then
  log "check-runtime-deploy-gate: /health HTTP ${health_code} (${health_kind})"
  exit 11
fi
if [[ "$http_code" != "200" ]]; then
  log "check-runtime-deploy-gate: /api/version HTTP $http_code"
  exit 11
fi

skip_dd="${RUNTIME_GATE_SKIP_DEPLOY_DRIFT:-}"
if [[ "$skip_dd" == "1" ]]; then
  set +e
  python3 "$EVAL_PY" --api-version-file "$tmp_api" --workspace-version-file "$WS_VER" --skip-deploy-drift
  ec=$?
  set -e
  if [[ "$ec" -eq 0 ]]; then
    log "check-runtime-deploy-gate: OK (Version/Pfad; deploy_drift uebersprungen)"
    exit 0
  fi
  log "check-runtime-deploy-gate: Evaluator Exit $ec (nicht bestanden)"
  exit "$ec"
fi

http_dd="000"
for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  http_dd="$(curl -sS -o "$tmp_dd" -w '%{http_code}' --connect-timeout 2 --max-time 12 "${BASE_URL}/api/dev-dashboard/status" 2>/dev/null || echo 000)"
  if [[ "$http_dd" == "200" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done
if [[ "$http_dd" != "200" ]]; then
  log "check-runtime-deploy-gate: /api/dev-dashboard/status HTTP $http_dd (oder nicht erreichbar)"
  exit 20
fi

allow_gray=0
[[ "${RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY:-}" == "1" ]] && allow_gray=1
py_args=(--api-version-file "$tmp_api" --workspace-version-file "$WS_VER" --dev-dashboard-file "$tmp_dd")
[[ "$allow_gray" == "1" ]] && py_args+=(--allow-gray)

set +e
python3 "$EVAL_PY" "${py_args[@]}"
ec=$?
set -e
if [[ "$ec" -eq 0 ]]; then
  log "check-runtime-deploy-gate: OK (Version, Pfad, deploy_drift/Manifest)"
  exit 0
fi
log "check-runtime-deploy-gate: Evaluator Exit $ec (nicht bestanden)"
exit "$ec"
