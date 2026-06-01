#!/usr/bin/env bash
# Static: QEMU developer smoke uses chardev+isa-serial by default (no VM start).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WRAPPER="${REPO_ROOT}/scripts/rescue-live/run-qemu-developer-iso-smoke.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[[ -f "$WRAPPER" ]] || fail "missing wrapper: $WRAPPER"
bash -n "$WRAPPER" || fail "bash -n wrapper"

grep -q 'SERIAL_BACKEND="${SETUPHELFER_QEMU_SERIAL_BACKEND:-chardev}"' "$WRAPPER" \
  || fail "default serial backend is not chardev"
grep -q 'append_qemu_serial_capture_args' "$WRAPPER" || fail "missing append_qemu_serial_capture_args"
grep -q 'charserial0' "$WRAPPER" || fail "missing chardev id=charserial0"
grep -q 'isa-serial' "$WRAPPER" || fail "missing isa-serial device"
grep -q 'chardev=charserial0' "$WRAPPER" || fail "missing chardev=charserial0 on isa-serial"
grep -q 'prepare_serial_log' "$WRAPPER" || fail "missing prepare_serial_log"
grep -q -- '--serial-backend' "$WRAPPER" || fail "missing --serial-backend flag"

# Legacy -serial file only on explicit legacy-file branch, not as unconditional default.
if grep -qE '^[[:space:]]*-serial "file:\$\{SERIAL_LOG\}"' "$WRAPPER"; then
  fail "unconditional -serial file: still present (legacy must be behind legacy-file only)"
fi

grep -q 'legacy-file' "$WRAPPER" || fail "legacy-file backend option missing"

echo "OK: qemu serial capture args v1"
