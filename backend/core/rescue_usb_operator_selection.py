"""Rescue USB operator selection — read-only discovery, explicit confirmation, evidence only (no dd)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.safe_device import ClassifiedDevice, list_classified_devices

Runner = Callable[..., Any]

CONFIRMATION_PHRASE = "WRITE SETUPHELFER RESCUE USB"
EVIDENCE_REL = "docs/evidence/runtime-results/rescue/usb_operator_selection_latest.json"

BLOCKER_SELECTION_REQUIRED = "RESCUE_USB_OPERATOR_SELECTION_REQUIRED"
BLOCKER_DESTRUCTIVE_NOT_CONFIRMED = "RESCUE_USB_DESTRUCTIVE_WRITE_NOT_CONFIRMED"
BLOCKER_OLD_REPLACE_NOT_CONFIRMED = "RESCUE_USB_OLD_VERSION_REPLACE_NOT_CONFIRMED"

REQUIRED_CONFIRMATIONS: tuple[str, ...] = (
    "confirm_correct_usb",
    "confirm_data_destruction",
    "confirm_not_system_or_backup",
    "confirm_old_stick_replace",
    "confirm_iso_sha256_and_device",
)

_FORBIDDEN_DEVICE_PATTERNS = (
    re.compile(r"^/dev/sda$"),
    re.compile(r"^/dev/nvme"),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _workspace_root() -> Path:
    from core.dev_dashboard import _effective_workspace_root

    return _effective_workspace_root(_repo_root())


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def evidence_path(workspace: Path | None = None) -> Path:
    root = (workspace or _workspace_root()).resolve(strict=False)
    return (root / EVIDENCE_REL).resolve(strict=False)


def _load_rescue_usb_gate(workspace: Path | None = None) -> dict[str, Any]:
    root = workspace or _workspace_root()
    path = root / "docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _lsblk_disks_raw(*, runner: Runner | None = None) -> list[dict[str, Any]]:
    from core.storage_facade import list_disk_blockdevice_nodes

    return list_disk_blockdevice_nodes(runner=runner, mode="rescue")


def _partition_rows(node: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ch in node.get("children") or []:
        if not isinstance(ch, dict) or ch.get("type") not in ("part", "crypt"):
            continue
        mps: list[str] = []
        raw_mps = ch.get("mountpoints")
        if isinstance(raw_mps, list):
            mps = [str(x).strip() for x in raw_mps if isinstance(x, str) and str(x).strip()]
        mp = ch.get("mountpoint")
        if isinstance(mp, str) and mp.strip():
            mps.append(mp.strip())
        rows.append(
            {
                "device": _device_path(ch),
                "name": str(ch.get("name") or ""),
                "size": ch.get("size"),
                "fstype": ch.get("fstype"),
                "label": ch.get("label") or ch.get("partlabel"),
                "mountpoints": sorted(set(mps)),
            }
        )
    return rows


def _device_path(node: Mapping[str, Any]) -> str:
    p = node.get("path")
    if isinstance(p, str) and p.startswith("/dev/"):
        return p
    name = node.get("name")
    if isinstance(name, str) and name:
        return name if name.startswith("/dev/") else f"/dev/{name}"
    return ""


def _is_rescue_stick_mountpoint(mp: str) -> bool:
    upper = (mp or "").upper()
    return "SETUPHELFER" in upper or "SETUP_LOGS" in upper


def _is_backup_mountpoint(mp: str) -> bool:
    s = (mp or "").rstrip("/")
    if not s or s in {"/", "/boot", "/boot/firmware"}:
        return False
    if _is_rescue_stick_mountpoint(s):
        return False
    if s.startswith("/mnt/setuphelfer") or s.startswith("/mnt/pi-installer"):
        return True
    parts = Path(s).parts
    if len(parts) >= 3 and parts[1] == "media":
        login = parts[2]
        if login not in ("setuphelfer",) and not _is_rescue_stick_mountpoint(s):
            return True
    return False


def _detect_setuphelfer_rescue(partitions: Sequence[Mapping[str, Any]], mountpoints: Sequence[str]) -> dict[str, Any]:
    labels: list[str] = []
    fstypes: list[str] = []
    for p in partitions:
        label = str(p.get("label") or "").strip()
        fst = str(p.get("fstype") or "").strip().lower()
        if label:
            labels.append(label)
        if fst:
            fstypes.append(fst)
    label_hit = any("SETUPHELFER_RESCUE" in lb.upper() for lb in labels)
    iso_hit = any(fst == "iso9660" for fst in fstypes)
    mount_hit = any("SETUPHELFER_RESCUE" in mp.upper() for mp in mountpoints)
    detected = label_hit or iso_hit or mount_hit
    version_hint = None
    if detected:
        version_hint = "legacy_setuphelfer_rescue"
    return {
        "detected": detected,
        "labels": sorted(set(labels)),
        "fstypes": sorted(set(fstypes)),
        "previous_setuphelfer_version": version_hint,
        "warning": (
            "Existing SETUPHELFER_RESCUE or iso9660 media detected — verify stick age before overwrite."
            if detected
            else None
        ),
    }


def _sda_removable_usb_allowed(device_path: str, transport: str, removable: bool) -> bool:
    """Allow /dev/sda when it is a hot-plug USB stick (common on laptops without sdb)."""
    return device_path == "/dev/sda" and transport.lower() == "usb" and removable


def device_blocked_reason(
    *,
    device_path: str,
    classified: ClassifiedDevice,
    transport: str,
    removable: bool | None = None,
) -> str | None:
    dev = device_path.strip()
    if not dev.startswith("/dev/"):
        return "INVALID_DEVICE_PATH"
    is_removable = removable if removable is not None else classified.removable
    for pat in _FORBIDDEN_DEVICE_PATTERNS:
        if pat.match(dev):
            if _sda_removable_usb_allowed(dev, transport, is_removable):
                continue
            return "FORBIDDEN_SYSTEM_OR_BACKUP_DEVICE"
    if transport.lower() != "usb":
        return "NOT_USB_TRANSPORT"
    if classified.is_system_disk or classified.is_boot_disk:
        return "SYSTEM_OR_BOOT_DISK"
    for mp in classified.mountpoints:
        if _is_backup_mountpoint(mp):
            return "MOUNTED_BACKUP_TARGET"
    for part in classified.partitions:
        for mp in part.mountpoints:
            if _is_backup_mountpoint(mp):
                return "MOUNTED_BACKUP_TARGET"
    return None


def build_usb_candidates_payload(*, runner: Runner | None = None, workspace: Path | None = None) -> dict[str, Any]:
    classified = {d.id: d for d in list_classified_devices(runner=runner)}
    raw_disks = _lsblk_disks_raw(runner=runner)
    gate = _load_rescue_usb_gate(workspace)
    devices: list[dict[str, Any]] = []

    for node in raw_disks:
        dev_path = _device_path(node)
        cd = classified.get(dev_path)
        if cd is None:
            continue
        transport = str(node.get("tran") or cd.type or "").lower()
        partitions = _partition_rows(node)
        rescue_meta = _detect_setuphelfer_rescue(partitions, cd.mountpoints)
        blocked = device_blocked_reason(
            device_path=dev_path,
            classified=cd,
            transport=transport,
            removable=cd.removable,
        )
        devices.append(
            {
                "device": dev_path,
                "name": cd.name,
                "size": cd.size,
                "model": node.get("model") or None,
                "serial": node.get("serial") or None,
                "transport": transport or None,
                "removable": cd.removable,
                "partitions": partitions,
                "mountpoints": cd.mountpoints,
                "fstypes": cd.filesystems,
                "setuphelfer_rescue_detected": rescue_meta["detected"],
                "setuphelfer_rescue_warning": rescue_meta["warning"],
                "previous_setuphelfer_version": rescue_meta["previous_setuphelfer_version"],
                "selectable": blocked is None,
                "blocked_reason": blocked,
                "read_only": True,
            }
        )

    return {
        "status": "ok",
        "read_only": True,
        "dd_execution_allowed": False,
        "auto_selection_forbidden": True,
        "iso_path": gate.get("iso_path"),
        "iso_sha256": gate.get("iso_sha256"),
        "devices": devices,
        "secrets_exposed": False,
    }


def build_generated_dd_command(*, device: str, iso_path: str) -> str:
    dev = device.strip()
    iso = iso_path.strip()
    return (
        f"sudo dd if=\"{iso}\" of=\"{dev}\" bs=16M status=progress conv=fsync"
    )


def evaluate_operator_submission(
    *,
    selected_device: str,
    operator_confirmations: Mapping[str, Any],
    confirmation_phrase: str,
    runner: Runner | None = None,
    workspace: Path | None = None,
) -> dict[str, Any]:
    candidates = build_usb_candidates_payload(runner=runner, workspace=workspace)
    gate = _load_rescue_usb_gate(workspace)
    iso_path = str(gate.get("iso_path") or "").strip()
    iso_sha256 = str(gate.get("iso_sha256") or "").strip()

    device_row = next((d for d in candidates["devices"] if d.get("device") == selected_device.strip()), None)
    errors: list[str] = []
    blockers: list[str] = []

    if device_row is None:
        errors.append("selected_device_not_found")
        blockers.append(BLOCKER_SELECTION_REQUIRED)
    elif not device_row.get("selectable"):
        errors.append(str(device_row.get("blocked_reason") or "device_not_selectable"))
        blockers.append(BLOCKER_SELECTION_REQUIRED)

    confirmations = {k: bool(operator_confirmations.get(k)) for k in REQUIRED_CONFIRMATIONS}
    phrase_ok = confirmation_phrase.strip() == CONFIRMATION_PHRASE

    if not confirmations["confirm_correct_usb"] or not confirmations["confirm_data_destruction"]:
        blockers.append(BLOCKER_DESTRUCTIVE_NOT_CONFIRMED)
    if not confirmations["confirm_not_system_or_backup"] or not confirmations["confirm_iso_sha256_and_device"]:
        blockers.append(BLOCKER_DESTRUCTIVE_NOT_CONFIRMED)
    if not phrase_ok:
        blockers.append(BLOCKER_DESTRUCTIVE_NOT_CONFIRMED)

    old_detected = bool(device_row and device_row.get("setuphelfer_rescue_detected"))
    if old_detected and not confirmations["confirm_old_stick_replace"]:
        blockers.append(BLOCKER_OLD_REPLACE_NOT_CONFIRMED)

    if not iso_path or not iso_sha256:
        errors.append("iso_metadata_missing")
        blockers.append(BLOCKER_SELECTION_REQUIRED)

    blockers = sorted(set(blockers))
    write_allowed = not blockers and device_row is not None

    previous_label = None
    previous_fstype = None
    previous_mountpoints: list[str] = []
    if device_row:
        parts = device_row.get("partitions") or []
        if parts:
            previous_fstype = parts[0].get("fstype")
            previous_label = parts[0].get("label")
        previous_mountpoints = list(device_row.get("mountpoints") or [])

    generated_dd_command = build_generated_dd_command(device=selected_device.strip(), iso_path=iso_path) if write_allowed else None

    return {
        "selected_device": selected_device.strip() if selected_device else None,
        "selected_model": (device_row or {}).get("model"),
        "selected_serial": (device_row or {}).get("serial"),
        "selected_size": (device_row or {}).get("size"),
        "previous_label": previous_label,
        "previous_fstype": previous_fstype,
        "previous_mountpoints": previous_mountpoints,
        "iso_path": iso_path or None,
        "iso_sha256": iso_sha256 or None,
        "operator_confirmations": confirmations,
        "confirmation_phrase_matched": phrase_ok,
        "write_allowed": write_allowed,
        "generated_dd_command": generated_dd_command,
        "created_at": _now_iso(),
        "secrets_exposed": False,
        "dd_execution_allowed": False,
        "blockers": blockers,
        "errors": errors,
        "setuphelfer_rescue_detected": old_detected,
    }


def load_operator_selection_evidence(workspace: Path | None = None) -> dict[str, Any] | None:
    path = evidence_path(workspace)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def save_operator_selection_evidence(record: Mapping[str, Any], workspace: Path | None = None) -> Path:
    path = evidence_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(record), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def build_operator_gate_blockers(evidence: Mapping[str, Any] | None) -> list[str]:
    if not evidence:
        return [
            BLOCKER_SELECTION_REQUIRED,
            BLOCKER_DESTRUCTIVE_NOT_CONFIRMED,
        ]
    blockers: list[str] = []
    if not evidence.get("selected_device"):
        blockers.append(BLOCKER_SELECTION_REQUIRED)
    if evidence.get("write_allowed") is not True:
        for code in (
            BLOCKER_SELECTION_REQUIRED,
            BLOCKER_DESTRUCTIVE_NOT_CONFIRMED,
            BLOCKER_OLD_REPLACE_NOT_CONFIRMED,
        ):
            stored = evidence.get("blockers") or []
            if code in stored:
                blockers.append(code)
        if not blockers:
            blockers.extend(
                [
                    BLOCKER_SELECTION_REQUIRED,
                    BLOCKER_DESTRUCTIVE_NOT_CONFIRMED,
                ]
            )
    return sorted(set(blockers))


def build_compact_usb_operator_summary(
    *,
    runner: Runner | None = None,
    workspace: Path | None = None,
) -> dict[str, Any]:
    evidence = load_operator_selection_evidence(workspace)
    candidates = build_usb_candidates_payload(runner=runner, workspace=workspace)
    usb_devices = [d for d in candidates.get("devices") or [] if d.get("transport") == "usb"]
    old_rescue = any(d.get("setuphelfer_rescue_detected") for d in usb_devices)
    selection_present = bool(evidence and evidence.get("selected_device"))
    write_allowed = evidence.get("write_allowed") is True if evidence else False
    blockers = build_operator_gate_blockers(evidence)

    next_step = (
        "Operator-Befehl aus DCC Developer Toolbox kopieren und manuell im Terminal ausführen."
        if write_allowed
        else "USB-Stick in DCC Developer Toolbox auswählen, alle Checkboxen und Textbestätigung setzen."
    )

    return {
        "usb_detected": len(usb_devices) > 0,
        "usb_device_count": len(usb_devices),
        "old_rescue_stick_detected": old_rescue,
        "operator_selection_present": selection_present,
        "operator_selection_device": evidence.get("selected_device") if evidence else None,
        "destructive_write_allowed": write_allowed,
        "dd_execution_allowed": False,
        "blockers": blockers,
        "next_step": next_step,
        "evidence_path": EVIDENCE_REL,
        "secrets_exposed": False,
    }
