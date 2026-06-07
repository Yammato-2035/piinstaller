#!/usr/bin/env bash
# Patch FAT32 ESP staging grub.cfg with real FAT filesystem UUID (after mkfs, before rsync).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

STAGING=""
FAT_UUID=""
usage() {
  echo "Usage: $0 --staging DIR --fat-uuid UUID" >&2
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) STAGING="$2"; shift 2 ;;
    --fat-uuid) FAT_UUID="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$STAGING" && -n "$FAT_UUID" ]] || usage
[[ -d "$STAGING" ]] || { echo "ERROR: staging dir missing: $STAGING" >&2; exit 21; }

python3 - <<PY
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import patch_staging_grub_for_fat_uuid

out = patch_staging_grub_for_fat_uuid(Path(${STAGING@Q}), ${FAT_UUID@Q})
print(f"OK: patched grub.cfg at {out}")
PY

grep -n "search" "${STAGING}/boot/grub/grub.cfg" || true
