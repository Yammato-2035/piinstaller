#!/usr/bin/env bash
# Static: developer-qemu bootloader serial + auto-boot in prepare script (no lb build).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PREP="${REPO_ROOT}/scripts/rescue-live/prepare-controlled-live-build-tree.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[[ -f "$PREP" ]] || fail "missing prepare script"
bash -n "$PREP" || fail "bash -n prepare"

grep -q 'write_developer_qemu_isolinux_serial_config' "$PREP" \
  || fail "missing write_developer_qemu_isolinux_serial_config"
grep -q 'write_developer_qemu_grub_serial_hook' "$PREP" \
  || fail "missing write_developer_qemu_grub_serial_hook"

grep -q 'SERIAL 0 115200' "$PREP" || fail "missing ISOLINUX SERIAL 0 115200"
grep -q 'CONSOLE 0' "$PREP" || fail "missing ISOLINUX CONSOLE 0"
grep -q 'TIMEOUT 30' "$PREP" || fail "missing ISOLINUX TIMEOUT 30"
grep -q 'DEFAULT live-' "$PREP" || fail "missing ISOLINUX DEFAULT live-"
grep -q 'ONTIMEOUT live-' "$PREP" || fail "missing ISOLINUX ONTIMEOUT live-"

grep -q 'serial --unit=0 --speed=115200' "$PREP" || fail "missing GRUB serial --unit=0"
grep -q 'terminal_input serial console' "$PREP" || fail "missing GRUB terminal_input serial console"
grep -q 'terminal_output serial console' "$PREP" || fail "missing GRUB terminal_output serial console"
grep -q 'set timeout=3' "$PREP" || fail "missing GRUB set timeout=3"

# developer-qemu branch invokes bootloader helpers
grep -q 'write_developer_qemu_isolinux_serial_config' "$PREP" \
  || fail "isolinux helper not referenced"
python3 - "$PREP" <<'PY' || exit 1
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(
    r"  write_developer_qemu_isolinux_serial_config\n.*?LIVE_BOOTAPPEND='([^']+)'",
    text,
    re.S,
)
if not m:
    raise SystemExit("developer-qemu bootloader/cmdline block not found")
body = m.group(0)
for needle in (
    "write_developer_qemu_grub_serial_hook",
    "console=tty0",
    "console=ttyS0,115200n8",
):
    if needle not in body:
        raise SystemExit(f"missing in developer-qemu block: {needle}")
matches = [m.group(1)]
if not matches:
    raise SystemExit("LIVE_BOOTAPPEND assignment not found in developer-qemu block")
append = matches[-1]
if "console=ttyS0,115200n8" not in append:
    raise SystemExit("developer-qemu LIVE_BOOTAPPEND missing console=ttyS0,115200n8")
import re as _re
if _re.search(r"(?:^|\s)quiet(?:\s|$)", append):
    raise SystemExit("quiet in developer-qemu LIVE_BOOTAPPEND")
if _re.search(r"(?:^|\s)splash(?:\s|$)", append):
    raise SystemExit("splash in developer-qemu LIVE_BOOTAPPEND")
PY

echo "OK: rescue bootloader serial config v1"
