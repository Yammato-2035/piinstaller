#!/usr/bin/env bash
# Rescue live temp runtime — read-only local-only checks (no writes).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESCUE_ROOT="${SETUPHELFER_RESCUE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
DIST="$RESCUE_ROOT/frontend/dist"
BACKEND_URL="${VERIFY_BACKEND_URL:-http://127.0.0.1:8000}"
UI_URL="${VERIFY_FRONTEND_URL:-http://127.0.0.1:3001}"
FAILED=0

_fail() { echo "FAIL: $*" >&2; FAILED=1; }
_ok() { echo "OK:   $*"; }

echo "=== rescue-live check-localonly ==="
echo "RESCUE_ROOT=$RESCUE_ROOT"

if command -v ss >/dev/null 2>&1; then
  echo "--- ss (8000/3001 listeners) ---"
  ss -ltnp 2>/dev/null | grep -E ':8000|:3001' || true
  if ss -ltnp 2>/dev/null | grep -E ':8000' | grep -qv '127.0.0.1:8000'; then
    _fail "backend listener not restricted to 127.0.0.1:8000"
  elif ss -ltnp 2>/dev/null | grep -qE '127\.0\.0\.1:8000'; then
    _ok "backend listens on 127.0.0.1:8000"
  else
    _fail "no listener on 127.0.0.1:8000"
  fi
  if ss -ltnp 2>/dev/null | grep -E ':3001' | grep -qv '127.0.0.1:3001'; then
    _fail "UI listener not restricted to 127.0.0.1:3001"
  elif ss -ltnp 2>/dev/null | grep -qE '127\.0\.0\.1:3001'; then
    _ok "UI listens on 127.0.0.1:3001"
  else
    _fail "no listener on 127.0.0.1:3001"
  fi
else
  echo "WARN: ss not available"
fi

if command -v curl >/dev/null 2>&1; then
  if curl -sf --max-time 5 "${BACKEND_URL%/}/api/version" >/dev/null; then
    _ok "curl ${BACKEND_URL%/}/api/version"
  else
    _fail "curl ${BACKEND_URL%/}/api/version"
  fi
  if curl -sfI --max-time 5 "$UI_URL/" | head -1 | grep -qE '200|301|302|304'; then
    _ok "curl -I $UI_URL/"
  else
    _fail "curl -I $UI_URL/"
  fi
else
  _fail "curl not available"
fi

if [[ -f "$DIST/index.html" ]]; then
  if grep -qE 'fonts\.googleapis\.com|fonts\.gstatic\.com' "$DIST/index.html"; then
    _fail "Google Fonts CDN in frontend/dist/index.html"
  else
    _ok "no Google Fonts CDN in frontend/dist/index.html"
  fi
else
  _fail "missing $DIST/index.html"
fi

if [[ "$FAILED" -ne 0 ]]; then
  echo "=== RESULT: FAIL ==="
  exit 1
fi
echo "=== RESULT: PASS ==="
exit 0
