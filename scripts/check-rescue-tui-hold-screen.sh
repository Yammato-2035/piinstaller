#!/usr/bin/env bash
# 001D7C — TUI hold screen: display exit must not leave bare tty1.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TUI="$REPO/scripts/rescue-live/image/setuphelfer-rescue-tui.sh"
HOLD="$REPO/scripts/rescue-live/image/setuphelfer-rescue-tui-hold"
DISPLAY="$REPO/scripts/rescue-live/image/setuphelfer-rescue-auto-e2e-tui-display.py"

fail=0
[[ -f "$TUI" && -f "$HOLD" && -f "$DISPLAY" ]] || { echo "MISSING tui/hold/display"; fail=1; }
grep -q '_tui_discovery_hold_needed\|_setuphelfer-rescue-tui-hold' "$TUI" || {
  echo "tui missing hold integration"
  fail=1
}
grep -q 'shutdown_pending\|_tui_shutdown_pending' "$TUI" || {
  echo "tui missing shutdown_pending gate"
  fail=1
}
# Must not unconditionally exit after a single display run without loop/hold.
if ! grep -q 'while true' "$TUI"; then
  echo "tui auto menu must loop"
  fail=1
fi
grep -q 'Fehler-Halteansicht\|Automatische Systemerkundung konnte nicht gestartet' "$HOLD" || {
  echo "hold screen missing German failure copy"
  fail=1
}
grep -q 'discovery_mode' "$DISPLAY" || fail=1
grep -q 'status") == "failed"' "$DISPLAY" || grep -q "terminal == \"failed\"" "$DISPLAY" || {
  echo "display must exit on discovery failed for hold handoff"
  fail=1
}

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-tui-hold-screen: FAILED"
  exit 1
fi
echo "check-rescue-tui-hold-screen: OK"
exit 0
