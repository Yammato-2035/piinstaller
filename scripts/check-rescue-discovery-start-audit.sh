#!/usr/bin/env bash
# 001D7C — Discovery start-gate audit wiring present in payload sources.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$REPO/backend/core/rescue_auto_discovery_start_gate.py"
OBS="$REPO/backend/core/rescue_discovery_observability.py"
UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-discovery.service"
WRAPPER="$REPO/scripts/rescue-live/image/setuphelfer-rescue-auto-discovery-start-gate"

fail=0
for f in "$GATE" "$OBS" "$UNIT" "$WRAPPER"; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f"
    fail=1
  fi
done
grep -q 'persist_start_gate_audit' "$GATE" || { echo "missing persist_start_gate_audit"; fail=1; }
grep -q '00-start-gate.json' "$OBS" || { echo "missing 00-start-gate.json writer"; fail=1; }
grep -q 'ExecCondition=/usr/local/sbin/setuphelfer-rescue-auto-discovery-start-gate' "$UNIT" || {
  echo "unit missing ExecCondition start-gate"
  fail=1
}
grep -q 'setuphelfer.rescue.discovery-start-gate.v1' "$OBS" || { echo "missing schema"; fail=1; }
[[ -x "$WRAPPER" || -f "$WRAPPER" ]] || fail=1

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-discovery-start-audit: FAILED"
  exit 1
fi
echo "check-rescue-discovery-start-audit: OK"
exit 0
