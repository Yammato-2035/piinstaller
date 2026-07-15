#!/usr/bin/env bash
# 001D7C — Late journal harvest unit/script present.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO/scripts/rescue-live/image/setuphelfer-rescue-late-journal-harvest"
UNIT="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-late-journal-harvest.service"
PATHU="$REPO/scripts/rescue-live/image/systemd/setuphelfer-rescue-late-journal-harvest.path"
CORE="$REPO/backend/core/rescue_discovery_boot_completion.py"

fail=0
for f in "$SCRIPT" "$UNIT" "$PATHU" "$CORE"; do
  [[ -f "$f" ]] || { echo "MISSING $f"; fail=1; }
done
grep -q 'harvest_late_journal' "$SCRIPT" || { echo "script missing harvest"; fail=1; }
grep -q 'late-journal.redacted.log' "$CORE" || { echo "core missing late journal path"; fail=1; }
grep -q 'ExecStart=/usr/local/sbin/setuphelfer-rescue-late-journal-harvest' "$UNIT" || fail=1
grep -q 'PathExists=/run/setuphelfer-rescue/auto-msi-evidence.done' "$PATHU" || fail=1
if grep -q 'StandardOutput=tty\|TTYPath=/dev/tty' "$UNIT"; then
  echo "late-journal must not use tty"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "check-rescue-late-journal-unit: FAILED"
  exit 1
fi
echo "check-rescue-late-journal-unit: OK"
exit 0
