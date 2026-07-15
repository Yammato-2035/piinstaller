"""Destructive MSI lab HDD target for physical E2E (001D5)."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.rescue_backup_target_policy import RESCUE_STICK_LABELS, classify_storage_role
from core.rescue_physical_e2e_auto_e2e_state import check_abort, write_heartbeat

DEFAULT_TIMEOUT = 300
MOUNT_BASE = Path("/run/setuphelfer-rescue/e2e")

LAB_PARTITIONS: tuple[dict[str, Any], ...] = (
    {"number": 1, "label": "SETUP_E2E_SOURCE", "size_gib": 8, "fstype": "ext4"},
    {"number": 2, "label": "SETUP_E2E_BACKUP", "size_gib": 32, "fstype": "ext4"},
    {"number": 3, "label": "SETUP_E2E_RESTORE", "size_gib": 32, "fstype": "ext4"},
)


@dataclass(frozen=True)
class LabDiskCandidate:
    disk_path: str
    model: str
    transport: str
    size_bytes: int
    role: str
    partitions: list[dict[str, Any]]


def _run_cmd(
    args: list[str],
    *,
    timeout: int = DEFAULT_TIMEOUT,
    allowed_disk: str | None = None,
) -> dict[str, Any]:
    if allowed_disk and args:
        joined = " ".join(args)
        if allowed_disk not in joined:
            return {"ok": False, "code": "blocked_unauthorized_device", "args": args}
    proc = subprocess.run(args, capture_output=True, text=True, check=False, timeout=timeout)
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "args": args,
        "stdout_tail": (proc.stdout or "")[-500:],
        "stderr_tail": (proc.stderr or "")[-500:],
    }


def _lsblk_tree() -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(
            [
                "lsblk",
                "-J",
                "-b",
                "-o",
                "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS,TRAN,RM,HOTPLUG,MODEL,UUID",
            ],
            text=True,
            timeout=30,
        )
        data = json.loads(out)
        return data.get("blockdevices") or []
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _flatten(nodes: list[dict[str, Any]], parent: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for node in nodes:
        entry = dict(node)
        if parent:
            entry["parent_path"] = parent.get("path")
            if not entry.get("tran"):
                entry["tran"] = parent.get("tran")
            if entry.get("model") in (None, ""):
                entry["model"] = parent.get("model")
        mps = entry.get("mountpoints") or []
        entry["mountpoint"] = mps[0] if mps else None
        flat.append(entry)
        flat.extend(_flatten(entry.get("children") or [], entry))
    return flat


def _is_rescue_stick_label(label: str | None) -> bool:
    if not label:
        return False
    upper = label.upper()
    return upper in {x.upper() for x in RESCUE_STICK_LABELS} or "SETUPHELFER" in upper or upper == "SETUP_LOGS"


def _disk_role(disk: dict[str, Any], parts: list[dict[str, Any]]) -> str:
    for part in parts:
        role = classify_storage_role(
            {
                "path": part.get("path"),
                "type": "part",
                "fstype": part.get("fstype"),
                "label": part.get("label"),
                "tran": disk.get("tran"),
            }
        )
        if role != "unknown":
            return role
    return classify_storage_role({"path": disk.get("path"), "type": "disk", "tran": disk.get("tran")})


def _partition_uuid(partition_path: str) -> str:
    proc = subprocess.run(
        ["blkid", "-o", "value", "-s", "UUID", partition_path],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    return (proc.stdout or "").strip()


def _disk_has_forbidden_mount(disk: dict[str, Any], parts: list[dict[str, Any]]) -> bool:
    forbidden = {"/", "/boot", "/boot/firmware", "/boot/efi"}
    for part in parts:
        mps = part.get("mountpoints") or []
        for mp in mps:
            if mp in forbidden or (mp and str(mp).startswith("/media/") and "SETUP" in str(mp).upper()):
                return True
    return False


def discover_lab_disk_candidates() -> list[LabDiskCandidate]:
    out: list[LabDiskCandidate] = []
    for disk in _lsblk_tree():
        if disk.get("type") != "disk":
            continue
        parts = [p for p in (disk.get("children") or []) if isinstance(p, dict)]
        size = int(disk.get("size") or 0)
        out.append(
            LabDiskCandidate(
                disk_path=str(disk.get("path") or ""),
                model=str(disk.get("model") or ""),
                transport=str(disk.get("tran") or "").lower(),
                size_bytes=size,
                role=_disk_role(disk, parts),
                partitions=[
                    {
                        "path": str(p.get("path") or ""),
                        "label": str(p.get("label") or ""),
                        "uuid": str(p.get("uuid") or _partition_uuid(str(p.get("path") or ""))),
                        "fstype": str(p.get("fstype") or ""),
                        "mountpoint": (p.get("mountpoints") or [None])[0],
                    }
                    for p in parts
                ],
            )
        )
    return out


def load_destructive_lab_config(run_control: dict[str, Any] | None) -> dict[str, Any] | None:
    if not run_control:
        return None
    cfg = run_control.get("destructive_lab_target")
    if not isinstance(cfg, dict):
        return None
    if not cfg.get("enabled") or not cfg.get("operator_authorized"):
        return None
    return cfg


def verify_destructive_target_identity(
    candidate: LabDiskCandidate,
    config: dict[str, Any],
    *,
    flat_devices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    expected_transport = str(config.get("expected_transport") or "usb").lower()
    if candidate.transport != expected_transport:
        errors.append("transport_mismatch")
    model_needle = str(config.get("expected_model_contains") or "").upper()
    if model_needle and model_needle not in candidate.model.upper():
        errors.append("model_mismatch")
    size_min = int(config.get("expected_size_bytes_min") or 0)
    size_max = int(config.get("expected_size_bytes_max") or 0)
    if size_min and candidate.size_bytes < size_min:
        errors.append("size_too_small")
    if size_max and candidate.size_bytes > size_max:
        errors.append("size_too_large")

    expected_uuid = str(config.get("expected_existing_partition_uuid") or "").lower()
    expected_label = str(config.get("expected_existing_label") or "")
    expected_role = str(config.get("expected_role") or "")
    if expected_role and candidate.role != expected_role:
        errors.append("role_mismatch")

    uuid_match = False
    label_match = False
    for part in candidate.partitions:
        if expected_uuid and str(part.get("uuid") or "").lower() == expected_uuid:
            uuid_match = True
        if expected_label and str(part.get("label") or "") == expected_label:
            label_match = True
    if expected_uuid and not uuid_match:
        errors.append("preformat_uuid_mismatch")
    if expected_label and not label_match:
        errors.append("label_mismatch")

    flat = flat_devices or _flatten(_lsblk_tree())
    disk_node = next((d for d in flat if d.get("path") == candidate.disk_path), None)
    parts = [d for d in flat if str(d.get("parent_path") or "") == candidate.disk_path]
    if disk_node and _disk_has_forbidden_mount(disk_node, parts):
        errors.append("forbidden_mount_present")

    for part in candidate.partitions:
        if _is_rescue_stick_label(part.get("label")):
            errors.append("blocked_rescue_stick_label")

    if candidate.transport in {"nvme", "sata"} and not str(candidate.disk_path).startswith("/dev/sd"):
        if "usb" not in candidate.transport:
            errors.append("blocked_internal_disk")

    code = "blocked_destructive_target_identity_mismatch"
    return {"ok": not errors, "code": code if errors else "ok", "errors": errors, "candidate": candidate}


def select_destructive_lab_target(config: dict[str, Any]) -> tuple[LabDiskCandidate | None, dict[str, Any]]:
    candidates = discover_lab_disk_candidates()
    matched: list[LabDiskCandidate] = []
    flat = _flatten(_lsblk_tree())
    for cand in candidates:
        if not cand.disk_path.startswith("/dev/"):
            continue
        gate = verify_destructive_target_identity(cand, config, flat_devices=flat)
        if gate.get("ok"):
            matched.append(cand)
    if len(matched) > 1:
        return None, {"ok": False, "code": "blocked_destructive_target_identity_mismatch", "reason": "ambiguous", "count": len(matched)}
    if len(matched) == 0:
        return None, {"ok": False, "code": "blocked_destructive_target_identity_mismatch", "reason": "no_match"}
    return matched[0], {"ok": True, "code": "ok"}


def wait_for_destructive_lab_target(
    config: dict[str, Any],
    *,
    run_id: str = "",
    max_wait_sec: int = 120,
) -> tuple[LabDiskCandidate | None, dict[str, Any]]:
    from core.rescue_physical_e2e_auto_e2e_state import update_auto_e2e_state

    deadline = time.time() + max_wait_sec
    last_gate: dict[str, Any] = {"ok": False, "code": "blocked_sabrent_not_detected"}
    while time.time() < deadline:
        abort = check_abort()
        if abort and abort.get("immediate"):
            return None, {"ok": False, "code": abort.get("reason")}
        candidate, gate = select_destructive_lab_target(config)
        last_gate = gate
        if gate.get("ok") and candidate is not None:
            update_auto_e2e_state(phase="sabrent_detected", status="running", last_progress="SABRENT-HDD erkannt")
            write_heartbeat(run_id=run_id, phase="sabrent_detected")
            return candidate, gate
        elapsed = int(max_wait_sec - max(0, deadline - time.time()))
        update_auto_e2e_state(
            phase="sabrent_waiting",
            status="running",
            last_progress=f"SABRENT wird gesucht ({elapsed}/{max_wait_sec} s)",
        )
        write_heartbeat(run_id=run_id, phase="sabrent_waiting")
        subprocess.run(["udevadm", "settle"], capture_output=True, check=False, timeout=30)
        time.sleep(2)
    return None, {"ok": False, "code": "blocked_sabrent_not_detected", "detail": last_gate}


def _partition_path(disk_path: str, number: int) -> str:
    if "nvme" in disk_path:
        return f"{disk_path}p{number}"
    return f"{disk_path}{number}"


def wipe_and_partition_disk(
    disk_path: str,
    *,
    config: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    if not config.get("allow_wipefs") or not config.get("allow_new_gpt") or not config.get("allow_partitioning"):
        return {"ok": False, "code": "destructive_not_authorized"}

    abort = check_abort(dangerous_phase=True)
    if abort and abort.get("immediate"):
        return {"ok": False, "code": abort.get("reason")}

    write_heartbeat(run_id=run_id, phase="test_disk_prepare")
    steps: list[dict[str, Any]] = []

    for cmd in (
        ["wipefs", "-a", disk_path],
        ["sgdisk", "--zap-all", disk_path],
        ["sgdisk", "--clear", disk_path],
    ):
        result = _run_cmd(cmd, allowed_disk=disk_path)
        steps.append(result)
        if not result.get("ok"):
            return {"ok": False, "code": "destructive_wipe_failed", "steps": steps}

    part_specs: list[str] = []
    for spec in LAB_PARTITIONS:
        num = int(spec["number"])
        size = int(spec["size_gib"])
        label = str(spec["label"])
        part_specs.extend(["-n", f"{num}:0:+{size}G", "-t", f"{num}:8300", "-c", f"{num}:{label}"])
    sgdisk_cmd = ["sgdisk", *part_specs, disk_path]
    result = _run_cmd(sgdisk_cmd, allowed_disk=disk_path)
    steps.append(result)
    if not result.get("ok"):
        return {"ok": False, "code": "destructive_partition_failed", "steps": steps}

    settle = _run_cmd(["udevadm", "settle"], timeout=60)
    steps.append(settle)
    probe = _run_cmd(["partprobe", disk_path], allowed_disk=disk_path, timeout=60)
    steps.append(probe)
    time.sleep(2)
    _run_cmd(["udevadm", "settle"], timeout=60)

    if not config.get("allow_format"):
        return {"ok": False, "code": "format_not_authorized"}

    for spec in LAB_PARTITIONS:
        abort = check_abort(dangerous_phase=True)
        if abort and abort.get("immediate"):
            return {"ok": False, "code": abort.get("reason"), "steps": steps}
        part = _partition_path(disk_path, int(spec["number"]))
        fmt = _run_cmd(
            ["mkfs.ext4", "-F", "-L", str(spec["label"]), part],
            allowed_disk=disk_path,
            timeout=600,
        )
        steps.append(fmt)
        if not fmt.get("ok"):
            return {"ok": False, "code": "destructive_format_failed", "steps": steps, "partition": part}

    _run_cmd(["udevadm", "settle"], timeout=60)
    return {"ok": True, "code": "ok", "steps": steps}


def verify_layout_after_partition(disk_path: str) -> dict[str, Any]:
    flat = _flatten(_lsblk_tree())
    parts = [d for d in flat if str(d.get("parent_path") or "") == disk_path and d.get("type") == "part"]
    if len(parts) != len(LAB_PARTITIONS):
        return {"ok": False, "code": "failed_destructive_target_layout_verification", "reason": "partition_count"}
    labels_found: set[str] = set()
    for part in parts:
        label = str(part.get("label") or "")
        fstype = str(part.get("fstype") or "").lower()
        if label:
            labels_found.add(label)
        if fstype and fstype != "ext4":
            return {"ok": False, "code": "failed_destructive_target_layout_verification", "reason": "fstype", "part": part.get("path")}
    expected_labels = {str(s["label"]) for s in LAB_PARTITIONS}
    if labels_found != expected_labels:
        return {"ok": False, "code": "failed_destructive_target_layout_verification", "reason": "labels", "found": sorted(labels_found)}
    return {"ok": True, "code": "ok", "partitions": parts}


def mount_e2e_partitions(disk_path: str, run_id: str) -> dict[str, Any]:
    base = MOUNT_BASE / run_id
    mounts = {
        "source": base / "source",
        "backup": base / "backup",
        "restore": base / "restore",
    }
    for key, spec in zip(("source", "backup", "restore"), LAB_PARTITIONS, strict=True):
        part = _partition_path(disk_path, int(spec["number"]))
        mp = mounts[key]
        mp.mkdir(parents=True, exist_ok=True)
        if any(mp.iterdir()) if mp.is_dir() and mp.exists() else False:
            pass
        result = _run_cmd(["mount", part, str(mp)], allowed_disk=disk_path, timeout=60)
        if not result.get("ok"):
            return {"ok": False, "code": "mount_failed", "mount": key, "result": result}
    return {"ok": True, "mounts": mounts, "disk_path": disk_path}


def unmount_e2e_partitions(mounts: dict[str, Path]) -> None:
    for key in ("restore", "backup", "source"):
        mp = mounts.get(key)
        if mp and Path(mp).is_dir():
            _run_cmd(["umount", str(mp)], timeout=60)


def prepare_destructive_run_paths(mounts: dict[str, Path], e2e_run_id: str) -> dict[str, Any]:
    source = Path(mounts["source"])
    backup = Path(mounts["backup"])
    restore = Path(mounts["restore"]) / "data"
    marker_root = source / "setuphelfer-e2e" / e2e_run_id
    marker_root.mkdir(parents=True, exist_ok=True)
    marker = {
        "schema": "setuphelfer.rescue.e2e-target.v1",
        "purpose": "setuphelfer_physical_e2e_test_only",
        "run_id": e2e_run_id,
        "internal_run_marker": True,
    }
    (marker_root / "setuphelfer-e2e-target.json").write_text(
        json.dumps(marker, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    source_data = source / "testdata"
    source_data.mkdir(parents=True, exist_ok=True)
    restore.mkdir(parents=True, exist_ok=True)
    if any(restore.iterdir()):
        raise ValueError("restore_partition_not_empty")
    if any(backup.iterdir()):
        for child in backup.iterdir():
            if child.name != ".keep":
                raise ValueError("backup_partition_not_empty")
    work_root = source / "setuphelfer-e2e" / e2e_run_id
    return {
        "layout_mode": "dedicated_external_lab_hdd",
        "lab_tmpfs_mode": False,
        "automation_class": "physical_full_destructive",
        "work_root": work_root,
        "source": source_data,
        "backup_archive": backup / "e2e-backup.tar.gz",
        "restore_dir": restore,
        "allowed_source_prefixes": (source,),
        "allowed_output_prefixes": (backup,),
        "allowed_restore_prefixes": (Path(mounts["restore"]),),
        "target_type": "dedicated_external_lab_hdd",
        "target_layout": "three_partition_e2e",
        "target_capacity_class": "large",
    }
