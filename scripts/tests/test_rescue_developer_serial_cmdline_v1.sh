#!/usr/bin/env bash
# Static checks: developer-qemu serial boot visibility (no VM, no ISO build).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PREP="${REPO_ROOT}/scripts/rescue-live/prepare-controlled-live-build-tree.sh"
PROFILE="${REPO_ROOT}/build/rescue/profiles/developer-qemu"
AUTOPILOT_SH="${PROFILE}/includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh"
MARKER_SH="${PROFILE}/includes.chroot/usr/local/sbin/setuphelfer-serial-boot-markers.sh"
FLEET_API="${REPO_ROOT}/scripts/rescue-live/fleet-session-api.sh"
QEMU_WRAPPER="${REPO_ROOT}/scripts/rescue-live/run-qemu-developer-iso-smoke.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

grep -q 'RESCUE_BUILD_PROFILE.*developer-qemu' "$PREP" || fail "prepare missing developer-qemu profile branch"

extract_qemu_append() {
  python3 - "$PREP" <<'PY'
import re
import sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(
    r'if \[\[ "\$\{RESCUE_BUILD_PROFILE\}" == "developer-qemu" \]\]; then\n'
    r"(?:  #.*\n)?  LIVE_BOOTAPPEND='([^']+)'\nfi\n\nwrite_text_file \"\$\{BUILD_ROOT\}/auto/config\"",
    text,
)
if not m:
    raise SystemExit(1)
print(m.group(1))
PY
}

APPEND="$(extract_qemu_append)"
[[ -n "$APPEND" ]] || fail "could not extract developer-qemu LIVE_BOOTAPPEND"

echo "$APPEND" | grep -q 'console=tty0' || fail "missing console=tty0"
echo "$APPEND" | grep -q 'console=ttyS0,115200n8' || fail "missing console=ttyS0,115200n8"
echo "$APPEND" | grep -q 'loglevel=7' || fail "missing loglevel=7"
echo "$APPEND" | grep -Eq 'systemd\.log_level=debug' || fail "missing systemd.log_level=debug"
echo "$APPEND" | grep -q 'quiet' && fail "quiet still in developer-qemu append"
echo "$APPEND" | grep -q 'splash' && fail "splash still in developer-qemu append"

for marker in \
  SETUPHELFER_BOOT_MARKER_START \
  SETUPHELFER_SYSTEMD_MARKER_START \
  SETUPHELFER_AUTOPILOT_START \
  SETUPHELFER_DEVSERVER_AGENT_START \
  SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT; do
  grep -q "$marker" "$MARKER_SH" "$AUTOPILOT_SH" 2>/dev/null || fail "missing marker $marker"
done

grep -q 'FLEET_SERIAL_PATH' "$FLEET_API" || fail "finish payload missing serial path"
grep -q 'classification_hint_serial_empty_boot_unknown' "$FLEET_API" || fail "finish missing classification hint"
grep -q 'FLEET_ACCELERATION' "$QEMU_WRAPPER" || fail "wrapper missing acceleration export on finish"

bash -n "$PREP" "$FLEET_API" "$QEMU_WRAPPER" "$AUTOPILOT_SH" "$MARKER_SH"

echo "OK: rescue developer serial cmdline v1"
