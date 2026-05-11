from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import (
    ensure_rescue_workspace_dirs,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    write_json_handoff,
)

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_MAX_BYTES = 1_500_000


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_storage_discovery_plan_status": status,
        "rescue_storage_discovery_plan_file_path": _PLAN_REL,
        "rescue_storage_discovery_plan": body,
        "rescue_storage_discovery_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_storage_discovery_result_status": status,
        "rescue_storage_discovery_result_file_path": _RESULT_REL,
        "rescue_storage_discovery_result": body,
        "rescue_storage_discovery_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_storage_discovery_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_STGPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_STGPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    body: dict[str, Any] = {
        "rescue_storage_discovery_plan_schema_version": 1,
        "strict_mode": "rescue_live_storage_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "allowed_readonly_commands": [
            {"cmd": "lsblk", "args": ["-J", "-o", "NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT,SIZE,MODEL,TRAN"]},
            {"cmd": "blkid"},
        ],
        "forbidden": ["mkfs", "fdisk", "parted", "dd", "wipefs", "mount", "-o", "rw", "fsck", "--repair"],
        "classification_targets": [
            "nvme",
            "sata",
            "usb",
            "sd",
            "efi_system_partition",
            "linux_fs",
            "ntfs",
            "btrfs",
            "xfs",
            "crypto_luks",
            "backup_candidate",
            "system_disk_candidate",
        ],
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def _walk_lsblk(node: dict[str, Any], out: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        return
    name = node.get("name") or node.get("NAME")
    if name:
        out.append(
            {
                "name": name,
                "type": node.get("type") or node.get("TYPE"),
                "fstype": node.get("fstype") or node.get("FSTYPE"),
                "label": node.get("label") or node.get("LABEL"),
                "uuid": node.get("uuid") or node.get("UUID"),
                "mountpoint": node.get("mountpoint") or node.get("MOUNTPOINT"),
                "size": node.get("size") or node.get("SIZE"),
                "model": node.get("model") or node.get("MODEL"),
                "tran": node.get("tran") or node.get("TRAN"),
            }
        )
    for ch in node.get("children") or []:
        if isinstance(ch, dict):
            _walk_lsblk(ch, out)


def _classify(rows: list[dict[str, Any]]) -> dict[str, Any]:
    flags = {
        "nvme": False,
        "sata": False,
        "usb": False,
        "sd": False,
        "efi_system_partition": False,
        "linux_fs": False,
        "ntfs": False,
        "btrfs": False,
        "xfs": False,
        "crypto_luks": False,
        "backup_candidate": False,
        "system_disk_candidate": False,
    }
    uuids: list[str] = []
    for r in rows:
        name = str(r.get("name") or "").lower()
        tran = str(r.get("tran") or "").lower()
        fst = str(r.get("fstype") or "").lower()
        partlabel = str(r.get("label") or "").lower()
        u = str(r.get("uuid") or "").strip()
        if u:
            uuids.append(u)
        if "nvme" in name:
            flags["nvme"] = True
        if tran == "usb":
            flags["usb"] = True
        if name.startswith("sd") and tran != "usb":
            flags["sata"] = True
        if name.startswith("mmc"):
            flags["sd"] = True
        if fst == "vfat" and ("efi" in partlabel or "esp" in partlabel):
            flags["efi_system_partition"] = True
        if fst in ("ext2", "ext3", "ext4", "xfs", "btrfs"):
            flags["linux_fs"] = True
        if fst == "ntfs":
            flags["ntfs"] = True
        if fst == "btrfs":
            flags["btrfs"] = True
        if fst == "xfs":
            flags["xfs"] = True
        if "crypto" in fst or "luks" in fst:
            flags["crypto_luks"] = True
        if "backup" in partlabel or "setuphelfer" in partlabel:
            flags["backup_candidate"] = True
        if r.get("mountpoint") in ("/", "/boot", "/efi"):
            flags["system_disk_candidate"] = True

    uuid_counts: dict[str, int] = {}
    for u in uuids:
        uuid_counts[u] = uuid_counts.get(u, 0) + 1
    uuid_conflicts = [u for u, c in uuid_counts.items() if c > 1 and u]
    return {"flags": flags, "uuid_conflicts": uuid_conflicts, "row_count": len(rows)}


def execute_rescue_storage_discovery(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_storage_discovery: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_storage_discovery:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_EXECUTE_STORAGE_DISCOVERY"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_EXECUTE_STORAGE_DISCOVERY"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_STGRES")
    if oerr or out_path is None:
        return _emit_result(
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=[oerr or "RESCUE_STGRES_INVALID"],
        )
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    _, perr = load_json_handoff(_PLAN_REL, "RESCUE_STGPLAN")
    warnings: list[str] = []
    if perr:
        warnings.append(str(perr))

    rows: list[dict[str, Any]] = []
    lsblk_raw = ""
    blkid_raw = ""
    try:
        p1 = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINT,SIZE,MODEL,TRAN"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        lsblk_raw = (p1.stdout or "")[:800_000]
        if p1.returncode == 0 and lsblk_raw.strip():
            tree = json.loads(lsblk_raw)
            for dev in tree.get("blockdevices") or []:
                if isinstance(dev, dict):
                    _walk_lsblk(dev, rows)
        else:
            warnings.append("RESCUE_STORAGE_LSBLK_NONZERO_OR_EMPTY")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        warnings.append(f"RESCUE_STORAGE_LSBLK_FAILED:{type(e).__name__}")

    try:
        p2 = subprocess.run(["blkid"], capture_output=True, text=True, timeout=30, check=False)
        blkid_raw = (p2.stdout or "")[:400_000]
    except (OSError, subprocess.TimeoutExpired):
        warnings.append("RESCUE_STORAGE_BLKID_FAILED")

    cls = _classify(rows)
    raw_body: dict[str, Any] = {
        "rescue_storage_discovery_result_schema_version": 1,
        "strict_mode": "rescue_live_storage_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lsblk_rows": rows[:500],
        "classification": cls,
        "lsblk_excerpt": lsblk_raw[:20_000],
        "blkid_excerpt": blkid_raw[:20_000],
    }
    werr = write_json_handoff(out_path, raw_body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw_body, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_storage_discovery_result(explicit_overwrite=True, warnings=warnings)


def build_rescue_storage_discovery_result(
    *,
    explicit_overwrite: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_STGRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_STGRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_STGRES_MISSING_RUN_EXECUTE"])

    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_STGRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_STGRES_JSON_INVALID"])

    warn = list(warnings or [])
    errs: list[str] = []

    cls = data.get("classification") if isinstance(data.get("classification"), dict) else {}
    uuid_conf = list(cls.get("uuid_conflicts") or []) if isinstance(cls.get("uuid_conflicts"), list) else []

    eval_status = "ok"
    if errs:
        eval_status = "blocked"
    elif uuid_conf:
        eval_status = "review_required"
        warn.append("RESCUE_STORAGE_UUID_CONFLICT_HINT")
    elif int(cls.get("row_count") or 0) == 0 and not data.get("lsblk_rows"):
        eval_status = "review_required"
        warn.append("RESCUE_STORAGE_NO_ROWS")

    merged = dict(data)
    merged["evaluation"] = {
        "rescue_storage_discovery_eval_status": eval_status,
        "readonly_analysis_only": True,
        "uuid_conflicts": uuid_conf,
        "flags": cls.get("flags") if isinstance(cls.get("flags"), dict) else {},
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_result(eval_status, merged, wrote=True, warnings=warn, errors=errs)
