#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D4 — Stage short-lived lab token onto SETUP_LOGS (no secret output).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
TOKEN_SRC="${SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE:-$HOME/.config/setuphelfer/rescue/telemetry-lab-token}"
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    --token-source) TOKEN_SRC="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] [--token-source PATH] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$TOKEN_SRC" ]] || { echo "STOP — live_telemetry_token_unavailable" >&2; exit 17; }

if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /run/media/*/SETUP_LOGS; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi

[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }
[[ "$EXECUTE" == true ]] || {
  python3 - <<PY
import json
print(json.dumps({"token_source_present": True, "token_staged": False, "token_value_logged": False, "plan_only": True}))
PY
  exit 0
}

DEST="${SETUP_LOGS}/setuphelfer/lab/telemetry-lab-token"
mkdir -p "$(dirname "$DEST")"
install -m 0600 "$TOKEN_SRC" "$DEST"
python3 - <<'PY'
import json
print(json.dumps({"token_source_present": True, "token_staged": True, "token_value_logged": False}))
PY
