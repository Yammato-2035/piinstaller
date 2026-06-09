#!/usr/bin/env bash
# Read-only verification of FAT32 ESP Rescue USB layout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

TARGET=""
PART=""
MOUNT=""
EXPECTED_SQ_SHA=""
usage() {
  echo "Usage: $0 --target /dev/sdX [--partition /dev/sdX1]" >&2
  exit 20
}

fail() {
  echo "RESCUE-FAT32-VERIFY: $1" >&2
  exit "${2:-1}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --partition) PART="$2"; shift 2 ;;
    --expected-squashfs-sha256) EXPECTED_SQ_SHA="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$TARGET" ]] || usage
[[ "$TARGET" != /dev/sda ]] || fail "forbidden target /dev/sda" 27
[[ "$TARGET" != /dev/nvme* ]] || fail "forbidden nvme target" 27

if [[ -z "$PART" ]]; then
  PART="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import partition_path_for_target
print(partition_path_for_target(${TARGET@Q}, 1))
PY
)"
fi

# Never use parent device for FAT label — partition only.
if [[ "$PART" == "$TARGET" ]]; then
  fail "FAT label must be read from partition device, not parent ${TARGET}" 22
fi

sudo udevadm settle --timeout=15 2>/dev/null || udevadm settle --timeout=15 2>/dev/null || true

EVAL_JSON="$(python3 - <<PY
import json
from core.rescue_fat32_esp_usb_verify import (
    evaluate_verify_probe,
    lsblk_field,
    probe_fat_volume_label,
    probe_parent_signature_types,
)

target = ${TARGET@Q}
part = ${PART@Q}

parent_pttype = lsblk_field(target, "PTTYPE")
part_parttype = lsblk_field(part, "PARTTYPE")
part_partlabel = lsblk_field(part, "PARTLABEL")
part_fstype = lsblk_field(part, "FSTYPE")
part_fat_label = probe_fat_volume_label(part)
parent_sigs = probe_parent_signature_types(target)

print(f"PTTYPE={parent_pttype} PARTTYPE={part_parttype} FSTYPE={part_fstype}", flush=True)
print(f"PARTLABEL={part_partlabel or ''} FAT_LABEL={part_fat_label or ''}", flush=True)

result = evaluate_verify_probe(
    parent_pttype=parent_pttype,
    parent_signature_types=parent_sigs,
    part_parttype=part_parttype,
    part_partlabel=part_partlabel,
    part_fstype=part_fstype,
    part_fat_label=part_fat_label,
    target_device=target,
)
print(json.dumps(result))
PY
)"

# stdout: two probe lines then JSON on last line
EVAL_LINE="$(echo "$EVAL_JSON" | tail -1)"
WARNINGS="$(python3 - <<PY
import json
r = json.loads(${EVAL_LINE@Q})
for w in r.get("warnings") or []:
    print(w)
PY
)"

while IFS= read -r warn_line; do
  [[ -n "$warn_line" ]] && echo "RESCUE-FAT32-VERIFY: ${warn_line}" >&2
done <<< "$WARNINGS"

VERIFY_OK="$(python3 - <<PY
import json
r = json.loads(${EVAL_LINE@Q})
print("yes" if r.get("ok") else "no")
PY
)"

if [[ "$VERIFY_OK" != "yes" ]]; then
  python3 - <<PY
import json, sys
r = json.loads(${EVAL_LINE@Q})
for err in r.get("errors") or []:
    print(f"RESCUE-FAT32-VERIFY: {err['message']}", file=sys.stderr)
sys.exit(int(r.get("exit_code") or 1))
PY
fi

MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
WAS_MOUNTED=false
if [[ -z "$MOUNT" ]]; then
  if command -v udisksctl >/dev/null; then
    udisksctl mount -b "$PART" --options ro >/dev/null 2>&1 || fail "read-only mount failed" 28
    MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
  else
    fail "read-only mount failed (no udisksctl)" 28
  fi
else
  WAS_MOUNTED=true
fi

[[ -n "$MOUNT" && -d "$MOUNT" ]] || fail "read-only mount failed" 28

cleanup() {
  if [[ "$WAS_MOUNTED" != true && -n "$MOUNT" ]]; then
    udisksctl unmount -b "$PART" >/dev/null 2>&1 || true
    sync || true
  fi
}
trap cleanup EXIT

check_file() {
  local rel="$1" code="$2"
  if [[ ! -e "$MOUNT/$rel" ]]; then
    fail "missing $rel" "$code"
  fi
  echo "OK: $rel"
}

check_file "EFI/BOOT/BOOTX64.EFI" 23
check_file "boot/grub/grub.cfg" 24
check_file "live/vmlinuz" 25
check_file "live/initrd.img" 25
check_file "live/filesystem.squashfs" 26
check_file "setuphelfer/rescue/boot-branding.txt" 26

if [[ -e "$MOUNT/.sqtmp" ]]; then
  fail "staging artifact .sqtmp must not be on USB" 26
fi

if grep -q "menuentry \"Setuphelfer Rettung starten\"" "$MOUNT/boot/grub/grub.cfg" 2>/dev/null; then
  echo "OK: grub menu Setuphelfer Rettung starten"
else
  fail "grub.cfg missing required menu entry" 24
fi

GRUB_CHECK="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_fat32_esp_usb_verify import (
    probe_fat_filesystem_uuid,
    validate_fat32_esp_grub_cfg_file,
)

mount = Path(${MOUNT@Q})
part = ${PART@Q}
fat_uuid = probe_fat_filesystem_uuid(part)
result = validate_fat32_esp_grub_cfg_file(
    mount / "boot/grub/grub.cfg",
    mount_root=mount,
    expected_fat_uuid=fat_uuid or None,
)
result["fat_uuid"] = fat_uuid or None
print(json.dumps(result))
PY
)"

GRUB_OK="$(python3 - <<PY
import json
print("yes" if json.loads(${GRUB_CHECK@Q}).get("ok") else "no")
PY
)"

if [[ "$GRUB_OK" != "yes" ]]; then
  python3 - <<PY
import json, sys
r = json.loads(${GRUB_CHECK@Q})
for code in r.get("errors") or []:
    print(f"RESCUE-FAT32-VERIFY: {code}", file=sys.stderr)
sys.exit(29)
PY
fi
echo "OK: grub.cfg FAT root search and kernel/initrd paths"

BOOTX64_CHECK="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_fat32_esp_usb_verify import validate_fat32_esp_bootx64_on_mount

mount = Path(${MOUNT@Q})
result = validate_fat32_esp_bootx64_on_mount(mount)
print(json.dumps(result))
PY
)"

BOOTX64_OK="$(python3 - <<PY
import json
print("yes" if json.loads(${BOOTX64_CHECK@Q}).get("ok") else "no")
PY
)"

if [[ "$BOOTX64_OK" != "yes" ]]; then
  python3 - <<PY
import json, sys
r = json.loads(${BOOTX64_CHECK@Q})
for code in r.get("errors") or []:
    print(f"RESCUE-FAT32-VERIFY: {code}", file=sys.stderr)
sys.exit(30)
PY
fi
echo "OK: standalone BOOTX64.EFI (grub_mkstandalone, differs from ISO)"

SQ_SIZE="$(stat -c '%s' "$MOUNT/live/filesystem.squashfs" 2>/dev/null || echo 0)"
echo "filesystem.squashfs size_bytes=${SQ_SIZE}"
[[ "$SQ_SIZE" -gt 100000000 ]] || fail "filesystem.squashfs size implausible" 26

if [[ -n "$EXPECTED_SQ_SHA" ]]; then
  SQ_SHA="$(sha256sum "$MOUNT/live/filesystem.squashfs" | awk '{print $1}')"
  SQ_HASH_CHECK="$(python3 - <<PY
import json
from core.rescue_fat32_esp_usb_verify import evaluate_expected_squashfs_sha256

print(json.dumps(evaluate_expected_squashfs_sha256(
    actual_sha256=${SQ_SHA@Q},
    expected_sha256=${EXPECTED_SQ_SHA@Q},
)))
PY
)"
  SQ_HASH_OK="$(python3 - <<PY
import json
print("yes" if json.loads(${SQ_HASH_CHECK@Q}).get("ok") else "no")
PY
)"
  if [[ "$SQ_HASH_OK" != "yes" ]]; then
    python3 - <<PY
import json, sys
r = json.loads(${SQ_HASH_CHECK@Q})
msg = r.get("message") or "squashfs hash mismatch"
print(f"RESCUE-FAT32-VERIFY: {msg}", file=sys.stderr)
print(f"RESCUE-FAT32-VERIFY: expected={r.get('expected_sha256')}", file=sys.stderr)
print(f"RESCUE-FAT32-VERIFY: actual={r.get('actual_sha256')}", file=sys.stderr)
sys.exit(31)
PY
  fi
  echo "OK: filesystem.squashfs sha256 matches expected"
fi

EXPECTED_FAT_LABEL="$(python3 - <<'PY'
from core.rescue_fat32_esp_usb_writer import FAT_VOLUME_LABEL
print(FAT_VOLUME_LABEL)
PY
)"
EXPECTED_GPT_PART_NAME="$(python3 - <<'PY'
from core.rescue_fat32_esp_usb_writer import GPT_PARTITION_NAME
print(GPT_PARTITION_NAME)
PY
)"

echo "OK: FAT32 ESP rescue USB verified read-only on ${PART} mount=${MOUNT} fat_label=${EXPECTED_FAT_LABEL} gpt_name=${EXPECTED_GPT_PART_NAME}"
exit 0
