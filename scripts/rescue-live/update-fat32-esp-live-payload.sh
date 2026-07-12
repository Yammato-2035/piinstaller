#!/usr/bin/env bash
# FAT32 ESP live payload update — squashfs/evidence only (no partition rewrite).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
EVIDENCE_ROOT="${REPO_ROOT}/docs/evidence/runtime-results/rescue"

TARGET=""
NEW_SQUASHFS=""
EXPECTED_SHA=""
EXPECTED_VERSION=""
CONFIRM_UPDATE=false
EXECUTE_UPDATE=false
CONFIRM_PHRASE=""
PART_DEV=""
LOGS_PART_DEV=""
MNT=""
EVIDENCE_DIR=""
ORDER_EVIDENCE_DIR=""
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
SOURCE_REPORT_JSON=""
CANONICAL_VERSION=""
ROLLBACK_REQUIRED=false
ROLLBACK_SUCCESSFUL=""
usage() {
  cat <<EOF
Usage: $0 --target /dev/sdX --new-squashfs PATH [options]

Options:
  --expected-sha256 HEX           Expected source squashfs SHA256 (required for execute)
  --expected-version VERSION      Expected internal payload version (required for execute)
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
  local payload_version="$3"
  local old_sq_path="${MNT}/live/filesystem.squashfs"
  local tmp_dir="${MNT}/.sqtmp"
  local new_tmp="${tmp_dir}/filesystem.squashfs.new"
  local evidence_path="${MNT}/setuphelfer/rescue/evidence.json"
  local version_path="${MNT}/setuphelfer/rescue/version.json"
  local meta_tmp
  local prev_backup=""
  meta_tmp="$(mktemp -d)"
  ROLLBACK_REQUIRED=false
  ROLLBACK_SUCCESSFUL=""

  OLD_SHA="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import sha256_file
from pathlib import Path
p = Path(${old_sq_path@Q})
print(sha256_file(p) if p.is_file() else "")
PY
)"
  OLD_META_VERSION="$(python3 - <<PY
import json
from pathlib import Path
p = Path(${version_path@Q})
if p.is_file():
    d = json.loads(p.read_text(encoding="utf-8"))
    print(d.get("project_version") or d.get("rescue_payload_version") or "")
PY
)"
  echo "OLD_SQUASHFS_SHA256=${OLD_SHA}" | tee -a "${EVIDENCE_DIR}/copy.log"
  echo "OLD_METADATA_VERSION=${OLD_META_VERSION}" | tee -a "${EVIDENCE_DIR}/copy.log"

  run_step "mkdir_sqtmp" sudo mkdir -p "$tmp_dir" || return 1
  run_step "cp_squashfs_new" sudo cp -f "$new_sq" "$new_tmp" || return 1
  sync
  STICK_SHA_TMP="$(sha256sum "$new_tmp" | awk '{print $1}')"
  if [[ "$STICK_SHA_TMP" != "$new_sha_expected" ]]; then
    FAILED_STEP="temporary_payload_hash_mismatch"
    WRITE_ERRORS_DETECTED=true
    sudo rm -rf "$tmp_dir"
    return 1
  fi

  if ! python3 - <<PY >>"${EVIDENCE_DIR}/copy.log" 2>&1
import json
from pathlib import Path
from core.rescue_usb_payload_atomic_update import (
    build_atomic_esp_evidence_json,
    build_atomic_esp_version_json,
    validate_esp_metadata,
)

mount = Path(${MNT@Q})
meta = Path(${meta_tmp@Q})
evidence_path = mount / "setuphelfer/rescue/evidence.json"
version_path = mount / "setuphelfer/rescue/version.json"
existing_evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.is_file() else {}
existing_version = json.loads(version_path.read_text(encoding="utf-8")) if version_path.is_file() else {}
version_doc = build_atomic_esp_version_json(
    payload_version=${payload_version@Q},
    payload_sha256=${new_sha_expected@Q},
    existing=existing_version,
)
evidence_doc = build_atomic_esp_evidence_json(
    payload_version=${payload_version@Q},
    payload_sha256=${new_sha_expected@Q},
    payload_size_bytes=Path(${new_sq@Q}).stat().st_size,
    existing=existing_evidence,
)
gate = validate_esp_metadata(version_doc, expected_version=${payload_version@Q}, expected_sha256=${new_sha_expected@Q})
if not gate["ok"]:
    raise SystemExit("metadata_validation_failed:" + ",".join(gate.get("errors") or []))
(meta / "version.json").write_text(json.dumps(version_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(meta / "evidence.json").write_text(json.dumps(evidence_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"metadata_prepared": True, "project_version": version_doc["project_version"]}))
PY
  then
    FAILED_STEP="metadata_prepare"
    WRITE_ERRORS_DETECTED=true
    rm -rf "$meta_tmp"
    sudo rm -rf "$tmp_dir"
    return 1
  fi

  if [[ -f "$old_sq_path" && -n "$OLD_META_VERSION" ]]; then
    prev_backup="${MNT}/live/filesystem.squashfs.prev-${OLD_META_VERSION}"
    # Drop incomplete prev backups from aborted runs (size mismatch vs active)
    for partial in "${MNT}/live"/filesystem.squashfs.prev-*; do
      [[ -e "$partial" ]] || continue
      partial_size="$(stat -c%s "$partial" 2>/dev/null || echo 0)"
      old_size="$(stat -c%s "$old_sq_path" 2>/dev/null || echo 0)"
      if [[ "$partial_size" != "$old_size" && "$partial" != "$prev_backup" ]]; then
        echo "CLEANUP: removing incomplete prev $(basename "$partial") size=${partial_size}" | tee -a "${EVIDENCE_DIR}/copy.log"
        sudo rm -f "$partial"
      fi
    done
    # Enforce max-one-prev policy: remove oldest prev if another would be created
    mapfile -t existing_prevs < <(find "${MNT}/live" -maxdepth 1 -name 'filesystem.squashfs.prev-*' -printf '%f\n' 2>/dev/null | sort)
    if [[ ${#existing_prevs[@]} -ge 1 && ! -e "$prev_backup" ]]; then
      oldest="${MNT}/live/${existing_prevs[0]}"
      echo "POLICY: removing oldest prev $(basename "$oldest") to enforce max-one-prev" | tee -a "${EVIDENCE_DIR}/copy.log"
      sudo rm -f "$oldest"
    fi
    if [[ ! -e "$prev_backup" ]]; then
      # mv (not cp) frees space on size-constrained ESP before activating new payload
      run_step "backup_prev_payload" sudo mv -f "$old_sq_path" "$prev_backup" || return 1
    else
      echo "SKIP: prev backup already exists: ${prev_backup}" | tee -a "${EVIDENCE_DIR}/copy.log"
    fi
  fi

  run_step "mv_squashfs_atomic" sudo mv -f "$new_tmp" "$old_sq_path" || {
    # restore active payload from prev if mv to active failed
    if [[ -n "${prev_backup:-}" && -f "$prev_backup" && ! -f "$old_sq_path" ]]; then
      sudo mv -f "$prev_backup" "$old_sq_path" || true
    fi
    return 1
  }
  sync

  STICK_SHA_AFTER="$(sha256sum "$old_sq_path" | awk '{print $1}')"
  echo "STICK_SQUASHFS_SHA256_AFTER=${STICK_SHA_AFTER}" | tee -a "${EVIDENCE_DIR}/copy.log"
  if [[ "$STICK_SHA_AFTER" != "$new_sha_expected" ]]; then
    FAILED_STEP="squashfs_hash_mismatch"
    WRITE_ERRORS_DETECTED=true
    ROLLBACK_REQUIRED=true
    if [[ -n "$prev_backup" && -f "$prev_backup" ]]; then
      sudo cp -f "$prev_backup" "$old_sq_path" && ROLLBACK_SUCCESSFUL=true || ROLLBACK_SUCCESSFUL=false
    fi
    return 1
  fi
  PAYLOAD_COPIED=true

  if ! run_step "cp_evidence_json" sudo cp -f "${meta_tmp}/evidence.json" "$evidence_path"; then
    ROLLBACK_REQUIRED=true
    if [[ -n "$prev_backup" && -f "$prev_backup" ]]; then
      sudo cp -f "$prev_backup" "$old_sq_path" && ROLLBACK_SUCCESSFUL=true || ROLLBACK_SUCCESSFUL=false
    fi
    return 1
  fi
  if ! run_step "cp_version_json" sudo cp -f "${meta_tmp}/version.json" "$version_path"; then
    ROLLBACK_REQUIRED=true
    if [[ -n "$prev_backup" && -f "$prev_backup" ]]; then
      sudo cp -f "$prev_backup" "$old_sq_path" && ROLLBACK_SUCCESSFUL=true || ROLLBACK_SUCCESSFUL=false
    fi
    return 1
  fi
  rm -rf "$meta_tmp"
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
    --expected-sha256) EXPECTED_SHA="$2"; shift 2 ;;
    --expected-version) EXPECTED_VERSION="$2"; shift 2 ;;
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

SOURCE_REPORT_JSON="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_usb_payload_atomic_update import validate_source_payload

report = validate_source_payload(
    Path(${NEW_SQUASHFS@Q}),
    expected_sha256=${EXPECTED_SHA@Q} or None,
    expected_version=${EXPECTED_VERSION@Q} or None,
)
print(json.dumps(report))
PY
)"

echo "=== Source payload preflight ==="
echo "$SOURCE_REPORT_JSON"

SOURCE_BLOCKED="$(python3 -c "import json,sys; print('yes' if json.loads(sys.stdin.read()).get('blocked') else 'no')" <<<"$SOURCE_REPORT_JSON")"
if [[ "$SOURCE_BLOCKED" == "yes" ]]; then
  echo "ERROR: source payload preflight blocked" >&2
  exit 28
fi

CANONICAL_VERSION="$(python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('canonical_version',''))" <<<"$SOURCE_REPORT_JSON")"

PART_DEV="$(partition_path_for_target "$TARGET" 1)"
LOGS_PART_DEV="$(python3 - <<PY
from core.rescue_fat32_esp_usb_writer import partition_path_for_target
print(partition_path_for_target(${TARGET@Q}, 2))
PY
)"

PROBE_JSON="$(python3 - <<PY
import json
import subprocess

def field(dev, name):
    p = subprocess.run(["lsblk", "-no", name, dev], capture_output=True, text=True, check=False)
    return (p.stdout or "").strip().splitlines()[0] if (p.stdout or "").strip() else ""

def blk(key, dev):
    for cmd in (["sudo", "blkid", "-p", "-s", key, "-o", "value", dev], ["blkid", "-p", "-s", key, "-o", "value", dev]):
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        v = (p.stdout or "").strip().strip('"')
        if v:
            return v
    return ""

from core.rescue_fat32_esp_payload_update import validate_payload_update_target_probe
from core.rescue_usb_payload_atomic_update import validate_sibling_setup_logs_partition

probe = validate_payload_update_target_probe(
    target_device=${TARGET@Q},
    partition_device=${PART_DEV@Q},
    transport=field(${TARGET@Q}, "TRAN"),
    size=field(${TARGET@Q}, "SIZE"),
    model=field(${TARGET@Q}, "MODEL"),
    serial=field(${TARGET@Q}, "SERIAL"),
    fstype=field(${PART_DEV@Q}, "FSTYPE"),
    label=blk("LABEL", ${PART_DEV@Q}) or field(${PART_DEV@Q}, "LABEL"),
    parttypename=field(${PART_DEV@Q}, "PARTTYPENAME"),
    gpt_partname=blk("PART_ENTRY_NAME", ${PART_DEV@Q}),
    mountpoints=[m for m in field(${PART_DEV@Q}, "MOUNTPOINTS").split() if m],
)
logs = validate_sibling_setup_logs_partition(
    parent_device=${TARGET@Q},
    logs_label=blk("LABEL", ${LOGS_PART_DEV@Q}) or field(${LOGS_PART_DEV@Q}, "LABEL"),
    logs_fstype=field(${LOGS_PART_DEV@Q}, "FSTYPE"),
)
if logs.get("blocked"):
    probe = dict(probe)
    probe["blockers"] = sorted(set(list(probe.get("blockers") or []) + list(logs.get("blockers") or [])))
    probe["blocked"] = bool(probe["blockers"])
    probe["write_allowed"] = not probe["blocked"]
probe["setup_logs_sibling"] = logs
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

[[ -n "$EXPECTED_SHA" && -n "$EXPECTED_VERSION" ]] || die "execute requires --expected-sha256 and --expected-version" 24

ORDER_EVIDENCE_DIR="${REPO_ROOT}/docs/evidence/pi_rs_usb_updater_001"
mkdir -p "$ORDER_EVIDENCE_DIR"

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

if execute_payload_update "$NEW_SQUASHFS" "$NEW_SHA" "$CANONICAL_VERSION"; then
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

RB_REQ=$([[ "${ROLLBACK_REQUIRED}" == true ]] && echo True || echo False)
RB_OK=$([[ "${ROLLBACK_SUCCESSFUL}" == true ]] && echo True || echo False)
PAYLOAD_COPIED_PY=$([[ "${PAYLOAD_COPIED}" == true ]] && echo True || echo False)
METADATA_WRITTEN_PY=$([[ "${METADATA_WRITTEN}" == true ]] && echo True || echo False)

python3 - <<PY >"${ORDER_EVIDENCE_DIR}/usb_update_result.json"
import json
from pathlib import Path
from core.rescue_usb_payload_atomic_update import build_usb_updater_result

source = json.loads(${SOURCE_REPORT_JSON@Q})
result_path = Path(${EVIDENCE_DIR@Q}) / "result.json"
legacy = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
rollback_required = ${RB_REQ}
rollback_successful = ${RB_OK} if rollback_required else None
status = "success" if ${UPDATE_STATUS@Q} == "success" else "failed"
if rollback_required:
    status = "failed_rolled_back" if rollback_successful else "critical_manual_recovery_required"
out = build_usb_updater_result(
    status=status,
    source=source,
    target={"device_path_at_runtime": ${TARGET@Q}, "partition": ${PART_DEV@Q}, "label": "SETUPHELFER"},
    before={"payload_sha256": legacy.get("old_squashfs_sha256"), "payload_version": "1.10.0.15"},
    after={"payload_sha256": legacy.get("stick_squashfs_sha256"), "payload_version": ${CANONICAL_VERSION@Q}},
    atomic_replace=${PAYLOAD_COPIED_PY} and ${METADATA_WRITTEN_PY},
    rollback_required=rollback_required,
    rollback_successful=rollback_successful,
    content_gate="passed_in_run_verify",
    secret_gate="not_run_on_device",
)
Path(${ORDER_EVIDENCE_DIR@Q}).mkdir(parents=True, exist_ok=True)
print(json.dumps(out, indent=2))
PY

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
