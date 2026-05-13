#!/usr/bin/env bash
# Backend-Version-Gate: nur lesend. Kein Install, kein Restart, kein Backup.
# Exit: 0 grün | 10 Dienst inaktiv | 11 /api/version nicht erreichbar |
#       12 /api/version HTTP != 200 | 13 Produktiv-config ungültig |
#       14 Workspace/API project_version drift | 15 Produktivdateien fehlen |
#       16 Update erforderlich (API-Fehlercode) | 20 unklar

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"
BASE_URL="${SETUPHELFER_VERSION_URL:-http://127.0.0.1:8000}"
OPT_ROOT="${SETUPHELFER_OPT_ROOT:-/opt/setuphelfer}"
WS_VER="${BACKEND_GATE_WORKSPACE_VERSION_JSON:-$REPO_ROOT/config/version.json}"
OPT_VER="${BACKEND_GATE_OPT_VERSION_JSON:-$OPT_ROOT/config/version.json}"
OPT_APP="$OPT_ROOT/backend/app.py"
OPT_VMOD="$OPT_ROOT/backend/core/versioning.py"

log() { printf '%s\n' "$*" >&2; }

need_cmd() { command -v "$1" >/dev/null 2>&1; }

json_field() {
  python3 -c "import json,sys; p=sys.argv[1]; k=sys.argv[2]; d=json.load(open(p,encoding='utf-8')); v=d.get(k); print('true' if v is True else ('false' if v is False else ('' if v is None else str(v)))))" "$1" "$2" 2>/dev/null || true
}

if ! need_cmd systemctl; then
  log "check-backend-version-gate: systemctl nicht gefunden"
  exit 20
fi

if ! systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
  log "check-backend-version-gate: Dienst $SERVICE nicht aktiv"
  exit 10
fi

if need_cmd ss && ! ss -ltn 2>/dev/null | grep -q ':8000'; then
  log "check-backend-version-gate: Hinweis — nichts lauscht auf TCP 8000 (laut ss)"
fi

if ! need_cmd curl; then
  log "check-backend-version-gate: curl fehlt"
  exit 11
fi

tmp_body="$(mktemp)"
trap 'rm -f "$tmp_body"' EXIT

http_code="000"
http_code="$(curl -sS -o "$tmp_body" -w '%{http_code}' --connect-timeout 2 --max-time 5 "${BASE_URL}/api/version" || true)"

if [[ "$http_code" == "000" ]]; then
  log "check-backend-version-gate: /api/version nicht erreichbar"
  exit 11
fi

if [[ "$http_code" != "200" ]]; then
  log "check-backend-version-gate: /api/version HTTP $http_code"
  exit 12
fi

api_status=""
api_status="$(python3 -c "import json; d=json.load(open('$tmp_body',encoding='utf-8')); print(d.get('status',''))" 2>/dev/null || true)"
if [[ "$api_status" != "success" ]]; then
  api_code="$(python3 -c "import json; d=json.load(open('$tmp_body',encoding='utf-8')); print(d.get('code',''))" 2>/dev/null || true)"
  log "check-backend-version-gate: /api/version status=$api_status code=${api_code:-?}"
  exit 16
fi

if [[ ! -f "$WS_VER" ]]; then
  log "check-backend-version-gate: Workspace $WS_VER fehlt"
  exit 20
fi
ws_truth="$(json_field "$WS_VER" version_source_of_truth)"
if [[ "$ws_truth" != "true" ]]; then
  log "check-backend-version-gate: Workspace version.json ohne version_source_of_truth=true"
  exit 20
fi
ws_pv="$(json_field "$WS_VER" project_version)"

if [[ ! -f "$OPT_APP" ]] || [[ ! -f "$OPT_VMOD" ]]; then
  log "check-backend-version-gate: Produktiv backend-Dateien fehlen (app.py oder core/versioning.py)"
  exit 15
fi

if [[ ! -f "$OPT_VER" ]]; then
  log "check-backend-version-gate: $OPT_VER fehlt"
  exit 13
fi
opt_truth="$(json_field "$OPT_VER" version_source_of_truth)"
if [[ "$opt_truth" != "true" ]]; then
  log "check-backend-version-gate: Produktiv version.json ungültig/legacy (kein version_source_of_truth=true)"
  exit 13
fi

api_pv="$(python3 -c "import json; d=json.load(open('$tmp_body',encoding='utf-8')); print(d.get('project_version',''))" 2>/dev/null || true)"
if [[ -n "$ws_pv" && -n "$api_pv" && "$ws_pv" != "$api_pv" ]]; then
  log "check-backend-version-gate: Drift workspace project_version=$ws_pv api=$api_pv"
  exit 14
fi

if ! grep -q "/api/version" "$OPT_APP" 2>/dev/null; then
  log "check-backend-version-gate: Unerwarteter Inhalt in $OPT_APP (Marker /api/version)"
  exit 20
fi

log "check-backend-version-gate: OK (HTTP 200, status=success, config konsistent)"
exit 0
