#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MENU="${REPO_ROOT}/scripts/rescue-live/setuphelfer-rescue-network-menu.sh"
fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$MENU" ]] || fail "missing network menu"
bash -n "$MENU" || fail "bash -n menu"

grep -q 'read -r -s' "$MENU" || fail "missing silent password read"
grep -q 'nicht geloggt' "$MENU" || fail "missing no-log hint"
grep -q 'apt' "$MENU" && grep -q 'kein apt' "$MENU" || fail "missing apt refusal message"

# logger line must not echo password variables
if grep -E 'logger.*wifi_pass|logger.*PAIRING_TOKEN|logger.*token' "$MENU"; then
  fail "logger may leak secrets"
fi

echo "OK: rescue network menu no secret logging v1"
