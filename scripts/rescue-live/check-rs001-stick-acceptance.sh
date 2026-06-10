#!/usr/bin/env bash
# RS-001 stick acceptance — read-only FAT32 ESP + SquashFS contract checks (no writes).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

TARGET=""
PART=""
EXPECTED_SQ_SHA=""
OUTPUT_JSON=""
QEMU_SMOKE="not_run"

usage() {
  echo "Usage: $0 --target /dev/sdX --expected-squashfs-sha256 HEX [--partition /dev/sdX1] [--output-json PATH]" >&2
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --partition) PART="$2"; shift 2 ;;
    --expected-squashfs-sha256) EXPECTED_SQ_SHA="$2"; shift 2 ;;
    --output-json) OUTPUT_JSON="$2"; shift 2 ;;
    --qemu-smoke) QEMU_SMOKE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$TARGET" && -n "$EXPECTED_SQ_SHA" ]] || usage

if [[ -z "$PART" ]]; then
  PART="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import partition_path_for_target
print(partition_path_for_target(${TARGET@Q}, 1))
PY
)"
fi

MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
WAS_MOUNTED=false
if [[ -z "$MOUNT" ]]; then
  if command -v udisksctl >/dev/null 2>&1; then
    udisksctl mount -b "$PART" --options ro >/dev/null 2>&1 || {
      echo "ERROR: read-only mount failed" >&2
      exit 30
    }
    MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
  else
    echo "ERROR: read-only mount failed (no udisksctl)" >&2
    exit 30
  fi
else
  WAS_MOUNTED=true
fi

[[ -n "$MOUNT" && -d "$MOUNT" ]] || {
  echo "ERROR: mount point missing" >&2
  exit 30
}

cleanup() {
  if [[ "$WAS_MOUNTED" != true && -n "$MOUNT" ]]; then
    udisksctl unmount -b "$PART" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

RESULT_TMP="$(mktemp)"
EXIT_TMP="$(mktemp)"
trap 'rm -f "$RESULT_TMP" "$EXIT_TMP"' EXIT

python3 - <<PY >"$RESULT_TMP"
import json
from pathlib import Path
from rescue.rescue_stick_acceptance import evaluate_stick_acceptance

result = evaluate_stick_acceptance(
    mount_root=Path(${MOUNT@Q}),
    target_device=${TARGET@Q},
    target_partition=${PART@Q},
    expected_squashfs_sha256=${EXPECTED_SQ_SHA@Q},
    repo_root=Path(${REPO_ROOT@Q}),
    qemu_smoke=${QEMU_SMOKE@Q},
)
print(json.dumps(result.to_json(), indent=2))
Path(${EXIT_TMP@Q}).write_text(str(result.exit_code), encoding="utf-8")
PY

EXIT_CODE="$(cat "$EXIT_TMP")"
if [[ -n "$OUTPUT_JSON" ]]; then
  cp -f "$RESULT_TMP" "$OUTPUT_JSON"
fi
cat "$RESULT_TMP"
STATUS="$(python3 -c "import json; print(json.load(open('$RESULT_TMP')).get('acceptance_status','blocked'))")"
echo "RS-001 stick acceptance: ${STATUS} (exit ${EXIT_CODE})" >&2
exit "$EXIT_CODE"
