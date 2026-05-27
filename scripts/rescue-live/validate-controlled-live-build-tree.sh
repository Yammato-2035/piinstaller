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

REQ=(
  config/package-lists/setuphelfer.list.chroot
  config/archives/debian-security.list.chroot
  config/archives/debian-security.list.binary
  config/includes.chroot/usr/local/bin/rsvg
  config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json
  config/includes.chroot/opt/setuphelfer-rescue/scripts/rescue-live/start-backend-localonly.sh
  config/includes.chroot/opt/setuphelfer-rescue/scripts/rescue-live/start-ui-localonly.sh
  config/includes.chroot/etc/systemd/system/setuphelfer-backend.service
  config/includes.chroot/etc/systemd/system/setuphelfer.service
  config/includes.chroot/etc/systemd/network/20-wired.network
  config/includes.chroot/etc/systemd/network/25-ethernet-alt.network
  config/hooks/normal/010-enable-setuphelfer-services.hook.chroot
  config/bootloaders/isolinux/bootlogo
  config/bootloaders/isolinux/splash.svg.in
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

echo "OK: controlled live build tree validation passed"
exit 0
