#!/usr/bin/env bash
# 001D7C — tty1 guard present; no root getty on tty1 in rescue units.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
GUARD="$REPO/scripts/rescue-live/image/setuphelfer-rescue-tui-guard"
UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-guard.service"
TIMER="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui-guard.timer"
TUI_UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-tui.service"
IMG="$REPO/scripts/rescue-live/image/systemd"

fail=0
for f in "$GUARD" "$UNIT" "$TIMER" "$TUI_UNIT"; do
  [[ -f "$f" ]] || { echo "MISSING $f"; fail=1; }
done
grep -q 'setuphelfer-rescue-tui.service' "$GUARD" || fail=1
grep -q 'StartLimitBurst=3' "$TUI_UNIT" || { echo "tui missing StartLimitBurst"; fail=1; }
grep -q 'Restart=on-failure' "$TUI_UNIT" || fail=1

# No root getty enabled on tty1 (Before=getty@tty1 for ordering is OK).
if rg -n '^(ExecStart=.*agetty.*tty1|ExecStart=.*getty@tty1)' "$IMG" 2>/dev/null \
  || rg -n 'WantedBy=.*getty@tty1|getty@tty1\.service$' "$IMG" --glob '!**/setuphelfer-rescue-boot-progress.service' 2>/dev/null; then
  # Narrow: only ExecStart that launches agetty on tty1
  if rg -n 'ExecStart=.*agetty.*tty1|ExecStart=/sbin/getty.*tty1|ExecStart=/usr/sbin/getty.*tty1' "$IMG" 2>/dev/null; then
    echo "forbidden bare getty on tty1 in rescue image units"
    fail=1
  fi
fi

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-tty1-guard: FAILED"
  exit 1
fi
echo "check-rescue-tty1-guard: OK"
exit 0
