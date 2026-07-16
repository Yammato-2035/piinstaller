#!/usr/bin/env bash
# 001D7C/001D7D — tty1 guard must be non-blocking; hold screen owns tty1.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
GUARD="$REPO/scripts/rescue-live/image/setuphelfer-rescue-tui-guard"
UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-guard.service"
TIMER="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-guard.timer"
HOLD_UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-hold.service"
TUI_UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service"
IMG="$REPO/scripts/rescue-live/image/systemd"

fail=0
for f in "$GUARD" "$UNIT" "$TIMER" "$HOLD_UNIT" "$TUI_UNIT"; do
  [[ -f "$f" ]] || { echo "MISSING $f"; fail=1; }
done
grep -q 'setuphelfer-rescue-tui.service' "$GUARD" || fail=1
grep -q 'setuphelfer-rescue-tui-hold.service' "$GUARD" || fail=1
grep -q 'TimeoutStartSec=' "$UNIT" || { echo "guard missing TimeoutStartSec"; fail=1; }
grep -q 'setuphelfer-rescue-tui-hold' "$GUARD" || fail=1
if grep -q 'setuphelfer-rescue-tui-hold --static-error' "$GUARD"; then
  echo "guard must not exec hold inline (blocks oneshot)"
  fail=1
fi
grep -q 'TTYPath=/dev/tty1' "$HOLD_UNIT" || { echo "hold unit must own tty1"; fail=1; }
grep -q 'OnUnitInactiveSec=' "$TIMER" || { echo "timer should use OnUnitInactiveSec"; fail=1; }
grep -q 'StartLimitBurst=3' "$TUI_UNIT" || { echo "tui missing StartLimitBurst"; fail=1; }
grep -q 'Restart=on-failure' "$TUI_UNIT" || fail=1

if rg -n 'ExecStart=.*agetty.*tty1|ExecStart=/sbin/getty.*tty1' "$IMG" 2>/dev/null; then
  echo "forbidden bare getty on tty1 in rescue image units"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-tty1-guard: FAILED"
  exit 1
fi
echo "check-rescue-tty1-guard: OK"
exit 0
