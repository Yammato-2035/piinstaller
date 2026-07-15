#!/usr/bin/env bash
# 001D7C — Discovery runner + outermost exception boundary present.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUNNER="$REPO/scripts/rescue-live/image/setuphelfer-rescue-auto-discovery-runner"
ORCH="$REPO/backend/core/rescue_auto_discovery_orchestrator.py"
UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-discovery.service"

fail=0
[[ -f "$RUNNER" ]] || { echo "MISSING runner"; fail=1; }
grep -q 'persist_service_start' "$RUNNER" || { echo "runner missing persist_service_start"; fail=1; }
grep -q 'ExecStart=/usr/local/sbin/setuphelfer-rescue-auto-discovery-runner' "$UNIT" || {
  echo "unit not using runner"
  fail=1
}
grep -q 'Restart=no' "$UNIT" || { echo "discovery Restart must be no"; fail=1; }
grep -q 'except BaseException' "$ORCH" || { echo "missing outer BaseException boundary"; fail=1; }
grep -q 'persist_orchestrator_exit' "$ORCH" || { echo "missing persist_orchestrator_exit"; fail=1; }
grep -E -q '\.sh' <<<"$(grep ExecStart "$UNIT" || true)" && {
  echo "ExecStart must not use .sh suffix"
  fail=1
}

# No TTY for discovery background service
if grep -q 'StandardOutput=tty\|TTYPath=/dev/tty' "$UNIT"; then
  echo "discovery unit must not own tty"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-discovery-runner: FAILED"
  exit 1
fi
echo "check-rescue-discovery-runner: OK"
exit 0
