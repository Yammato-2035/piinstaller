"""
Linux install readiness gate — dual-NVMe identity + baseline preconditions.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 Phase 13.

This phase never authorizes writes: ``writes_allowed`` is always False.
Device identities exposed to the operator are hashed/redacted (never treat
``nvme0n1`` / ``nvme1n1`` as stable identity).
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from core.hardware_baseline_contracts import BaselineStatus

LINUX_INSTALL_READINESS_VERSION = 1

_READY = "ready"
_REVIEW = "review_required"
_BLOCKED = "blocked"

_REVIEW_MEMORY_CPU = frozenset(
    {
        BaselineStatus.DEGRADED.value,
        BaselineStatus.REVIEW_REQUIRED.value,
        BaselineStatus.EXTENDED_TEST_RECOMMENDED.value,
        BaselineStatus.TEST_UNAVAILABLE.value,
        BaselineStatus.NOT_TESTED.value,
    }
)

_BLOCK_MEMORY_CPU = frozenset(
    {
        BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value,
        BaselineStatus.EXTENDED_TEST_REQUIRED.value,
    }
)


def _hash_identity(disk_id: str) -> str:
    return hashlib.sha256(str(disk_id).encode("utf-8")).hexdigest()[:16]


def _find_disk(disks: Sequence[Mapping[str, Any]], disk_id: str | None) -> dict[str, Any] | None:
    if not disk_id:
        return None
    for disk in disks or ():
        if str(disk.get("disk_id") or "") == str(disk_id):
            return dict(disk)
    return None


def _redacted_device(disk_id: str | None, disk: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not disk_id:
        return None
    identity_hash = _hash_identity(disk_id)
    src = dict(disk or {})
    return {
        "identity_hash": identity_hash,
        "disk_id_redacted": f"disk:{identity_hash}",
        "model": src.get("model"),
        "capacity_bytes": src.get("capacity_bytes"),
        "pci_path": src.get("pci_path"),
        "role_hint": src.get("role_hint"),
        "stable": src.get("stable"),
    }


def _truthy(value: Any) -> bool:
    return bool(value)


def evaluate_linux_install_readiness(
    *,
    disks: list[dict] | Sequence[Mapping[str, Any]],
    memory_status: str,
    cpu_status: str,
    windows_disk_id: str | None,
    linux_target_disk_id: str | None,
    image_verified: bool = False,
    efi_plan_isolated: bool = False,
) -> dict[str, Any]:
    """
    Evaluate whether a controlled Linux install on a second disk may proceed.

    Always returns ``writes_allowed=False`` in this phase.
    """
    disk_list = [dict(d or {}) for d in (disks or [])]
    blockers: list[str] = []
    reasons: list[str] = []

    win_id = str(windows_disk_id).strip() if windows_disk_id else None
    linux_id = str(linux_target_disk_id).strip() if linux_target_disk_id else None

    if not win_id or not linux_id:
        blockers.append("missing_dual_identity")
        reasons.append("Windows and Linux target disks must both be uniquely identified.")

    if win_id and linux_id and win_id == linux_id:
        blockers.append("windows_and_linux_target_same_id")
        reasons.append("Windows device and Linux target resolve to the same identity.")

    if not image_verified:
        blockers.append("image_not_verified")
        reasons.append("Installation image is not verified.")

    if not efi_plan_isolated:
        blockers.append("efi_plan_not_isolated")
        reasons.append("EFI plan is not isolated from the Windows EFI.")

    mem = str(memory_status or BaselineStatus.NOT_TESTED.value)
    cpu = str(cpu_status or BaselineStatus.NOT_TESTED.value)

    if mem in _BLOCK_MEMORY_CPU:
        blockers.append("memory_immediate_issue_detected" if mem == BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value else "memory_baseline_blocks_install")
        reasons.append(f"Memory baseline status is {mem}.")
    elif mem in _REVIEW_MEMORY_CPU:
        reasons.append(f"Memory baseline status requires review: {mem}.")

    if cpu in _BLOCK_MEMORY_CPU:
        blockers.append("cpu_immediate_issue_detected" if cpu == BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value else "cpu_baseline_blocks_install")
        reasons.append(f"CPU baseline status is {cpu}.")
    elif cpu in _REVIEW_MEMORY_CPU:
        reasons.append(f"CPU baseline status requires review: {cpu}.")

    windows_disk = _find_disk(disk_list, win_id)
    linux_disk = _find_disk(disk_list, linux_id)

    if linux_id and linux_disk is None:
        blockers.append("linux_target_not_in_disk_inventory")
        reasons.append("Linux target identity is not present in the disk inventory.")

    if linux_disk is not None:
        if _truthy(linux_disk.get("critical_warning")):
            blockers.append("linux_target_critical_warning")
            reasons.append("Linux target reports an NVMe critical warning.")
        media_errors = linux_disk.get("media_errors")
        if media_errors not in (None, 0, "0", False):
            try:
                media_count = int(media_errors)
            except (TypeError, ValueError):
                media_count = 1 if media_errors else 0
            if media_count > 0:
                blockers.append("linux_target_media_errors")
                reasons.append("Linux target reports media/data integrity errors.")
        if linux_disk.get("stable") is False:
            blockers.append("linux_target_unstable")
            reasons.append("Linux target is not marked stable.")

    review_needed = bool(
        mem in _REVIEW_MEMORY_CPU
        or cpu in _REVIEW_MEMORY_CPU
        or (linux_disk is not None and linux_disk.get("stable") is None and not blockers)
    )

    if blockers:
        readiness = _BLOCKED
    elif review_needed:
        readiness = _REVIEW
        if not reasons:
            reasons.append("Baseline or target state requires operator review.")
    elif (
        win_id
        and linux_id
        and image_verified
        and efi_plan_isolated
        and mem == BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        and cpu == BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        and linux_disk is not None
        and not _truthy(linux_disk.get("critical_warning"))
        and (linux_disk.get("media_errors") in (None, 0, "0", False))
        and linux_disk.get("stable") is not False
    ):
        readiness = _READY
        reasons.append("Dual disk identity, baselines, image verification and EFI isolation satisfy the install gate.")
    else:
        readiness = _REVIEW
        reasons.append("Install readiness could not be confirmed as ready.")

    return {
        "schema_version": "linux-install-readiness.v1",
        "readiness_version": LINUX_INSTALL_READINESS_VERSION,
        "linux_install_readiness": readiness,
        "windows_device": _redacted_device(win_id, windows_disk),
        "linux_target": _redacted_device(linux_id, linux_disk),
        "memory_status": mem,
        "cpu_status": cpu,
        "image_verified": bool(image_verified),
        "efi_plan_isolated": bool(efi_plan_isolated),
        "reasons": reasons,
        "blockers": blockers,
        "writes_allowed": False,
        "read_only": True,
    }


__all__ = [
    "LINUX_INSTALL_READINESS_VERSION",
    "evaluate_linux_install_readiness",
]
