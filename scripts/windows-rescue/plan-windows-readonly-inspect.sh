#!/usr/bin/env bash
# Read-only Windows rescue inspect mount plan — operator terminal, no writes, no mount.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT="${1:-}"

cd "$REPO_ROOT"

python3 - "${OUT}" <<'PY'
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

out_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else ""

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run_json(cmd: list[str]) -> tuple[str, object | None, str | None]:
    if not shutil.which(cmd[0]):
        return "tool_missing", None, cmd[0]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return "command_failed", None, (proc.stderr or proc.stdout or "").strip()[:500]
    try:
        return "ok", json.loads(proc.stdout or "null"), None
    except json.JSONDecodeError as exc:
        return "json_error", None, str(exc)

def run_lines(cmd: list[str]) -> tuple[str, list[str], str | None]:
    if not shutil.which(cmd[0]):
        return "tool_missing", [], cmd[0]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return "command_failed", [], (proc.stderr or proc.stdout or "").strip()[:500]
    return "ok", [ln for ln in (proc.stdout or "").splitlines() if ln.strip()], None

lsblk_status, lsblk, lsblk_err = run_json(["lsblk", "-J", "-b", "-o", "NAME,TYPE,SIZE,FSTYPE,PTTYPE,PARTTYPE,MOUNTPOINT,UUID,MODEL,TRAN"])
blkid_status, blkid_lines, blkid_err = run_lines(["blkid"])

nvme_devices: list[dict] = []
blockdevices: list[dict] = []
partitions: list[dict] = []
efi_candidates: list[dict] = []
ntfs_partitions: list[dict] = []
windows_candidates: list[dict] = []
linux_candidates: list[dict] = []
bitlocker_hints: list[dict] = []

def walk(node: dict, disk_id: int | None = None) -> None:
    name = str(node.get("name") or "")
    typ = str(node.get("type") or "")
    entry = {
        "name": name,
        "type": typ,
        "size_bytes": node.get("size"),
        "fstype": node.get("fstype"),
        "pttype": node.get("pttype"),
        "parttype": node.get("parttype"),
        "mountpoint": node.get("mountpoint"),
        "model": node.get("model"),
        "tran": node.get("tran"),
    }
    blockdevices.append(entry)
    if typ == "disk" and (name.startswith("nvme") or str(node.get("tran") or "").lower() == "nvme"):
        nvme_devices.append(entry)
    if typ == "part":
        fst = str(node.get("fstype") or "").lower()
        parttype = str(node.get("parttype") or "").lower()
        part = {**entry, "disk_hint": disk_id}
        partitions.append(part)
        if fst in ("vfat", "fat32", "fat") or parttype.startswith("c12a7328"):
            efi_candidates.append(part)
        if fst in ("ntfs", "fuseblk") or "microsoft basic data" in parttype:
            ntfs_partitions.append(part)
            windows_candidates.append({**part, "role_hint": "windows_data_or_os"})
        if fst in ("ext4", "ext3", "xfs", "btrfs", "linux"):
            linux_candidates.append(part)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            walk(child, disk_id if typ == "disk" else disk_id)

if isinstance(lsblk, dict):
    for dev in lsblk.get("blockdevices") or []:
        if isinstance(dev, dict):
            walk(dev)

for line in blkid_lines:
    low = line.lower()
    if "bitlocker" in low or "type=\"bitlocker\"" in low:
        bitlocker_hints.append({"source": "blkid", "line": line[:240]})

bitlocker_status = "unknown"
if bitlocker_hints:
    bitlocker_status = "locked"
elif lsblk_status == "ok" and ntfs_partitions and not bitlocker_hints:
    bitlocker_status = "not_detected"

dual_nvme = len(nvme_devices) >= 2
blocked_reasons: list[str] = []
required_operator_actions: list[str] = []

if lsblk_status == "tool_missing":
    blocked_reasons.append("tool_missing:lsblk")
    required_operator_actions.append("INSTALL_OR_USE_RESCUE_ENV_WITH_LSBLK")
if bitlocker_status in ("unknown", "locked"):
    blocked_reasons.append(f"bitlocker_{bitlocker_status}_blocks_file_access")
    required_operator_actions.append("VERIFY_BITLOCKER_BEFORE_READONLY_MOUNT")
if dual_nvme:
    blocked_reasons.append("dual_nvme_layout_requires_operator_review")
    required_operator_actions.append("REVIEW_2X2TB_NVME_LAYOUT")

mount_plan: list[dict] = []
if bitlocker_status not in ("unknown", "locked"):
    for idx, part in enumerate(windows_candidates[:4]):
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(part.get("name") or f"part{idx}"))
        mount_plan.append(
            {
                "device_hint": part.get("name"),
                "filesystem": part.get("fstype"),
                "mountpoint_plan": f"/run/setuphelfer-rescue/mnt/{safe}",
                "read_only": True,
                "execution": "plan_only",
                "requires_operator_context": True,
                "blocked_until_bitlocker_ok": True,
            }
        )
else:
    required_operator_actions.append("NO_MOUNT_UNTIL_BITLOCKER_OK")

body = {
    "schema_version": 1,
    "generated_at": utc_now(),
    "source": "plan_windows_readonly_inspect",
    "strict_mode": "read_only_plan_no_mount",
    "write_actions_allowed": False,
    "tools": {
        "lsblk": lsblk_status,
        "blkid": blkid_status,
        "lsblk_error": lsblk_err,
        "blkid_error": blkid_err,
    },
    "hardware_hints": {
        "nvme_count": len(nvme_devices),
        "dual_nvme_detected": dual_nvme,
        "target_profile": "2x2TB_NVMe_AMD_Ryzen_NVIDIA",
    },
    "blockdevices": blockdevices,
    "nvme_devices": nvme_devices,
    "partitions": partitions,
    "efi_candidates": efi_candidates,
    "ntfs_partitions": ntfs_partitions,
    "windows_candidates": windows_candidates,
    "linux_candidates": linux_candidates,
    "bitlocker": {
        "status": bitlocker_status,
        "hints": bitlocker_hints,
        "confidence": "low" if bitlocker_status == "unknown" else "medium",
    },
    "readonly_mount_plan": mount_plan,
    "blocked_reasons": blocked_reasons,
    "required_operator_actions": required_operator_actions,
    "forbidden": [
        "mount_without_operator_context",
        "ntfsfix",
        "chkdsk",
        "bcdedit",
        "bootrec",
        "parted_write",
        "mkfs",
        "dd",
        "bitlocker_unlock",
        "cloud_credentials",
    ],
}

text = json.dumps(body, indent=2, ensure_ascii=False)
if out_path:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
else:
    print(text)
PY
