#!/usr/bin/env bash
# Read-only: prüft filesystem.squashfs in einer Rescue-Hybrid-ISO.
# Exit 0 ok | 10 missing artifact | 11 integration gap | 20 usage
set -euo pipefail

ISO="${1:-}"
if [[ -z "$ISO" || ! -f "$ISO" ]]; then
  echo "Usage: $0 /path/to/binary.hybrid.iso" >&2
  exit 20
fi

fail_missing() { echo "MISSING: $*" >&2; exit 10; }
fail_gap() { echo "INTEGRATION_GAP: $*" >&2; exit 11; }

command -v unsquashfs >/dev/null || fail_missing "unsquashfs"
command -v xorriso >/dev/null || fail_missing "xorriso"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

xorriso -osirrox on -indev "$ISO" -extract /live/filesystem.squashfs "$WORK/filesystem.squashfs" 2>/dev/null \
  || fail_missing "extract /live/filesystem.squashfs from ISO"

SQ="$WORK/filesystem.squashfs"

squashfs_path_exists() {
  unsquashfs -cat "$SQ" "$1" >/dev/null 2>&1
}

squashfs_path_exists 'opt/setuphelfer-rescue/MANIFEST.json' \
  || fail_missing "/opt/setuphelfer-rescue/MANIFEST.json in squashfs"

squashfs_path_exists 'opt/setuphelfer-rescue/backend/venv/bin/python3' \
  || fail_missing "bundled backend venv in squashfs"

squashfs_path_exists 'etc/systemd/system/setuphelfer-backend.service' \
  || fail_missing "setuphelfer-backend.service unit in squashfs"

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer-backend.service'; then
  fail_gap "setuphelfer-backend.service not enabled in squashfs (no multi-user.target.wants symlink)"
fi

if ! squashfs_path_exists 'etc/systemd/system/multi-user.target.wants/setuphelfer.service'; then
  fail_gap "setuphelfer.service not enabled in squashfs (no multi-user.target.wants symlink)"
fi

echo "OK: rescue ISO squashfs contains bundle and enabled Setuphelfer units"
