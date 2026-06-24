#!/usr/bin/env bash
# Capture rescue UI screenshot to SETUP_LOGS (no package install).
set -euo pipefail

LABEL="${1:-ui}"
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
API_BASE="${RESCUE_API_BASE:-http://127.0.0.1:8000}"

payload=$(printf '{"label":"%s"}' "$LABEL")
resp=$(curl -sf -X POST "${API_BASE}/api/rescue/ui/screenshot" \
  -H 'Content-Type: application/json' \
  -d "$payload" 2>/dev/null || true)

if [[ -z "$resp" ]]; then
  echo "blocked: api_unreachable" >&2
  exit 2
fi

status=$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",""))')
path=$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("path") or "")')

printf '%s\n' "$resp"

if [[ "$status" != "ok" ]]; then
  exit 3
fi

if [[ -n "$path" && -f "$path" ]]; then
  echo "screenshot: $path"
  exit 0
fi

exit 4
