#!/usr/bin/env bash
# FAT32 ESP Rescue USB writer — default dry-run; destructive write with operator confirm.
# --execute-write runs controlled steps when all safety gates pass (operator terminal only).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVIDENCE_ROOT="${REPO_ROOT}/docs/evidence/runtime-results/rescue"

ISO=""
TARGET=""
DRY_RUN=true
CONFIRM_WRITE=false
EXECUTE_WRITE=false
CONFIRM_PHRASE=""
ESP_SIZE_MIB=4096
STAGING_DIR="${REPO_ROOT}/build/rescue/fat32-esp-staging"
EXPECTED_ISO_SHA256="c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194"

RUN_ID=""
EVIDENCE_DIR=""
WRITE_LOG=""
FAILED_STEP=""
FAT_UUID=""
MNT=""
PART_DEV=""

usage() {
  cat <<EOF
Usage: $0 --iso PATH --target /dev/sdX [options]

Options:
  --dry-run                          Plan only (default)
  --operator-confirm-write             Required for destructive mode
  --confirm-phrase PHRASE            Must be: WRITE SETUPHELFER FAT32 ESP USB
  --execute-write                    Run destructive steps (operator terminal only)
  --esp-size-mib N                   ESP size (default 4096)
  --staging-dir PATH                 Staging directory
  --expected-iso-sha256 HEX          ISO SHA256 gate (default: canonical rescue ISO)

Without --execute-write: prints plan and write_manual; write_executed=false.
With --execute-write: runs wipefs/sgdisk/mkfs/rsync/verify when all gates pass.

DCC/Agent must NOT invoke --execute-write automatically.
EOF
  exit 20
}

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

partition_path_for_target() {
  python3 - <<PY
from core.rescue_fat32_esp_usb_writer import partition_path_for_target
print(partition_path_for_target(${1@Q}, int(${2:-1})))
PY
}

run_step() {
  local name="$1"
  shift
  echo "=== STEP: ${name} ===" | tee -a "$WRITE_LOG"
  echo "+ $*" | tee -a "$WRITE_LOG"
  if ! "$@" >>"$WRITE_LOG" 2>&1; then
    FAILED_STEP="$name"
    echo "FAILED_STEP=${name}" | tee -a "$WRITE_LOG" >&2
    return 1
  fi
  echo "OK: ${name}" | tee -a "$WRITE_LOG"
}

record_pre_state() {
  {
    echo "=== pre_lsblk ==="
    lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,PARTTYPENAME,MOUNTPOINTS "$TARGET" || true
    lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,PARTTYPENAME,MOUNTPOINTS "$PART_DEV" 2>/dev/null || true
    echo "=== pre_wipefs ==="
    sudo wipefs --no-act "$TARGET" 2>&1 || wipefs --no-act "$TARGET" 2>&1 || true
    echo "=== pre_sgdisk ==="
    sudo sgdisk -p "$TARGET" 2>&1 || true
  } >"${EVIDENCE_DIR}/pre_lsblk.txt"
  cp "${EVIDENCE_DIR}/pre_lsblk.txt" "${EVIDENCE_DIR}/pre_wipefs.txt"
  cp "${EVIDENCE_DIR}/pre_lsblk.txt" "${EVIDENCE_DIR}/pre_sgdisk.txt"
}

record_post_state() {
  {
    echo "=== post_lsblk ==="
    lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,PARTTYPENAME,MOUNTPOINTS "$TARGET" || true
    lsblk -o NAME,PATH,SIZE,TYPE,FSTYPE,PARTTYPENAME,MOUNTPOINTS "$PART_DEV" 2>/dev/null || true
    echo "=== post_blkid ==="
    sudo blkid -p "$PART_DEV" 2>&1 || blkid -p "$PART_DEV" 2>&1 || true
  } >"${EVIDENCE_DIR}/post_lsblk.txt"
  cp "${EVIDENCE_DIR}/post_lsblk.txt" "${EVIDENCE_DIR}/post_blkid.txt"
}

finalize_write_evidence() {
  local write_status="$1"
  local verify_status="$2"
  local write_executed="$3"
  export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
  FAT32_EVIDENCE_DIR="$EVIDENCE_DIR" \
  FAT32_EVIDENCE_ROOT="$EVIDENCE_ROOT" \
  FAT32_REPO_ROOT="$REPO_ROOT" \
  FAT32_ISO="$ISO" \
  FAT32_TARGET="$TARGET" \
  FAT32_STARTED_AT="$STARTED_AT" \
  FAT32_WRITE_STATUS="$write_status" \
  FAT32_VERIFY_STATUS="$verify_status" \
  FAT32_WRITE_EXECUTED="$write_executed" \
  FAT32_FAILED_STEP="${FAILED_STEP:-}" \
  FAT32_FAT_UUID="${FAT_UUID:-}" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

from core.rescue_fat32_esp_usb_writer import finalize_fat32_esp_write_evidence

def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")

out = finalize_fat32_esp_write_evidence(
    evidence_dir=Path(os.environ["FAT32_EVIDENCE_DIR"]),
    evidence_root=Path(os.environ["FAT32_EVIDENCE_ROOT"]),
    repo_root=Path(os.environ["FAT32_REPO_ROOT"]),
    iso_path=Path(os.environ["FAT32_ISO"]),
    target_device=os.environ["FAT32_TARGET"],
    started_at=os.environ["FAT32_STARTED_AT"],
    write_executed=_bool_env("FAT32_WRITE_EXECUTED"),
    write_status=os.environ["FAT32_WRITE_STATUS"],
    verify_status=os.environ["FAT32_VERIFY_STATUS"],
    failed_step=os.environ.get("FAT32_FAILED_STEP") or None,
    fat_uuid=os.environ.get("FAT32_FAT_UUID") or None,
)
print(
    json.dumps(
        {
            "write_status": out["result"]["write_status"],
            "verify_status": out["result"]["verify_status"],
            "evidence_status": out["evidence_status"],
        }
    )
)
PY
}

cleanup_mount_on_exit() {
  if [[ -n "${MNT:-}" && -d "${MNT:-}" ]]; then
    sudo umount "$MNT" 2>/dev/null || true
    rmdir "$MNT" 2>/dev/null || true
  fi
}

execute_fat32_esp_write() {
  set -euo pipefail
  trap cleanup_mount_on_exit EXIT

  local labels gpt_name fat_label
  labels="$(python3 - <<'PY'
from core.rescue_fat32_esp_usb_writer import fat32_esp_label_spec
import json
print(json.dumps(fat32_esp_label_spec()))
PY
)"
  gpt_name="$(python3 -c "import json; print(json.loads('''$labels''')['gpt_partition_name'])")"
  fat_label="$(python3 -c "import json; print(json.loads('''$labels''')['fat_volume_label'])")"

  record_pre_state

  run_step wipefs_probe sudo wipefs --no-act "$TARGET" || true
  run_step wipefs_full sudo wipefs -a "$TARGET"
  run_step sgdisk_zap sudo sgdisk --zap-all "$TARGET"
  run_step sgdisk_create_esp sudo sgdisk -n "1:0:+${ESP_SIZE_MIB}MiB" -t "1:EF00" -c "1:${gpt_name}" "$TARGET"
  run_step partprobe sudo partprobe "$TARGET" || true
  run_step udev_settle sudo udevadm settle --timeout=30 || true
  sleep 2
  run_step mkfs_vfat sudo mkfs.vfat -F 32 -n "${fat_label}" "$PART_DEV"
  run_step partprobe_after_mkfs sudo partprobe "$TARGET" || true
  run_step udev_settle_after_mkfs sudo udevadm settle --timeout=30 || true
  sleep 1

  FSTYPE="$(lsblk -no FSTYPE "$PART_DEV" 2>/dev/null | head -1 || true)"
  [[ "$FSTYPE" == "vfat" ]] || die "${PART_DEV} not vfat (${FSTYPE})" 31

  LABEL="$(sudo blkid -p -s LABEL -o value "$PART_DEV" 2>/dev/null || true)"
  if [[ "$LABEL" != "$fat_label" ]]; then
    sudo fatlabel "$PART_DEV" "$fat_label" 2>/dev/null || sudo dosfslabel "$PART_DEV" "$fat_label"
  fi

  FAT_UUID="$(sudo blkid -p -s UUID -o value "$PART_DEV")"
  [[ -n "$FAT_UUID" ]] || die "FAT UUID missing on ${PART_DEV}" 32
  echo "FAT_UUID=${FAT_UUID}" | tee -a "$WRITE_LOG"

  run_step patch_grub_uuid "${SCRIPT_DIR}/patch-fat32-esp-grub-for-uuid.sh" \
    --staging "$STAGING_DIR" --fat-uuid "$FAT_UUID"

  MNT="$(mktemp -d)"
  run_step mount_esp sudo mount "$PART_DEV" "$MNT"

  local rsync_cmd
  rsync_cmd="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import fat32_staging_rsync_command
print(fat32_staging_rsync_command(staging=${STAGING_DIR@Q}, mount=${MNT@Q}, sudo=True))
PY
)"
  run_step rsync_staging bash -lc "$rsync_cmd"
  run_step sync sync
  run_step umount_esp sudo umount "$MNT"
  rmdir "$MNT"
  MNT=""

  sync
  sudo partprobe "$TARGET" || true
  sudo udevadm settle --timeout=30 || true

  record_post_state

  if ! "${SCRIPT_DIR}/verify-fat32-esp-rescue-usb.sh" --target "$TARGET" --partition "$PART_DEV" \
    >"${EVIDENCE_DIR}/verify.log" 2>&1; then
    FAILED_STEP="verify_fat32_esp"
    cat "${EVIDENCE_DIR}/verify.log" >&2
    return 1
  fi
  echo "OK: verify_fat32_esp" | tee -a "$WRITE_LOG"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --operator-confirm-write) CONFIRM_WRITE=true; DRY_RUN=false; shift ;;
    --execute-write) EXECUTE_WRITE=true; shift ;;
    --confirm-phrase) CONFIRM_PHRASE="$2"; shift 2 ;;
    --esp-size-mib) ESP_SIZE_MIB="$2"; shift 2 ;;
    --staging-dir) STAGING_DIR="$2"; shift 2 ;;
    --expected-iso-sha256) EXPECTED_ISO_SHA256="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$ISO" && -n "$TARGET" ]] || usage
[[ -f "$ISO" ]] || die "ISO missing: $ISO" 21

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

PART_DEV="$(partition_path_for_target "$TARGET" 1)"

PLAN_JSON="$(mktemp)"
trap 'rm -f "$PLAN_JSON"' EXIT

if [[ "$DRY_RUN" == true ]]; then
  DRY_PY=True
else
  DRY_PY=False
fi

python3 - <<PY >"$PLAN_JSON"
import json
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import build_write_plan

plan = build_write_plan(
    iso_path=Path(${ISO@Q}),
    target_device=${TARGET@Q},
    staging_dir=Path(${STAGING_DIR@Q}),
    esp_size_mib=int(${ESP_SIZE_MIB}),
    dry_run=${DRY_PY},
    confirm_phrase=${CONFIRM_PHRASE@Q} or None,
)
print(json.dumps(plan, indent=2))
PY

echo "=== FAT32 ESP USB Writer Plan ==="
cat "$PLAN_JSON"

if [[ "$DRY_RUN" == true ]]; then
  echo "OK: dry-run complete — no device write performed"
  echo "write_executed=false"
  exit 0
fi

BLOCKED="$(python3 - <<PY
import json
from pathlib import Path
plan = json.loads(Path(${PLAN_JSON@Q}).read_text())
print("yes" if plan.get("safety", {}).get("blocked") else "no")
PY
)"

if [[ "$BLOCKED" == "yes" ]]; then
  echo "ERROR: write blocked by safety checks — see plan JSON" >&2
  exit 27
fi

if [[ "$CONFIRM_WRITE" != true ]]; then
  echo "ERROR: --operator-confirm-write required for destructive mode" >&2
  exit 27
fi

if [[ ! -f "${STAGING_DIR}/EFI/BOOT/BOOTX64.EFI" ]]; then
  echo "=== Building staging layout ==="
  "${SCRIPT_DIR}/build-fat32-esp-usb-layout.sh" --iso "$ISO" --output-dir "$STAGING_DIR"
fi

if [[ "$EXECUTE_WRITE" != true ]]; then
  echo "=== DESTRUCTIVE WRITE PREPARED (operator terminal only) ==="
  echo "Target: ${TARGET} partition: ${PART_DEV}"
  echo "NOTE: Add --execute-write to run steps automatically (still requires operator terminal)."
  echo ""
  python3 - <<PY
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import build_operator_terminal_commands

cmds = build_operator_terminal_commands(
    iso_path=Path(${ISO@Q}),
    target_device=${TARGET@Q},
    workspace=Path(${REPO_ROOT@Q}),
)
print(cmds["write_manual"])
PY
  echo ""
  echo "write_executed=false (use --execute-write to execute automatically)"
  exit 0
fi

GATES_JSON="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import (
    load_operator_selection_evidence,
    validate_fat32_execute_write_gates,
)

ws = Path(${REPO_ROOT@Q})
evidence = load_operator_selection_evidence(ws)
gates = validate_fat32_execute_write_gates(
    target_device=${TARGET@Q},
    iso_path=Path(${ISO@Q}),
    staging_dir=Path(${STAGING_DIR@Q}),
    operator_evidence=evidence,
    confirm_phrase=${CONFIRM_PHRASE@Q} or None,
    execute_write=True,
    confirm_write=True,
    expected_iso_sha256=${EXPECTED_ISO_SHA256@Q},
)
print(json.dumps(gates, indent=2))
PY
)"

echo "=== FAT32 ESP execute-write gates ==="
echo "$GATES_JSON"

GATES_BLOCKED="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('blocked') else 'no')" <<<"$GATES_JSON")"
if [[ "$GATES_BLOCKED" == "yes" ]]; then
  echo "ERROR: execute-write blocked — see gates JSON" >&2
  exit 28
fi

RUN_ID="fat32_esp_write_$(date -u +%Y%m%d_%H%M%S)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_ID}"
mkdir -p "$EVIDENCE_DIR"
cp "$PLAN_JSON" "${EVIDENCE_DIR}/plan.json"
WRITE_LOG="${EVIDENCE_DIR}/write_steps.log"
: >"$WRITE_LOG"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "=== FAT32 ESP execute-write starting ==="
echo "EVIDENCE_DIR=${EVIDENCE_DIR}"
echo "TARGET=${TARGET} PART=${PART_DEV}"

VERIFY_STATUS="not_run"
WRITE_STATUS="failed"
if execute_fat32_esp_write; then
  WRITE_STATUS="success"
  VERIFY_STATUS="success"
else
  if [[ "$FAILED_STEP" == "verify_fat32_esp" ]]; then
    VERIFY_STATUS="failed"
    WRITE_STATUS="failed"
  fi
fi

EVIDENCE_STATUS="complete"
if ! FINALIZE_JSON="$(finalize_write_evidence "$WRITE_STATUS" "$VERIFY_STATUS" "$([[ "$WRITE_STATUS" == success ]] && echo true || echo false)")"; then
  EVIDENCE_STATUS="review_required"
  echo "WARN: evidence report generation failed — write/verify status preserved" >&2
  echo "evidence_status=${EVIDENCE_STATUS}" >&2
elif [[ -n "$FINALIZE_JSON" ]]; then
  EVIDENCE_STATUS="$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('evidence_status','complete'))" "$FINALIZE_JSON")"
fi

if [[ "$WRITE_STATUS" != "success" ]]; then
  echo "ERROR: FAT32 ESP write failed at step: ${FAILED_STEP:-unknown}" >&2
  exit 29
fi

echo "OK: FAT32 ESP write complete — evidence: ${EVIDENCE_DIR}"
echo "write_executed=true"
echo "rs001_status=red (hardware boot not yet proven)"
exit 0
