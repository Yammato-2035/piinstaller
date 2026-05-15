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
tmp_dd="$(mktemp)"
trap 'rm -f "$tmp_api" "$tmp_dd"' EXIT

# Nach systemctl restart: kurz active/ss, aber Uvicorn noch nicht bereit (curl 7).
API_RETRIES="${RUNTIME_GATE_API_RETRIES:-8}"
API_SLEEP="${RUNTIME_GATE_API_SLEEP_SEC:-1}"

http_code="000"
for ((attempt = 1; attempt <= API_RETRIES; attempt++)); do
  http_code="$(curl -sS -o "$tmp_api" -w '%{http_code}' --connect-timeout 2 --max-time 8 "${BASE_URL}/api/version" 2>/dev/null || echo 000)"
  if [[ "$http_code" != "000" ]]; then
    break
  fi
  if [[ "$attempt" -lt "$API_RETRIES" ]]; then
    sleep "$API_SLEEP"
  fi
done

if [[ "$http_code" == "000" ]]; then
  log "check-runtime-deploy-gate: /api/version nicht erreichbar (nach ${API_RETRIES} Versuchen; ggf. Dienst-Log: journalctl -u $SERVICE -n 30)"
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
