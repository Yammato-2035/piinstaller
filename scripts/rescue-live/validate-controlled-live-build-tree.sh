#!/usr/bin/env bash
# Validiert controlled live-build-Arbeitsbaum (read-only, kein lb build).
# Exit 0 ok | 10 missing | 11 forbidden artifact | 12 secret | 13 CDN | 14 forbidden token | 20 unknown
set -euo pipefail

BUILD_ROOT="${1:-}"
if [[ -z "$BUILD_ROOT" || ! -d "$BUILD_ROOT" ]]; then
  echo "Usage: $0 /path/to/setuphelfer-rescue-live" >&2
  exit 20
fi

fail_missing() { echo "MISSING: $*" >&2; exit 10; }
fail_forbidden() { echo "FORBIDDEN: $*" >&2; exit 11; }
fail_secret() { echo "SECRET: $*" >&2; exit 12; }
fail_cdn() { echo "CDN: $*" >&2; exit 13; }
fail_token() { echo "FORBIDDEN_TOKEN: $*" >&2; exit 14; }
fail_firmware_apt() { echo "RESCUE-ISO-FIRMWARE-APT-COMPONENT-001: $*" >&2; exit 10; }
fail_firmware_pkg() { echo "RESCUE-ISO-FIRMWARE-PACKAGE-LIST-001: $*" >&2; exit 10; }
fail_networkmanager() { echo "RESCUE-ISO-NETWORKMANAGER-MISSING-001: $*" >&2; exit 10; }
fail_parent_archive() { echo "RESCUE-ISO-PARENT-ARCHIVE-AREAS-001: $*" >&2; exit 10; }
fail_chroot_sources() { echo "RESCUE-ISO-CHROOT-SOURCES-NONFREE-FIRMWARE-MISSING-001: $*" >&2; exit 10; }
fail_firmware_source_incomplete() { echo "RESCUE-ISO-FIRMWARE-APT-SOURCE-INCOMPLETE-001: $*" >&2; exit 10; }

REQ=(
  config/package-lists/setuphelfer.list.binary
  config/package-lists/setuphelfer.list.chroot
  config/archives/debian.list.chroot
  config/archives/debian.list.binary
  config/archives/debian-security.list.chroot
  config/archives/debian-security.list.binary
  config/includes.chroot/usr/local/bin/rsvg
  config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json
  config/includes.chroot/opt/setuphelfer-rescue/scripts/rescue-live/start-backend-localonly.sh
  config/includes.chroot/opt/setuphelfer-rescue/scripts/rescue-live/start-ui-localonly.sh
  config/includes.chroot/etc/systemd/system/setuphelfer-backend.service
  config/includes.chroot/etc/systemd/system/setuphelfer.service
  config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service
  config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer.service
  config/includes.chroot/etc/live/config.conf.d/10-setuphelfer-rescue.conf
  config/includes.chroot/etc/default/keyboard
  config/includes.chroot/etc/vconsole.conf
  config/includes.chroot/etc/locale.gen
  config/includes.chroot/etc/default/locale
  config/includes.chroot/etc/timezone
  config/includes.chroot/etc/localtime
  config/includes.chroot/etc/issue
  config/includes.chroot/etc/motd
  config/includes.chroot/etc/systemd/network/20-wired.network
  config/includes.chroot/etc/systemd/network/25-ethernet-alt.network
  config/hooks/normal/010-enable-setuphelfer-services.hook.chroot
  config/bootloaders/isolinux/bootlogo
  config/bootloaders/isolinux/splash.svg.in
  config/bootloaders/grub-efi/setuphelfer-grub-efi-note.txt
  auto/config
  auto/build
  auto/clean
  evidence/build-tree-manifest.json
  README_SETUPHELFER_RESCUE_LIVE.md
)

for rel in "${REQ[@]}"; do
  [[ -e "$BUILD_ROOT/$rel" ]] || fail_missing "$rel"
done
[[ -x "$BUILD_ROOT/config/includes.chroot/usr/local/bin/rsvg" ]] || fail_missing "usr/local/bin/rsvg not executable"
if ! grep -qx 'syslinux-utils' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" 2>/dev/null; then
  fail_missing "setuphelfer.list.chroot must list syslinux-utils (isohybrid runs in lb chroot; list.binary is ISO pool only)"
fi
if ! grep -qx 'syslinux-utils' "$BUILD_ROOT/config/package-lists/setuphelfer.list.binary" 2>/dev/null; then
  fail_missing "setuphelfer.list.binary must list syslinux-utils (optional ISO pool mirror)"
fi
grep -qx 'grub-efi-amd64-bin' "$BUILD_ROOT/config/package-lists/setuphelfer.list.binary" \
  || fail_missing "setuphelfer.list.binary must list grub-efi-amd64-bin (UEFI-x64 ISO pool)"
grep -qx 'grub-common' "$BUILD_ROOT/config/package-lists/setuphelfer.list.binary" \
  || fail_missing "setuphelfer.list.binary must list grub-common (UEFI-x64 ISO pool)"
if ! grep -q 'init=/lib/systemd/systemd' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set init=/lib/systemd/systemd in --bootappend-live"
fi
if ! grep -qE 'bootloaders syslinux,grub-efi|LB_COMMON' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must configure UEFI-x64 bootloaders or LB_COMMON eval wrapper"
fi
if ! grep -q 'Use controlled gate before running lb build' "$BUILD_ROOT/auto/build"; then
  fail_missing "auto/build gate message"
fi
if grep -Eq '^[[:space:]]*lb[[:space:]]+clean([[:space:]]|$)' "$BUILD_ROOT/auto/clean"; then
  fail_missing "auto/clean must not recurse into lb clean"
fi
if ! grep -q 'rm -rf .build chroot cache binary local' "$BUILD_ROOT/auto/clean"; then
  fail_missing "auto/clean must remove only live-build stage directories"
fi
if ! grep -q 'lb config noauto' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must use noauto"
fi
if ! grep -q -- '--security false' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must disable broken default security repo"
fi
if ! grep -q -- '--firmware-chroot false' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must disable broken firmware contents fetch"
fi
if ! grep -q -- '--firmware-binary false' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must disable broken firmware contents fetch for binary stage"
fi
if ! grep -q -- '--zsync false' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must disable zsync (stale .zsync.xz breaks incremental rebuilds)"
fi
if ! grep -q 'binary\*.zsync\*' "$BUILD_ROOT/auto/clean"; then
  fail_missing "auto/clean must remove binary*.zsync* artifacts at build-tree root"
fi
if ! grep -q 'hostname=setuphelfer-rescue' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set live hostname via --bootappend-live"
fi
if ! grep -q 'username=user' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set live username via --bootappend-live"
fi
if ! grep -q 'keyboard-layouts=de' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set keyboard-layouts=de in --bootappend-live"
fi
if ! grep -q 'locales=de_DE.UTF-8' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set locales=de_DE.UTF-8 in --bootappend-live"
fi
if ! grep -q 'timezone=Europe/Berlin' "$BUILD_ROOT/auto/config"; then
  fail_missing "auto/config must set timezone=Europe/Berlin in --bootappend-live"
fi
grep -qx 'dbus' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list dbus"
grep -qx 'systemd' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list systemd"
grep -qx 'systemd-sysv' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list systemd-sysv"
grep -qx 'firmware-iwlwifi' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_firmware_pkg "setuphelfer.list.chroot must list firmware-iwlwifi (MSI Intel WiFi/BT ibt via non-free-firmware)"
grep -qx 'firmware-intel-sound' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_firmware_pkg "setuphelfer.list.chroot must list firmware-intel-sound (Intel sound DSP)"
grep -qx 'network-manager' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_networkmanager "setuphelfer.list.chroot must list network-manager (rescue WLAN menu / nmcli)"
grep -qx 'wpasupplicant' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_networkmanager "setuphelfer.list.chroot must list wpasupplicant (WLAN supplicant for NetworkManager)"
if ! grep -qE '\-\-initsystem systemd' "$BUILD_ROOT/auto/config"; then
  fail_networkmanager "auto/config must set --initsystem systemd (live-config-sysvinit removes network-manager)"
fi
grep -qx 'wireless-regdb' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_firmware_pkg "setuphelfer.list.chroot must list wireless-regdb (WLAN regulatory domain)"
if grep -qx 'firmware-iwlwifi' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  && ! grep -q 'non-free-firmware' "$BUILD_ROOT/auto/config"; then
  fail_firmware_source_incomplete "firmware packages listed but auto/config missing non-free-firmware archive areas"
fi
if ! grep -qE "archive-areas 'main contrib non-free-firmware'|archive-areas \"main contrib non-free-firmware\"" "$BUILD_ROOT/auto/config"; then
  fail_firmware_apt "auto/config must quote --archive-areas 'main contrib non-free-firmware' (unquoted words break lb config)"
fi
if ! grep -qE "parent-archive-areas 'main contrib non-free-firmware'|parent-archive-areas \"main contrib non-free-firmware\"" "$BUILD_ROOT/auto/config"; then
  fail_parent_archive "auto/config must quote --parent-archive-areas 'main contrib non-free-firmware'"
fi
if [[ -f "$BUILD_ROOT/config/common" ]]; then
  if grep -qE 'LB_PARENT_ARCHIVE_AREAS="main"' "$BUILD_ROOT/config/common" \
    && ! grep -q 'non-free-firmware' "$BUILD_ROOT/config/common"; then
    fail_parent_archive "config/common stale: LB_PARENT_ARCHIVE_AREAS main-only (clean + prepare required)"
  fi
  if grep -qE 'LB_ARCHIVE_AREAS="main"' "$BUILD_ROOT/config/common" \
    && ! grep -q 'non-free-firmware' "$BUILD_ROOT/config/common"; then
    fail_firmware_apt "config/common stale: LB_ARCHIVE_AREAS main-only (clean + prepare required)"
  fi
fi
CHROOT_SOURCES="$BUILD_ROOT/chroot/etc/apt/sources.list"
if [[ -f "$CHROOT_SOURCES" ]]; then
  if grep -Eq 'bookworm main$|bookworm main[[:space:]]*$' "$CHROOT_SOURCES" \
    && ! grep -q 'non-free-firmware' "$CHROOT_SOURCES"; then
    fail_chroot_sources "stale chroot/etc/apt/sources.list is bookworm main-only — sudo clean required before rebuild"
  fi
fi
grep -q 'bookworm main contrib non-free-firmware' "$BUILD_ROOT/config/archives/debian.list.chroot" \
  || fail_parent_archive "debian.list.chroot must include bookworm main contrib non-free-firmware"
grep -q 'bookworm-updates main contrib non-free-firmware' "$BUILD_ROOT/config/archives/debian.list.chroot" \
  || fail_firmware_source_incomplete "debian.list.chroot must include bookworm-updates main contrib non-free-firmware"
if grep -Eq 'bookworm main$|bookworm main[[:space:]]*$' "$BUILD_ROOT/config/archives/debian.list.chroot" 2>/dev/null; then
  fail_parent_archive "debian.list.chroot parent mirror line is main-only"
fi
grep -q 'bookworm-security main contrib non-free-firmware' "$BUILD_ROOT/config/archives/debian-security.list.chroot" \
  || fail_firmware_source_incomplete "debian-security.list.chroot must include bookworm-security main contrib non-free-firmware"
grep -q 'non-free-firmware' "$BUILD_ROOT/config/archives/debian.list.binary" \
  || fail_parent_archive "debian.list.binary must include non-free-firmware for parent mirror"
grep -q 'non-free-firmware' "$BUILD_ROOT/config/archives/debian-security.list.binary" \
  || fail_firmware_source_incomplete "debian-security.list.binary must include non-free-firmware component"
python3 - "$BUILD_ROOT" <<'PY' || exit 10
import sys
from pathlib import Path

build_root = Path(sys.argv[1])
errors: list[str] = []
auto = (build_root / "auto/config").read_text(encoding="utf-8") if (build_root / "auto/config").is_file() else ""
parent = (build_root / "config/archives/debian.list.chroot").read_text(encoding="utf-8") if (build_root / "config/archives/debian.list.chroot").is_file() else ""
security = (build_root / "config/archives/debian-security.list.chroot").read_text(encoding="utf-8") if (build_root / "config/archives/debian-security.list.chroot").is_file() else ""

required_auto = (
    "archive-areas 'main contrib non-free-firmware'",
    "parent-archive-areas 'main contrib non-free-firmware'",
)
for token in required_auto:
    if token not in auto and token.replace("'", '"') not in auto:
        errors.append(f"auto/config missing {token}")

if "bookworm main contrib non-free-firmware" not in parent:
    errors.append("RESCUE-ISO-PARENT-ARCHIVE-AREAS-001: parent debian.list.chroot lacks bookworm non-free-firmware")
if "bookworm-updates main contrib non-free-firmware" not in parent:
    errors.append("RESCUE-ISO-FIRMWARE-APT-SOURCE-INCOMPLETE-001: parent debian.list.chroot lacks bookworm-updates non-free-firmware")
if "non-free-firmware" in security and "bookworm main contrib non-free-firmware" not in parent:
    errors.append("RESCUE-ISO-FIRMWARE-APT-SOURCE-INCOMPLETE-001: security has non-free-firmware but parent mirror does not")
if "bookworm-security main contrib non-free-firmware" not in security:
    errors.append("RESCUE-ISO-FIRMWARE-APT-SOURCE-INCOMPLETE-001: security list incomplete")

for err in errors:
    print(err, file=sys.stderr)
if errors:
    sys.exit(1)
print("OK: apt archive areas complete for firmware packages")
PY
grep -q 'XKBLAYOUT="de"' "$BUILD_ROOT/config/includes.chroot/etc/default/keyboard" \
  || fail_missing 'etc/default/keyboard must contain XKBLAYOUT="de"'
grep -q 'KEYMAP=de-latin1' "$BUILD_ROOT/config/includes.chroot/etc/vconsole.conf" \
  || fail_missing 'etc/vconsole.conf must contain KEYMAP=de-latin1'
grep -q 'LANG=de_DE.UTF-8' "$BUILD_ROOT/config/includes.chroot/etc/default/locale" \
  || fail_missing 'etc/default/locale must contain LANG=de_DE.UTF-8'
grep -q 'Europe/Berlin' "$BUILD_ROOT/config/includes.chroot/etc/timezone" \
  || fail_missing 'etc/timezone must contain Europe/Berlin'
grep -qE 'Login: user|Login: user ' "$BUILD_ROOT/config/includes.chroot/etc/issue" \
  || fail_missing 'etc/issue must document user login'
grep -q 'live' "$BUILD_ROOT/config/includes.chroot/etc/issue" \
  || fail_missing 'etc/issue must document live password'
[[ -L "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service" ]] \
  || fail_missing "systemd enable symlink setuphelfer-backend.service"
[[ -L "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer.service" ]] \
  || fail_missing "systemd enable symlink setuphelfer.service"
set +e
"$BUILD_ROOT/auto/build" >/dev/null 2>&1
build_rc=$?
set -e
[[ "$build_rc" -eq 20 ]] || fail_missing "auto/build must exit 20 (got $build_rc)"

while IFS= read -r -d '' f; do
  fail_forbidden "$f"
done < <(find "$BUILD_ROOT" -type f \( \
  -name '*.iso' -o -name '*.img' -o -name '*.qcow2' \
  -o -name 'filesystem.squashfs' -o -name 'initrd.img' -o -name 'vmlinuz' \
  -o -name '.env' \
\) -print0 2>/dev/null)

if find "$BUILD_ROOT" -type d -name node_modules 2>/dev/null | grep -q .; then
  fail_forbidden "node_modules"
fi

RUNTIME="$BUILD_ROOT/config/includes.chroot/opt/setuphelfer-rescue"
if grep -rqE 'fonts\.googleapis\.com|fonts\.gstatic\.com' "$RUNTIME/frontend/dist" 2>/dev/null; then
  fail_cdn "Google Fonts in runtime frontend/dist"
fi

SECRET_PAT='API_KEY=|SECRET=|PASSWORD=|TOKEN=|PRIVATE KEY'
for scan_dir in backend config; do
  [[ -d "$RUNTIME/$scan_dir" ]] || continue
  if grep -rIE "$SECRET_PAT" "$RUNTIME/$scan_dir" \
    --exclude-dir='venv' --exclude-dir='tests' \
    2>/dev/null \
    | grep -v 'your-app-password' \
    | grep -v 'BEGIN OPENSSH' \
    | grep -v 're.search(r"API_KEY=|SECRET=|PASSWORD=|TOKEN=|PRIVATE KEY"' \
    | head -1 | grep -q .; then
    fail_secret "pattern in $scan_dir"
  fi
done

FORBIDDEN_TOKENS=(
  'dd if='
  mkfs
  parted
  'mount '
  'umount '
  'apt install'
  'apt upgrade'
  'restore --execute'
  'queue apply'
)

while IFS= read -r -d '' script; do
  [[ -f "$script" ]] || continue
  case "$script" in
    */includes.chroot/opt/setuphelfer-rescue/*) continue ;;
  esac
  for tok in "${FORBIDDEN_TOKENS[@]}"; do
    if grep -qF "$tok" "$script" 2>/dev/null; then
      fail_token "$tok in $script"
    fi
  done
done < <(find "$BUILD_ROOT" -type f \( -name '*.sh' -o -name '*.hook.chroot' -o -path '*/auto/*' \) -print0 2>/dev/null)

python3 - "$BUILD_ROOT/evidence/build-tree-manifest.json" <<'PY' || exit 20
import json, sys
from pathlib import Path
m = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert m.get("controlled_live_build_tree") is True
assert m.get("no_real_build_execution") is True
assert m.get("real_iso_build_allowed") is False
assert m.get("usb_write_allowed") is False
print(f"OK: build-tree-manifest source_head={m.get('source_head')}")
PY

"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/validate-live-build-dpkg-preflight.sh" "$BUILD_ROOT"

marker_svc="$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-serial-boot-markers.service"
if [[ -f "$marker_svc" ]]; then
  if ! grep -q 'ConditionVirtualization=qemu' "$marker_svc"; then
    echo "RESCUE-ISO-SERIAL-MARKER-001: serial-boot-markers.service missing ConditionVirtualization=qemu" >&2
    exit 12
  fi
  if grep -q 'TTYPath=/dev/ttyS0' "$marker_svc"; then
    echo "RESCUE-ISO-SERIAL-MARKER-001: serial-boot-markers.service must not use TTYPath=/dev/ttyS0 on hardware" >&2
    exit 12
  fi
else
  echo "RESCUE-ISO-SERIAL-MARKER-001: missing setuphelfer-serial-boot-markers.service in chroot overlay" >&2
  exit 12
fi
grep -qx 'rfkill' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_networkmanager "setuphelfer.list.chroot must list rfkill"
grep -qx 'iputils-ping' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list iputils-ping"
grep -qx 'pciutils' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list pciutils"
grep -qx 'usbutils' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_missing "setuphelfer.list.chroot must list usbutils"
grep -qx 'iw' "$BUILD_ROOT/config/package-lists/setuphelfer.list.chroot" \
  || fail_networkmanager "setuphelfer.list.chroot must list iw"
for _script in setuphelfer-rescue-network-onboarding setuphelfer-rescue-media-check setuphelfer-rescue-live-medium-check.py setuphelfer-rescue-telemetry-push setuphelfer-rescue-telemetry-retry setuphelfer-rescue-telemetry-build-payload.py setuphelfer-rescue-task-pull setuphelfer-rescue-disk-discovery setuphelfer-rescue-disk-discovery.py setuphelfer-rescue-start-assistant setuphelfer-rescue-plan-builder.py; do
  [[ -x "$BUILD_ROOT/config/includes.chroot/usr/local/sbin/${_script}" ]] \
    || fail_missing "usr/local/sbin/${_script} missing or not executable"
done
[[ -f "$BUILD_ROOT/config/includes.chroot/usr/share/setuphelfer/rescue/boot-branding.txt" ]] \
  || fail_missing "usr/share/setuphelfer/rescue/boot-branding.txt missing"
[[ -f "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-telemetry-retry.timer" ]] \
  || fail_missing "setuphelfer-rescue-telemetry-retry.timer missing"
[[ -f "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-telemetry-retry.service" ]] \
  || fail_missing "setuphelfer-rescue-telemetry-retry.service missing"
_hook="$BUILD_ROOT/config/hooks/normal/020-setuphelfer-rescue-boot-menu.hook.binary"
if [[ -f "$_hook" ]]; then
  grep -q 'Setuphelfer Rettung starten' "$_hook" || fail_missing "boot menu hook missing Setuphelfer Rettung starten entry"
  grep -q 'label setuphelfer-rescue-default' "$BUILD_ROOT/config/bootloaders/isolinux/live.cfg.in" \
    || fail_missing "live.cfg.in missing setuphelfer-rescue-default label"
  grep -q 'setuphelfer-rescue-start-assistant' "$BUILD_ROOT/config/includes.chroot/usr/local/sbin/setuphelfer-rescue-start-assistant" \
    || fail_missing "setuphelfer-rescue-start-assistant missing"
  [[ -f "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" ]] \
    || fail_missing "setuphelfer-rescue-start-assistant.service missing"
  grep -q 'ConditionKernelCommandLine=setuphelfer_start_assistant=1' \
    "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" \
    || fail_missing "start-assistant.service missing ConditionKernelCommandLine"
  grep -q 'TTYPath=/dev/tty1' \
    "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" \
    || fail_missing "start-assistant.service missing TTYPath=/dev/tty1"
  grep -q 'StandardInput=tty' \
    "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" \
    || fail_missing "start-assistant.service missing StandardInput=tty"
  grep -q 'StandardOutput=tty' \
    "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" \
    || fail_missing "start-assistant.service missing StandardOutput=tty"
  grep -q 'Environment=TERM=linux' \
    "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-start-assistant.service" \
    || fail_missing "start-assistant.service missing TERM=linux"
  [[ -f "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/getty@tty1.service.d/setuphelfer-rescue.conf" ]] \
    || fail_missing "getty@tty1 rescue drop-in missing"
  python3 -m py_compile "$BUILD_ROOT/config/includes.chroot/usr/local/sbin/setuphelfer-rescue-disk-discovery.py" \
    || fail_missing "setuphelfer-rescue-disk-discovery.py py_compile failed"
  python3 -m py_compile "$BUILD_ROOT/config/includes.chroot/usr/local/sbin/setuphelfer-rescue-plan-builder.py" \
    || fail_missing "setuphelfer-rescue-plan-builder.py py_compile failed"
else
  fail_missing "missing 020-setuphelfer-rescue-boot-menu.hook.binary"
fi
python3 -m py_compile "$BUILD_ROOT/config/includes.chroot/usr/local/sbin/setuphelfer-rescue-telemetry-build-payload.py" \
  || fail_missing "setuphelfer-rescue-telemetry-build-payload.py py_compile failed"
[[ -f "$BUILD_ROOT/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-network-onboarding.service" ]] \
  || fail_missing "setuphelfer-rescue-network-onboarding.service missing"
if [[ ! -f "$BUILD_ROOT/config/hooks/normal/015-ensure-network-manager.hook.chroot" ]]; then
  fail_networkmanager "missing 015-ensure-network-manager.hook.chroot (NM safety net after live-packages)"
fi

MANIFEST="${BUILD_ROOT}/evidence/build-tree-manifest.json"
python3 - "$MANIFEST" "$BUILD_ROOT" <<'PY' || fail_missing "developer-qemu profile markers incomplete (see stderr)"
import json
import os
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
build_root = Path(sys.argv[2])
if not manifest.is_file():
    sys.exit(0)
data = json.loads(manifest.read_text(encoding="utf-8"))
if data.get("rescue_build_profile") != "developer-qemu":
    sys.exit(0)

errors = []
auto = (build_root / "auto/config").read_text(encoding="utf-8") if (build_root / "auto/config").is_file() else ""
if "console=ttyS0" not in auto:
    errors.append("auto/config missing console=ttyS0")
if "quiet splash" in auto:
    errors.append("auto/config has quiet splash (not developer-qemu)")
if not (build_root / "config/hooks/normal/090-enable-qemu-smoke-autopilot.hook.chroot").is_file():
    errors.append("missing 090-enable-qemu-smoke-autopilot.hook.chroot")
if not (build_root / "config/includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh").is_file():
    errors.append("missing setuphelfer-qemu-smoke-autopilot.sh")
isolinux = build_root / "config/bootloaders/isolinux/isolinux.cfg"
if isolinux.is_file() and "SERIAL 0" not in isolinux.read_text(encoding="utf-8"):
    errors.append("isolinux.cfg missing SERIAL 0 (developer-qemu)")
if not data.get("qemu_serial_console_configured"):
    errors.append("manifest qemu_serial_console_configured=false")
if not data.get("qemu_smoke_autopilot_hook"):
    errors.append("manifest qemu_smoke_autopilot_hook=false")
wants = build_root / "config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service"
if not wants.is_symlink() and not wants.exists():
    errors.append(f"missing autopilot wants symlink: {wants}")
elif wants.is_symlink() or wants.exists():
    target = os.readlink(wants) if wants.is_symlink() else ""
    if target and target != "../setuphelfer-qemu-smoke-autopilot.service":
        errors.append(f"autopilot wants symlink target wrong: {target!r}")
marker_svc = build_root / "config/includes.chroot/etc/systemd/system/setuphelfer-serial-boot-markers.service"
if marker_svc.is_file():
    marker_text = marker_svc.read_text(encoding="utf-8")
    if "ConditionVirtualization=qemu" not in marker_text:
        errors.append("serial-boot-markers.service missing ConditionVirtualization=qemu")
    if "TTYPath=/dev/ttyS0" in marker_text:
        errors.append("serial-boot-markers.service must not use TTYPath=/dev/ttyS0 on hardware")
    if "StandardOutput=tty" in marker_text:
        errors.append("serial-boot-markers.service must not force StandardOutput=tty")
else:
    errors.append("missing setuphelfer-serial-boot-markers.service in chroot overlay")
if errors:
    for e in errors:
        print(f"DEVELOPER_QEMU: {e}", file=sys.stderr)
    sys.exit(1)
print("OK: developer-qemu profile markers present")
PY

echo "OK: controlled live build tree validation passed"
exit 0
