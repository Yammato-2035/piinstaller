#!/usr/bin/env bash
# Local lab fleet session API client + JSONL fallback (no control actions).
set -euo pipefail

API_BASE="${SETUPHELFER_FLEET_SESSION_API:-http://127.0.0.1:8000}"
REPO_ROOT="${SETUPHELFER_FLEET_SESSION_REPO_ROOT:-}"
JSONL_FALLBACK="${SETUPHELFER_FLEET_SESSION_JSONL:-}"

if [[ -z "$REPO_ROOT" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
if [[ -z "$JSONL_FALLBACK" ]]; then
  JSONL_FALLBACK="${REPO_ROOT}/docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl"
fi

_fleet_fallback_append() {
  local line="$1"
  mkdir -p "$(dirname "$JSONL_FALLBACK")"
  printf '%s\n' "$line" >>"$JSONL_FALLBACK"
}

_fleet_curl() {
  local method="$1" path="$2" data="${3:-}"
  if [[ -n "$data" ]]; then
    curl -sS -m 5 -X "$method" "${API_BASE}${path}" \
      -H 'Content-Type: application/json' \
      -d "$data" 2>/dev/null || return 1
  else
    curl -sS -m 5 -X "$method" "${API_BASE}${path}" 2>/dev/null || return 1
  fi
}

fleet_session_create() {
  local payload="$1"
  local resp
  resp="$(_fleet_curl POST /api/fleet/sessions "$payload" || true)"
  if [[ -n "$resp" ]] && printf '%s' "$resp" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
    printf '%s' "$resp"
    return 0
  fi
  _fleet_fallback_append "$payload"
  local sid
  sid="$(printf '%s' "$payload" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("session_id") or ("fleet-"+d.get("run_id","")))')"
  printf '{"code":"FLEET_SESSION_CREATED_FALLBACK","session":{"session_id":"%s"}}\n' "$sid"
}

fleet_session_patch() {
  local session_id="$1" action="$2" payload="${3:-\{\}}"
  local resp
  resp="$(_fleet_curl POST "/api/fleet/sessions/${session_id}/${action}" "$payload" || true)"
  if [[ -n "$resp" ]] && printf '%s' "$resp" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
    printf '%s' "$resp"
    return 0
  fi
  _fleet_fallback_append "$(python3 -c "import json; print(json.dumps({'session_id':''${session_id}'','action':''${action}'','patch':json.loads('''${payload}''')}))")"
  printf '{"code":"FLEET_SESSION_%s_FALLBACK"}\n' "$(echo "$action" | tr '[:lower:]' '[:upper:]')"
}
