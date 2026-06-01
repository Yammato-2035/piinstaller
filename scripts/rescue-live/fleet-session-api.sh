#!/usr/bin/env bash
# Local lab fleet session API client + JSONL fallback (no control actions).
set -euo pipefail

API_BASE="${SETUPHELFER_FLEET_SESSION_API:-http://127.0.0.1:8000}"
REPO_ROOT="${SETUPHELFER_FLEET_SESSION_REPO_ROOT:-}"
JSONL_FALLBACK="${SETUPHELFER_FLEET_SESSION_JSONL:-}"
FLEET_JSON_ERROR_LOG="${SETUPHELFER_FLEET_JSON_ERROR_LOG:-}"

if [[ -z "$REPO_ROOT" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
if [[ -z "$JSONL_FALLBACK" ]]; then
  JSONL_FALLBACK="${REPO_ROOT}/docs/evidence/runtime-results/dev-dashboard/fleet_sessions.jsonl"
fi

_fleet_log_json_error() {
  local msg="$1"
  [[ -n "$FLEET_JSON_ERROR_LOG" ]] || return 0
  mkdir -p "$(dirname "$FLEET_JSON_ERROR_LOG")"
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" >>"$FLEET_JSON_ERROR_LOG"
}

fleet_validate_json() {
  local payload="$1"
  printf '%s' "$payload" | python3 -m json.tool >/dev/null 2>&1
}

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

fleet_post_json() {
  local session_id="$1" action="$2" payload="$3"
  if ! fleet_validate_json "$payload"; then
    _fleet_log_json_error "wrapper_json_invalid action=${action} session_id=${session_id}"
    return 1
  fi
  _fleet_curl POST "/api/fleet/sessions/${session_id}/${action}" "$payload"
}

# --- Payload builders (ENV → Python heredoc → valid JSON) ---

fleet_session_create_payload() {
  export FLEET_RUN_ID="${1:?run_id}"
  export FLEET_ISO_PATH="${2:-}"
  export FLEET_PROXY_PORT="${3:-8001}"
  export FLEET_TIMEOUT_SECONDS="${4:-900}"
  export FLEET_HAS_KVM="${5:-false}"
  export FLEET_SESSION_TYPE="${6:-local_qemu_smoke}"
  export FLEET_LABEL="${7:-QEMU Developer ISO Smoke}"
  export FLEET_EVIDENCE_SUBPATH="${8:-}"
  python3 <<'PY'
import json
import os

run_id = os.environ["FLEET_RUN_ID"]
evdir = os.environ.get("FLEET_EVIDENCE_SUBPATH", "")
paths = [evdir] if evdir else []

def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default

print(
    json.dumps(
        {
            "run_id": run_id,
            "session_id": f"fleet-{run_id}",
            "session_type": os.environ.get("FLEET_SESSION_TYPE", "local_qemu_smoke"),
            "status": "starting",
            "label": os.environ.get("FLEET_LABEL", "QEMU Developer ISO Smoke"),
            "host": {
                "has_kvm": env_bool("FLEET_HAS_KVM", False),
                "kvm_enabled": False,
            },
            "qemu": {
                "iso_path": os.environ.get("FLEET_ISO_PATH", ""),
                "proxy_port": int(os.environ.get("FLEET_PROXY_PORT", "8001")),
                "timeout_seconds": int(os.environ.get("FLEET_TIMEOUT_SECONDS", "900")),
                "acceleration": "unknown",
            },
            "evidence_paths": paths,
        },
        ensure_ascii=False,
    )
)
PY
}

fleet_session_heartbeat_payload() {
  export FLEET_HB_STATUS="${1:-}"
  export FLEET_SERIAL_PATH="${2:-}"
  export FLEET_SERIAL_EXISTS="${3:-false}"
  export FLEET_SERIAL_SIZE="${4:-0}"
  export FLEET_QEMU_PID="${5:-}"
  export FLEET_ACCELERATION="${6:-}"
  export FLEET_HAS_KVM="${7:-}"
  export FLEET_KVM_ENABLED="${8:-}"
  export FLEET_FINDINGS_JSON="${9:-[]}"
  python3 <<'PY'
import json
import os

def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default

def env_int(name: str, default=None):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

payload: dict = {}
status = os.environ.get("FLEET_HB_STATUS", "").strip()
if status:
    payload["status"] = status

accel = os.environ.get("FLEET_ACCELERATION", "").strip()
if accel:
    payload.setdefault("qemu", {})["acceleration"] = accel

pid = env_int("FLEET_QEMU_PID", None)
if pid is not None:
    payload.setdefault("qemu", {})["pid"] = pid

if os.environ.get("FLEET_HAS_KVM") or os.environ.get("FLEET_KVM_ENABLED"):
    payload.setdefault("host", {})
    if os.environ.get("FLEET_HAS_KVM"):
        payload["host"]["has_kvm"] = env_bool("FLEET_HAS_KVM", False)
    if os.environ.get("FLEET_KVM_ENABLED"):
        payload["host"]["kvm_enabled"] = env_bool("FLEET_KVM_ENABLED", False)

serial_path = os.environ.get("FLEET_SERIAL_PATH", "")
if serial_path or os.environ.get("FLEET_SERIAL_EXISTS") or os.environ.get("FLEET_SERIAL_SIZE"):
    payload["serial"] = {
        "path": serial_path,
        "exists": env_bool("FLEET_SERIAL_EXISTS", False),
        "size_bytes": env_int("FLEET_SERIAL_SIZE", 0) or 0,
    }

findings_raw = os.environ.get("FLEET_FINDINGS_JSON", "[]")
try:
    findings = json.loads(findings_raw)
    if isinstance(findings, list) and findings:
        payload["findings"] = findings
except json.JSONDecodeError:
    pass

print(json.dumps(payload, ensure_ascii=False))
PY
}

fleet_session_finish_payload() {
  export FLEET_FINISH_STATUS="${1:?status}"
  export FLEET_QEMU_EXIT_CODE="${2:-0}"
  export FLEET_GUEST_REPORT_SEEN="${3:-false}"
  export FLEET_DEV_SERVER_REPORT_NEW="${4:-false}"
  export FLEET_SERIAL_SIZE="${5:-0}"
  export FLEET_FINDINGS_JSON="${6:-[]}"
  python3 <<'PY'
import json
import os

def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return True
    if v in {"0", "false", "no", "off"}:
        return False
    return default

status = os.environ.get("FLEET_FINISH_STATUS", "failed")
qemu_exit = int(os.environ.get("FLEET_QEMU_EXIT_CODE", "0") or "0")
findings: list[str] = []
try:
    findings = list(json.loads(os.environ.get("FLEET_FINDINGS_JSON", "[]")))
except json.JSONDecodeError:
    findings = []

if qemu_exit == 124:
    status = "timeout"
    if "qemu_timeout_124" not in findings:
        findings.append("qemu_timeout_124")

serial_size = int(os.environ.get("FLEET_SERIAL_SIZE", "0") or "0")
if serial_size == 0 and "serial_empty" not in findings:
    findings.append("serial_empty")

guest_seen = env_bool("FLEET_GUEST_REPORT_SEEN", False)
if not guest_seen and "guest_report_missing" not in findings:
    findings.append("guest_report_missing")

payload = {
    "status": status,
    "qemu_exit_code": qemu_exit,
    "guest": {
        "report_seen": guest_seen,
        "dev_server_report_new": env_bool("FLEET_DEV_SERVER_REPORT_NEW", False),
    },
    "serial": {"size_bytes": serial_size},
    "findings": findings,
    "evidence_paths": [],
}
print(json.dumps(payload, ensure_ascii=False))
PY
}

fleet_session_patch_simple() {
  local status="$1"
  fleet_session_heartbeat_payload "$status" "" "false" "0" "" "" "" "" "[]"
}

fleet_session_create() {
  local payload="$1"
  local resp
  if ! fleet_validate_json "$payload"; then
    _fleet_log_json_error "wrapper_json_invalid action=create"
    printf '{"code":"FLEET_SESSION_BLOCKED_INVALID_PAYLOAD","errors":["wrapper_json_invalid"]}\n'
    return 1
  fi
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
  local session_id="$1" action="$2" payload="${3:-{}}"
  local resp
  if ! fleet_validate_json "$payload"; then
    _fleet_log_json_error "wrapper_json_invalid action=${action} session_id=${session_id}"
    return 1
  fi
  resp="$(_fleet_curl POST "/api/fleet/sessions/${session_id}/${action}" "$payload" || true)"
  if [[ -n "$resp" ]] && printf '%s' "$resp" | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
    printf '%s' "$resp"
    return 0
  fi
  export FLEET_FB_SESSION_ID="$session_id" FLEET_FB_ACTION="$action" FLEET_FB_PAYLOAD="$payload"
  _fleet_fallback_append "$(python3 <<'PY'
import json
import os
print(
    json.dumps(
        {
            "session_id": os.environ["FLEET_FB_SESSION_ID"],
            "action": os.environ["FLEET_FB_ACTION"],
            "patch": json.loads(os.environ["FLEET_FB_PAYLOAD"]),
        },
        ensure_ascii=False,
    )
)
PY
)"
  printf '{"code":"FLEET_SESSION_%s_FALLBACK"}\n' "$(echo "$action" | tr '[:lower:]' '[:upper:]')"
}

fleet_session_parse_id() {
  local resp="$1"
  printf '%s' "$resp" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("session") or {}).get("session_id") or d.get("session_id",""))' 2>/dev/null || true
}
