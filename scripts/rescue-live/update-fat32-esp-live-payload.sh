#!/usr/bin/env bash
# FAT32 ESP live payload update — squashfs/evidence only (no partition rewrite).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVIDENCE_ROOT="${REPO_ROOT}/docs/evidence/runtime-results/rescue"

TARGET=""
NEW_SQUASHFS=""
CONFIRM_UPDATE=false
EXECUTE_UPDATE=false
CONFIRM_PHRASE=""
PART_DEV=""
MNT=""
EVIDENCE_DIR=""
STARTED_AT=""
FAILED_STEP=""
WRITE_ERRORS_DETECTED=false
STICK_SHA_AFTER=""
UPDATE_STATUS="failed"
VERIFY_STATUS="not_run"
PAYLOAD_EXECUTED=false
PAYLOAD_COPIED=false
METADATA_WRITTEN=false
STAGING_CLEANED=false
usage() {
  cat <<EOF
Usage: $0 --target /dev/sdX --new-squashfs PATH [options]

Options:
  --operator-confirm-update       Required for write mode
  --confirm-phrase PHRASE         Must be: UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD
  --execute-update                Run payload copy (operator terminal only)

Without --execute-update: plan only, payload_update_executed=false.
No partition rewrite, format, or full-stick imaging.

DCC/Agent must NOT invoke --execute-update automatically.
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

cleanup_mount() {
  if [[ -n "${MNT:-}" && -d "${MNT:-}" ]]; then
    sudo umount "$MNT" 2>/dev/null || true
    rmdir "$MNT" 2>/dev/null || true
    MNT=""
  fi
}

record_file() {
  local dest="$1"
  shift
  { echo "=== $(basename "$dest") ==="; "$@"; } >"$dest" 2>&1 || true
}

run_step() {
  local desc="$1"
  shift
  echo "STEP: ${desc}" | tee -a "${EVIDENCE_DIR}/copy.log"
  if ! "$@" >>"${EVIDENCE_DIR}/copy.log" 2>&1; then
    FAILED_STEP="$desc"
    WRITE_ERRORS_DETECTED=true
    echo "FAILED: ${desc} (exit $?)" | tee -a "${EVIDENCE_DIR}/copy.log" >&2
    return 1
  fi
  echo "OK: ${desc}" | tee -a "${EVIDENCE_DIR}/copy.log"
  return 0
}

write_result_json() {
  local status="$1" verify_status="$2" executed="$3" old_sha="$4" new_sha="$5" stick_sha="$6"
  export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
  FAT32_EVIDENCE_DIR="$EVIDENCE_DIR" \
  FAT32_TARGET="$TARGET" \
  FAT32_STARTED_AT="$STARTED_AT" \
  FAT32_STATUS="$status" \
  FAT32_VERIFY_STATUS="$verify_status" \
  FAT32_EXECUTED="$executed" \
  FAT32_OLD_SHA="$old_sha" \
  FAT32_NEW_SHA="$new_sha" \
  FAT32_STICK_SHA="$stick_sha" \
  FAT32_FAILED_STEP="${FAILED_STEP:-}" \
  FAT32_WRITE_ERRORS="${WRITE_ERRORS_DETECTED}" \
  FAT32_PAYLOAD_COPIED="${PAYLOAD_COPIED}" \
  FAT32_METADATA_WRITTEN="${METADATA_WRITTEN}" \
  FAT32_STAGING_CLEANED="${STAGING_CLEANED}" \
  python3 - <<'PY'
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.rescue_fat32_esp_payload_update import build_payload_update_result

def _bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")

result = build_payload_update_result(
    target_device=os.environ["FAT32_TARGET"],
    old_squashfs_sha256=os.environ.get("FAT32_OLD_SHA") or None,
    new_squashfs_sha256=os.environ.get("FAT32_NEW_SHA") or None,
    stick_squashfs_sha256=os.environ.get("FAT32_STICK_SHA") or None,
    started_at=os.environ["FAT32_STARTED_AT"],
    completed_at=datetime.now(tz=timezone.utc).isoformat(),
    payload_update_executed=_bool("FAT32_EXECUTED"),
    payload_update_status=os.environ["FAT32_STATUS"],
    verify_status=os.environ["FAT32_VERIFY_STATUS"],
    evidence_dir=os.environ["FAT32_EVIDENCE_DIR"],
    failed_step=os.environ.get("FAT32_FAILED_STEP") or None,
    write_errors_detected=_bool("FAT32_WRITE_ERRORS"),
    payload_copied=_bool("FAT32_PAYLOAD_COPIED"),
    metadata_written=_bool("FAT32_METADATA_WRITTEN"),
    staging_artifacts_cleaned=_bool("FAT32_STAGING_CLEANED"),
)
out_dir = Path(os.environ["FAT32_EVIDENCE_DIR"])
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
latest = Path(os.environ["FAT32_EVIDENCE_DIR"]).parents[0] / "fat32_esp_payload_update_latest.json"
latest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"payload_update_status": result["payload_update_status"], "verify_status": result["verify_status"]}))
PY
}

execute_payload_update() {
  local new_sq="$1"
  local new_sha_expected="$2"
  local old_sq_path="${MNT}/live/filesystem.squashfs"
  local tmp_dir="${MNT}/.sqtmp"
  local new_tmp="${tmp_dir}/filesystem.squashfs.new"
  local evidence_path="${MNT}/setuphelfer/rescue/evidence.json"
  local version_path="${MNT}/setuphelfer/rescue/version.json"
  local meta_tmp
  meta_tmp="$(mktemp -d)"

  OLD_SHA="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import sha256_file
from pathlib import Path
p = Path(${old_sq_path@Q})
print(sha256_file(p) if p.is_file() else "")
PY
)"
  echo "OLD_SQUASHFS_SHA256=${OLD_SHA}" | tee -a "${EVIDENCE_DIR}/copy.log"

  run_step "mkdir_sqtmp" sudo mkdir -p "$tmp_dir" || return 1
  run_step "cp_squashfs_new" sudo cp -f "$new_sq" "$new_tmp" || return 1
  sync
  run_step "mv_squashfs_atomic" sudo mv -f "$new_tmp" "$old_sq_path" || return 1
  sync

  STICK_SHA_AFTER="$(sha256sum "$old_sq_path" | awk '{print $1}')"
  echo "STICK_SQUASHFS_SHA256_AFTER=${STICK_SHA_AFTER}" | tee -a "${EVIDENCE_DIR}/copy.log"
  if [[ "$STICK_SHA_AFTER" != "$new_sha_expected" ]]; then
    FAILED_STEP="squashfs_hash_mismatch"
    WRITE_ERRORS_DETECTED=true
    echo "FAILED: squashfs hash mismatch expected=${new_sha_expected} actual=${STICK_SHA_AFTER}" \
      | tee -a "${EVIDENCE_DIR}/copy.log" >&2
    return 1
  fi

  if ! python3 - <<PY >>"${EVIDENCE_DIR}/copy.log" 2>&1
import json
from pathlib import Path
from core.rescue_fat32_esp_payload_update import build_updated_stick_evidence

mount = Path(${MNT@Q})
meta = Path(${meta_tmp@Q})
evidence_path = mount / "setuphelfer/rescue/evidence.json"
version_path = mount / "setuphelfer/rescue/version.json"
existing = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.is_file() else {}
version_payload = json.loads(version_path.read_text(encoding="utf-8")) if version_path.is_file() else {}
project_version = version_payload.get("project_version", "1.7.9.4")
updated = build_updated_stick_evidence(
    medium_evidence=existing,
    new_squashfs=Path(${new_sq@Q}),
    project_version=project_version,
)
(meta / "evidence.json").write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
version_payload["project_version"] = project_version
version_payload["payload_updated_at"] = updated.get("payload_updated_at")
(meta / "version.json").write_text(json.dumps(version_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"evidence_prepared": True, "new_sha256": updated["files"][-1]["sha256"] if updated.get("files") else None}))
PY
  then
    FAILED_STEP="metadata_prepare"
    WRITE_ERRORS_DETECTED=true
    return 1
  fi

  run_step "cp_evidence_json" sudo cp -f "${meta_tmp}/evidence.json" "$evidence_path" || return 1
  run_step "cp_version_json" sudo cp -f "${meta_tmp}/version.json" "$version_path" || return 1
  rm -rf "$meta_tmp"
  PAYLOAD_COPIED=true
  METADATA_WRITTEN=true

  run_step "cleanup_sqtmp" sudo rm -rf "$tmp_dir" || return 1
  if [[ -d "$tmp_dir" || -e "$tmp_dir" ]]; then
    FAILED_STEP="cleanup_sqtmp"
    WRITE_ERRORS_DETECTED=true
    echo "FAILED: .sqtmp still present after cleanup" | tee -a "${EVIDENCE_DIR}/copy.log" >&2
    return 1
  fi
  STAGING_CLEANED=true
  echo "OK: staging artifacts cleaned" | tee -a "${EVIDENCE_DIR}/copy.log"

  python3 - <<PY >"${EVIDENCE_DIR}/old_payload_hashes.json"
import json
print(json.dumps({"live/filesystem.squashfs": ${OLD_SHA@Q}}, indent=2))
PY
  python3 - <<PY >"${EVIDENCE_DIR}/new_payload_hashes.json"
import json
print(json.dumps({"live/filesystem.squashfs": ${STICK_SHA_AFTER@Q}}, indent=2))
PY

  sync
  sudo umount "$MNT"
  MNT=""

  if ! "${SCRIPT_DIR}/verify-fat32-esp-rescue-usb.sh" --target "$TARGET" --partition "$PART_DEV" \
    --expected-squashfs-sha256 "$new_sha_expected" \
    >"${EVIDENCE_DIR}/verify.log" 2>&1; then
    FAILED_STEP="verify_fat32_esp"
    WRITE_ERRORS_DETECTED=true
    return 1
  fi
  echo "OK: verify with expected squashfs hash" | tee -a "${EVIDENCE_DIR}/copy.log"
  return 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --new-squashfs) NEW_SQUASHFS="$2"; shift 2 ;;
    --operator-confirm-update) CONFIRM_UPDATE=true; shift ;;
    --execute-update) EXECUTE_UPDATE=true; shift ;;
    --confirm-phrase) CONFIRM_PHRASE="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) die "Unknown arg: $1" 21 ;;
  esac
done

[[ -n "$TARGET" && -n "$NEW_SQUASHFS" ]] || usage
[[ -f "$NEW_SQUASHFS" ]] || die "new squashfs missing: $NEW_SQUASHFS" 22

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
PART_DEV="$(partition_path_for_target "$TARGET" 1)"

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
    return ""

from core.rescue_fat32_esp_payload_update import validate_payload_update_target_probe

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

echo "=== FAT32 ESP payload update safety ==="
echo "$PROBE_JSON"

if [[ "$CONFIRM_UPDATE" == true ]]; then PAYLOAD_CONFIRM_PY=True; else PAYLOAD_CONFIRM_PY=False; fi
if [[ "$EXECUTE_UPDATE" == true ]]; then PAYLOAD_EXECUTE_PY=True; else PAYLOAD_EXECUTE_PY=False; fi

PROBE_FILE="$(mktemp)"
echo "$PROBE_JSON" >"$PROBE_FILE"
export FAT32_PROBE_FILE="$PROBE_FILE"
export FAT32_TARGET="$TARGET"
export FAT32_NEW_SQUASHFS="$NEW_SQUASHFS"
export FAT32_CONFIRM_PHRASE="$CONFIRM_PHRASE"
export FAT32_CONFIRM_UPDATE="$PAYLOAD_CONFIRM_PY"
export FAT32_EXECUTE_UPDATE="$PAYLOAD_EXECUTE_PY"

PLAN_JSON="$(python3 - <<'PY'
import json
import os
from pathlib import Path

from core.rescue_fat32_esp_payload_update import build_payload_update_plan

safety = json.loads(Path(os.environ["FAT32_PROBE_FILE"]).read_text(encoding="utf-8"))
plan = build_payload_update_plan(
    target_device=os.environ["FAT32_TARGET"],
    new_squashfs=Path(os.environ["FAT32_NEW_SQUASHFS"]),
    confirm_phrase=os.environ.get("FAT32_CONFIRM_PHRASE") or None,
    confirm_update=os.environ.get("FAT32_CONFIRM_UPDATE") == "True",
    execute_update=os.environ.get("FAT32_EXECUTE_UPDATE") == "True",
    safety=safety,
)
print(json.dumps(plan, indent=2))
PY
)"
rm -f "$PROBE_FILE"
unset FAT32_PROBE_FILE

echo "=== FAT32 ESP payload update plan ==="
echo "$PLAN_JSON"

BLOCKED="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('blocked') else 'no')" <<<"$PLAN_JSON")"
if [[ "$BLOCKED" == "yes" ]]; then
  echo "ERROR: payload update blocked" >&2
  exit 27
fi

if [[ "$EXECUTE_UPDATE" != true ]]; then
  echo "payload_update_executed=false (use --execute-update to apply)"
  exit 0
fi

RUN_ID="fat32_esp_payload_update_$(date -u +%Y%m%d_%H%M%S)"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${RUN_ID}"
mkdir -p "$EVIDENCE_DIR"
echo "$PLAN_JSON" >"${EVIDENCE_DIR}/plan.json"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
: >"${EVIDENCE_DIR}/copy.log"

record_file "${EVIDENCE_DIR}/pre_lsblk.txt" lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,LABEL,PARTTYPENAME,MOUNTPOINTS "$TARGET"
cp "${EVIDENCE_DIR}/pre_lsblk.txt" "${EVIDENCE_DIR}/pre_blkid.txt"
sudo blkid -p "$PART_DEV" >>"${EVIDENCE_DIR}/pre_blkid.txt" 2>&1 || blkid -p "$PART_DEV" >>"${EVIDENCE_DIR}/pre_blkid.txt" 2>&1 || true

MNT="$(mktemp -d)"
trap cleanup_mount EXIT
sudo mount "$PART_DEV" "$MNT"

OLD_SHA=""
NEW_SHA="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import sha256_file
from pathlib import Path
print(sha256_file(Path(${NEW_SQUASHFS@Q})))
PY
)"

if execute_payload_update "$NEW_SQUASHFS" "$NEW_SHA"; then
  UPDATE_STATUS="success"
  VERIFY_STATUS="success"
  PAYLOAD_EXECUTED=true
  OLD_SHA="$(python3 -c "import json; print(json.load(open('${EVIDENCE_DIR}/old_payload_hashes.json')).get('live/filesystem.squashfs',''))")"
else
  PAYLOAD_EXECUTED=false
  if [[ "$FAILED_STEP" == "verify_fat32_esp" ]]; then
    VERIFY_STATUS="failed"
    UPDATE_STATUS="failed"
  elif [[ "$PAYLOAD_COPIED" == true && "$METADATA_WRITTEN" == true && "$STICK_SHA_AFTER" == "$NEW_SHA" ]]; then
    PAYLOAD_EXECUTED=true
    if [[ "$STAGING_CLEANED" != true ]]; then
      UPDATE_STATUS="failed"
      VERIFY_STATUS="failed"
      [[ -z "$FAILED_STEP" ]] && FAILED_STEP="cleanup_sqtmp"
    else
      UPDATE_STATUS="review_required"
      VERIFY_STATUS="review_required"
    fi
  else
    UPDATE_STATUS="failed"
    if [[ "$VERIFY_STATUS" == "not_run" ]]; then
      VERIFY_STATUS="review_required"
    fi
  fi
fi

write_result_json "$UPDATE_STATUS" "$VERIFY_STATUS" "$PAYLOAD_EXECUTED" "$OLD_SHA" "$NEW_SHA" "$STICK_SHA_AFTER"

record_file "${EVIDENCE_DIR}/post_lsblk.txt" lsblk -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,FSTYPE,LABEL,PARTTYPENAME,MOUNTPOINTS "$TARGET"
cp "${EVIDENCE_DIR}/post_lsblk.txt" "${EVIDENCE_DIR}/post_blkid.txt"
sudo blkid -p "$PART_DEV" >>"${EVIDENCE_DIR}/post_blkid.txt" 2>&1 || true

if [[ "$UPDATE_STATUS" != "success" ]]; then
  echo "ERROR: payload update failed at: ${FAILED_STEP:-unknown}" >&2
  exit 29
fi

echo "OK: FAT32 ESP payload update complete — evidence: ${EVIDENCE_DIR}"
echo "payload_update_executed=true"
echo "rs001_status=yellow (hardware retest pending)"
exit 0
