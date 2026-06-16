"""
Stabile Blockgeräte-Identität für Rescue-Restore (lsblk/blkid, keine neuen Pakete).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from core.storage_facade import probe_block_device_identity

Runner = Callable[..., Any] | None


def build_device_identity(device_path: str | None, *, runner: Runner = None) -> dict[str, Any]:
    """
    Liefert strukturierte Identität für ein Blockgerät (Partition oder Whole-Disk).

    Fehlschlag von lsblk → minimales Dict mit ``weak_identity: True``.
    """
    dev = (device_path or "").strip()
    if not dev.startswith("/dev/"):
        return {"device_path": dev or None, "weak_identity": True, "codes": ["rescue.restore.target_not_found"]}

    if not Path(dev).exists():
        return {"device_path": dev, "weak_identity": True, "codes": ["rescue.restore.target_not_found"]}

    node = probe_block_device_identity(dev, runner=runner)
    out: dict[str, Any] = {
        "device_path": dev,
        "size_human": None,
        "type": None,
        "model": None,
        "serial": None,
        "transport": None,
        "uuid": None,
        "partuuid": None,
        "pkname": None,
        "fstype": None,
        "weak_identity": True,
        "codes": [],
    }
    if node is None:
        out["codes"].append("rescue.restore.target_ambiguous")
        return out
    out["size_human"] = node.get("size")
    out["type"] = node.get("type")
    out["model"] = (node.get("model") or "").strip() or None
    out["serial"] = (node.get("serial") or "").strip() or None
    out["transport"] = (node.get("tran") or "").strip() or None
    out["uuid"] = (node.get("uuid") or "").strip() or None
    out["partuuid"] = (node.get("partuuid") or "").strip() or None
    pk = (node.get("pkname") or "").strip()
    out["pkname"] = pk if pk.startswith("/dev/") else None
    out["fstype"] = (node.get("fstype") or "").strip() or None
    if out["serial"] or out["partuuid"] or out["uuid"]:
        out["weak_identity"] = False
    elif out["size_human"] and out["model"]:
        out["weak_identity"] = False
    return out


def compare_device_identity(
    stored: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    """
    Vergleicht gespeicherte (Dry-Run) vs. aktuelle Identität.

    Rückgabe: (ok, mismatch_codes).
    """
    if not stored or not current:
        return False, ["rescue.restore.target_identity_mismatch"]
    errs: list[str] = []

    def _norm(s: Any) -> str:
        return str(s or "").strip()

    ss, sc = _norm(stored.get("serial")), _norm(current.get("serial"))
    ps, pc = _norm(stored.get("partuuid")), _norm(current.get("partuuid"))
    us, uc = _norm(stored.get("uuid")), _norm(current.get("uuid"))
    if ss and sc and ss != sc:
        errs.append("rescue.restore.target_identity_mismatch")
    if ps and pc and ps != pc:
        errs.append("rescue.restore.target_identity_mismatch")
    if us and uc and us != uc:
        errs.append("rescue.restore.target_identity_mismatch")
    if _norm(stored.get("size_human")) and _norm(current.get("size_human")) and _norm(stored.get("size_human")) != _norm(
        current.get("size_human")
    ):
        errs.append("rescue.restore.target_changed")
    sp = (stored.get("device_path") or "").strip()
    cp = (current.get("device_path") or "").strip()
    if sp and cp and Path(sp).name != Path(cp).name:
        if not (ss and sc and ss == sc) and not (ps and pc and ps == pc) and not (us and uc and us == uc):
            errs.append("rescue.restore.target_identity_mismatch")
    return len(errs) == 0, errs


def detect_target_identity_mismatch(
    stored: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> str | None:
    ok, errs = compare_device_identity(stored, current)
    if ok:
        return None
    return errs[0] if errs else "rescue.restore.target_identity_mismatch"


def render_target_confirmation_descriptor(identity: dict[str, Any] | None) -> str:
    """Kurzbeschreibung für Logs/Reports (keine Secrets)."""
    if not identity:
        return "(no device)"
    parts = [
        identity.get("device_path"),
        identity.get("size_human"),
        identity.get("model"),
        identity.get("serial"),
        identity.get("transport"),
    ]
    return " | ".join(str(p) for p in parts if p)


__all__ = [
    "build_device_identity",
    "compare_device_identity",
    "detect_target_identity_mismatch",
    "render_target_confirmation_descriptor",
]
