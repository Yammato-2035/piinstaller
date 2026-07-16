#!/usr/bin/env bash
# 001D7E — SETUP_LOGS resolution / canonical mount gates.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
fail=0

check() {
  local file="$1" pattern="$2" msg="$3"
  if ! grep -F -q -- "$pattern" "$file"; then
    echo "FAIL: $msg"
    fail=1
  fi
}

RESOLVER_PY="$REPO/backend/core/rescue_setup_logs_resolver.py"
RESOLVER_SH="$REPO/scripts/rescue-live/image/setuphelfer-rescue-resolve-setup-logs"
RESOLVER_UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-setup-logs-resolver.service"
OBSERVER="$REPO/scripts/rescue-live/image/setuphelfer-rescue-boot-observer"
OBSERVER_UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-boot-observer.service"
IMPORT="$REPO/scripts/run-e2e-live-001d-dev-automation.sh"

for f in "$RESOLVER_PY" "$RESOLVER_SH" "$RESOLVER_UNIT" "$OBSERVER" "$OBSERVER_UNIT" "$IMPORT"; do
  [[ -f "$f" ]] || { echo "MISSING $f"; fail=1; }
done

check "$RESOLVER_PY" 'CANONICAL_MOUNT' "canonical mount missing"
check "$RESOLVER_PY" 'shadow_directory' "shadow rejection missing"
check "$RESOLVER_UNIT" 'Before=setuphelfer-rescue-boot-observer.service' "resolver before observer"
check "$OBSERVER_UNIT" 'EnvironmentFile=-/run/setuphelfer-rescue/environment' "observer envfile"
check "$IMPORT" '--mode' "import mode flag missing"
check "$IMPORT" 'auto-discovery' "auto-discovery mode missing"
check "$IMPORT" 'select_setup_logs_for_import' "import mount selection missing"

# Must not hardcode /media/volker in live payload scripts
if rg -n '/media/volker/SETUP_LOGS' "$RESOLVER_SH" "$OBSERVER" "$RESOLVER_PY" 2>/dev/null | grep -v 'shadow\|ignored\|example\|test'; then
  echo "FAIL: hard-coded /media/volker path in live resolver path"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "setup_logs_resolution_gate: FAILED"
  exit 1
fi
echo "setup_logs_resolution_gate=passed"
echo "canonical_mount_gate=passed"
echo "observer_persistence_gate=passed"
echo "import_mode_gate=passed"
exit 0
