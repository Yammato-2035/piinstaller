#!/usr/bin/env bash
# FAT32 ESP GRUB branding update — theme/grub.cfg/BOOTX64 only (no partition rewrite).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVIDENCE_ROOT="${REPO_ROOT}/docs/evidence/runtime-results/rescue"

TARGET=""
CONFIRM_UPDATE=false
EXECUTE_UPDATE=false
CONFIRM_PHRASE=""
ALLOW_MOUNTED=false
PART_DEV=""
MNT=""
EVIDENCE_DIR=""
STARTED_AT=""
FAILED_STEP=""
UPDATE_STATUS="failed"
VERIFY_STATUS="not_run"
BRANDING_EXECUTED=false

usage() {
  cat <<EOF
Usage: $0 --target /dev/sdX [options]

Options:
  --operator-confirm-update       Required for write mode
  --confirm-phrase PHRASE         Must be: UPDATE SETUPHELFER FAT32 ESP GRUB BRANDING
  --execute-update                Apply branding (operator terminal only)
  --allow-mounted                 Allow update while partition is user-mounted (udisksctl rw)

Without --execute-update: plan only, grub_branding_update_executed=false.
No partition rewrite, format, or full-stick imaging.
EOF
  exit 20
}

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

partition_path_for_target() {
  python3 - <<PY
from core.rescue_fat32_esp_usb_writer import partition_path_for_target
print(partition_path_for_target(${1@Q}, 1))
PY
}

mount_partition_rw() {
  local part="$1"
  MNT="$(lsblk -no MOUNTPOINTS "$part" 2>/dev/null | head -1 || true)"
  if [[ -n "$MNT" && -d "$MNT" ]]; then
    if [[ "$ALLOW_MOUNTED" == true ]]; then
      udisksctl mount -b "$part" --options rw >/dev/null 2>&1 || true
      MNT="$(lsblk -no MOUNTPOINTS "$part" 2>/dev/null | head -1 || true)"
      [[ -n "$MNT" && -w "$MNT" ]] || die "mounted partition not writable: $part" 32
      return 0
    fi
    die "partition already mounted — unmount or pass --allow-mounted" 31
  fi
  MNT="$(mktemp -d)"
  if command -v udisksctl >/dev/null 2>&1; then
    udisksctl mount -b "$part" --options rw >/dev/null
    MNT="$(lsblk -no MOUNTPOINTS "$part" 2>/dev/null | head -1 || true)"
    [[ -n "$MNT" && -d "$MNT" ]] || die "udisksctl rw mount failed" 32
  elif sudo -n mount "$part" "$MNT" 2>/dev/null; then
    :
  else
    die "rw mount failed (need udisksctl or passwordless sudo)" 32
  fi
}

cleanup_mount() {
  if [[ "$ALLOW_MOUNTED" == true ]]; then
    sync || true
    return 0
  fi
  if [[ -n "${MNT:-}" && -d "${MNT:-}" ]]; then
    if lsblk -no MOUNTPOINTS "$PART_DEV" 2>/dev/null | grep -q .; then
      udisksctl unmount -b "$PART_DEV" >/dev/null 2>&1 || sudo umount "$MNT" 2>/dev/null || true
    fi
    if [[ "$MNT" == /tmp/* || "$MNT" == /var/tmp/* ]]; then
      rmdir "$MNT" 2>/dev/null || true
    fi
    MNT=""
  fi
}

write_result_json() {
  local status="$1" verify_status="$2" executed="$3" apply_json="$4"
  export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
  FAT32_EVIDENCE_DIR="$EVIDENCE_DIR" \
  FAT32_TARGET="$TARGET" \
  FAT32_STARTED_AT="$STARTED_AT" \
  FAT32_STATUS="$status" \
  FAT32_VERIFY_STATUS="$verify_status" \
  FAT32_EXECUTED="$executed" \
  FAT32_APPLY_JSON="$apply_json" \
  FAT32_FAILED_STEP="${FAILED_STEP:-}" \
  python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.rescue_fat32_esp_grub_branding_update import build_grub_branding_update_result

apply = json.loads(os.environ.get("FAT32_APPLY_JSON") or "{}")
executed = os.environ.get("FAT32_EXECUTED", "").lower() in ("1", "true", "yes")
result = build_grub_branding_update_result(
    target_device=os.environ["FAT32_TARGET"],
    started_at=os.environ["FAT32_STARTED_AT"],
    completed_at=datetime.now(tz=timezone.utc).isoformat(),
    grub_branding_update_executed=executed,
    grub_branding_update_status=os.environ["FAT32_STATUS"],
    verify_status=os.environ["FAT32_VERIFY_STATUS"],
    evidence_dir=os.environ["FAT32_EVIDENCE_DIR"],
    apply_result=apply,
    failed_step=os.environ.get("FAT32_FAILED_STEP") or None,
)
out_dir = Path(os.environ["FAT32_EVIDENCE_DIR"])
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
latest = out_dir.parent / "fat32_esp_grub_branding_update_latest.json"
latest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"grub_branding_update_status": result["grub_branding_update_status"], "verify_status": result["verify_status"]}))
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --operator-confirm-update) CONFIRM_UPDATE=true; shift ;;
    --execute-update) EXECUTE_UPDATE=true; shift ;;
    --confirm-phrase) CONFIRM_PHRASE="$2"; shift 2 ;;
    --allow-mounted) ALLOW_MOUNTED=true; shift ;;
    -h|--help) usage ;;
    *) die "Unknown arg: $1" 21 ;;
  esac
done

[[ -n "$TARGET" ]] || usage

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
PART_DEV="$(partition_path_for_target "$TARGET")"

PROBE_JSON="$(python3 - <<PY
import json
import subprocess

def field(dev, name):
    p = subprocess.run(["lsblk", "-no", name, dev], capture_output=True, text=True, check=False)
    return (p.stdout or "").strip().splitlines()[0] if (p.stdout or "").strip() else ""

def blk(key):
    for cmd in (["sudo", "blkid", "-p", "-s", key, "-o", "value", ${PART_DEV@Q}], ["blkid", "-p", "-s", key, "-o", "value", ${PART_DEV@Q}]):
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        v = (p.stdout or "").strip().strip('"')
        if v:
            return v
    return field(${PART_DEV@Q}, "UUID") if key == "UUID" else ""

from core.rescue_fat32_esp_grub_branding_update import validate_payload_update_target_probe

probe = validate_payload_update_target_probe(
    target_device=${TARGET@Q},
    partition_device=${PART_DEV@Q},
    transport=field(${TARGET@Q}, "TRAN"),
    size=field(${TARGET@Q}, "SIZE"),
    model=field(${TARGET@Q}, "MODEL"),
    serial=field(${TARGET@Q}, "SERIAL"),
    fstype=field(${PART_DEV@Q}, "FSTYPE"),
    label=blk("LABEL") or field(${PART_DEV@Q}, "LABEL"),
    parttypename=field(${PART_DEV@Q}, "PARTTYPENAME"),
    gpt_partname=blk("PART_ENTRY_NAME"),
    mountpoints=[m for m in field(${PART_DEV@Q}, "MOUNTPOINTS").split() if m],
)
print(json.dumps(probe, indent=2))
PY
)"

echo "=== FAT32 ESP GRUB branding update safety ==="
echo "$PROBE_JSON"

if [[ "$CONFIRM_UPDATE" == true ]]; then BR_CONFIRM_PY=True; else BR_CONFIRM_PY=False; fi
if [[ "$EXECUTE_UPDATE" == true ]]; then BR_EXECUTE_PY=True; else BR_EXECUTE_PY=False; fi
if [[ "$ALLOW_MOUNTED" == true ]]; then BR_ALLOW_MOUNTED=True; else BR_ALLOW_MOUNTED=False; fi

PROBE_FILE="$(mktemp)"
echo "$PROBE_JSON" >"$PROBE_FILE"
export FAT32_PROBE_FILE="$PROBE_FILE"
export FAT32_TARGET="$TARGET"
export FAT32_CONFIRM_PHRASE="$CONFIRM_PHRASE"
export FAT32_CONFIRM_UPDATE="$BR_CONFIRM_PY"
export FAT32_EXECUTE_UPDATE="$BR_EXECUTE_PY"
export FAT32_ALLOW_MOUNTED="$BR_ALLOW_MOUNTED"

PLAN_JSON="$(python3 - <<'PY'
import json
import os
from pathlib import Path

from core.rescue_fat32_esp_grub_branding_update import build_grub_branding_update_plan

safety = json.loads(Path(os.environ["FAT32_PROBE_FILE"]).read_text(encoding="utf-8"))
plan = build_grub_branding_update_plan(
    target_device=os.environ["FAT32_TARGET"],
    confirm_phrase=os.environ.get("FAT32_CONFIRM_PHRASE") or None,
    confirm_update=os.environ.get("FAT32_CONFIRM_UPDATE") == "True",
    execute_update=os.environ.get("FAT32_EXECUTE_UPDATE") == "True",
    safety=safety,
    allow_mounted=os.environ.get("FAT32_ALLOW_MOUNTED") == "True",
)
print(json.dumps(plan, indent=2))
PY
)"
rm -f "$PROBE_FILE"

echo "=== FAT32 ESP GRUB branding update plan ==="
echo "$PLAN_JSON"

BLOCKED="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('blocked') else 'no')" <<<"$PLAN_JSON")"
if [[ "$BLOCKED" == "yes" && "$EXECUTE_UPDATE" == true ]]; then
  echo "ERROR: GRUB branding update blocked" >&2
  exit 27
fi

if [[ "$EXECUTE_UPDATE" != true ]]; then
  echo "grub_branding_update_executed=false (use --execute-update to apply)"
  exit 0
fi

RUN_ID="fat32_esp_grub_branding_update_$(date -u +%Y%m%d_%H%M%S)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_ID}"
mkdir -p "$EVIDENCE_DIR"
echo "$PLAN_JSON" >"${EVIDENCE_DIR}/plan.json"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
: >"${EVIDENCE_DIR}/copy.log"

lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,LABEL,PARTTYPENAME,MOUNTPOINTS "$TARGET" \
  >"${EVIDENCE_DIR}/pre_lsblk.txt" 2>&1 || true

trap cleanup_mount EXIT
mount_partition_rw "$PART_DEV"
echo "MOUNT=$MNT" | tee -a "${EVIDENCE_DIR}/copy.log"

FAT_UUID="$(lsblk -no UUID "$PART_DEV" 2>/dev/null | head -1 || true)"
APPLY_JSON="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_fat32_esp_grub_branding_update import apply_grub_branding_on_mount

result = apply_grub_branding_on_mount(
    Path(${MNT@Q}),
    repo_root=Path(${REPO_ROOT@Q}),
    fat_uuid=${FAT_UUID@Q} or None,
)
print(json.dumps(result))
PY
)" 2>>"${EVIDENCE_DIR}/copy.log" || {
  FAILED_STEP="apply_grub_branding"
  UPDATE_STATUS="failed"
  write_result_json "$UPDATE_STATUS" "$VERIFY_STATUS" false "{}"
  die "GRUB branding apply failed" 29
}

echo "$APPLY_JSON" >"${EVIDENCE_DIR}/apply.json"
BRANDING_OK="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('branding_ok') else 'no')" <<<"$APPLY_JSON")"
if [[ "$BRANDING_OK" != "yes" ]]; then
  FAILED_STEP="branding_validation"
  UPDATE_STATUS="failed"
  write_result_json "$UPDATE_STATUS" "$VERIFY_STATUS" true "$APPLY_JSON"
  die "GRUB branding validation failed" 29
fi

sync
cleanup_mount
trap - EXIT

BRANDING_EXECUTED=true
UPDATE_STATUS="success"
VERIFY_STATUS="success"
write_result_json "$UPDATE_STATUS" "$VERIFY_STATUS" true "$APPLY_JSON"

echo "OK: GRUB branding update -> ${EVIDENCE_DIR}"
echo "grub_branding_update_status=${UPDATE_STATUS}"
