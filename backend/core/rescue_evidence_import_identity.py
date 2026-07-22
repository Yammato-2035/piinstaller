"""Evidence import identity gates — prevent cross-device session merges."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

CONTRACT_VERSION = 1

_MSI_RE = re.compile(r"micro.?star|\bmsi\b|GE63|MS-16P5", re.I)
_ASUS_RE = re.compile(r"asus", re.I)
_G513QM_RE = re.compile(r"G513QM", re.I)


def fingerprint_hash_from_fields(
    *,
    manufacturer: str,
    product_name: str,
    board_name: str,
    bios_vendor: str = "",
    system_uuid_hash: str = "",
    board_serial_hash: str = "",
    cpu_signature: str = "",
    gpu_pci_ids: list[str] | None = None,
    storage_controller_pci_ids: list[str] | None = None,
) -> str:
    parts = [
        manufacturer.strip().lower(),
        product_name.strip().lower(),
        board_name.strip().lower(),
        bios_vendor.strip().lower(),
        system_uuid_hash.strip().lower(),
        board_serial_hash.strip().lower(),
        cpu_signature.strip().lower(),
        ",".join(sorted(gpu_pci_ids or [])),
        ",".join(sorted(storage_controller_pci_ids or [])),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def build_machine_fingerprint(
    *,
    dmi: Mapping[str, str],
    cpu_signature: str = "",
    gpu_pci_ids: list[str] | None = None,
    storage_controller_pci_ids: list[str] | None = None,
) -> dict[str, Any]:
    from core.rescue_machine_identity_profiles import hash_serial, hash_system_uuid

    manufacturer = dmi.get("sys_vendor") or dmi.get("board_vendor") or ""
    product = dmi.get("product_name") or ""
    board = dmi.get("board_name") or ""
    bios_vendor = dmi.get("bios_vendor") or ""
    uuid_hash = hash_system_uuid(dmi.get("product_uuid") or "")
    board_serial_hash = hash_serial(dmi.get("board_serial") or "")
    fp = fingerprint_hash_from_fields(
        manufacturer=manufacturer,
        product_name=product,
        board_name=board,
        bios_vendor=bios_vendor,
        system_uuid_hash=uuid_hash,
        board_serial_hash=board_serial_hash,
        cpu_signature=cpu_signature,
        gpu_pci_ids=gpu_pci_ids,
        storage_controller_pci_ids=storage_controller_pci_ids,
    )
    required_ok = bool(manufacturer and product and board)
    confidence = "high" if required_ok and uuid_hash else ("medium" if required_ok else "low")
    return {
        "schema_version": "1.1",
        "contract_version": CONTRACT_VERSION,
        "manufacturer": manufacturer,
        "product_name": product,
        "board_name": board,
        "product_family": dmi.get("product_family") or "",
        "bios_vendor": bios_vendor,
        "bios_version": dmi.get("bios_version") or "",
        "system_uuid_hash": uuid_hash,
        "board_serial_hash": board_serial_hash,
        "cpu_signature": cpu_signature,
        "gpu_pci_ids": list(gpu_pci_ids or []),
        "storage_controller_pci_ids": list(storage_controller_pci_ids or []),
        "fingerprint_hash": fp,
        "confidence": confidence,
        "required_fields_present": required_ok,
    }


def session_machine_blob(session_dir: Path) -> dict[str, Any] | None:
    machine = session_dir / "01-machine.json"
    if not machine.is_file():
        return None
    try:
        data = json.loads(machine.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def session_matches_boot_id(session_dir: Path, boot_id: str) -> bool:
    meta = session_dir / "00-session.json"
    if not meta.is_file():
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return str(data.get("boot_id") or "") == str(boot_id)


def manufacturers_compatible(a: str, b: str) -> bool:
    a_l, b_l = (a or "").lower(), (b or "").lower()
    if not a_l or not b_l:
        return False
    if _MSI_RE.search(a_l) and _ASUS_RE.search(b_l):
        return False
    if _ASUS_RE.search(a_l) and _MSI_RE.search(b_l):
        return False
    if _MSI_RE.search(a_l) and _MSI_RE.search(b_l):
        return True
    if _ASUS_RE.search(a_l) and _ASUS_RE.search(b_l):
        return True
    return a_l.split()[0] == b_l.split()[0]


def session_compatible_with_expected(
    session_machine: Mapping[str, Any],
    *,
    expected_manufacturer: str | None = None,
    expected_board: str | None = None,
    expected_product: str | None = None,
    expected_fingerprint_hash: str | None = None,
) -> dict[str, Any]:
    vendor = str(session_machine.get("vendor") or session_machine.get("manufacturer") or "")
    product = str(session_machine.get("product_name") or "")
    board = str(session_machine.get("board_name") or "")
    reasons: list[str] = []
    if expected_manufacturer and not manufacturers_compatible(vendor, expected_manufacturer):
        reasons.append("manufacturer_mismatch")
    if expected_board and board and expected_board.upper() not in board.upper():
        reasons.append("board_mismatch")
    if expected_product and product and expected_product.upper() not in product.upper() and not (
        expected_board and expected_board.upper() in board.upper()
    ):
        # board match can override loose product string differences
        if not (expected_board and expected_board.upper() in board.upper()):
            reasons.append("product_mismatch")
    if expected_fingerprint_hash:
        # optional strict path when session carries fingerprint
        sess_fp = str(session_machine.get("fingerprint_hash") or "")
        if sess_fp and sess_fp != expected_fingerprint_hash:
            reasons.append("fingerprint_mismatch")
    # hard MSI vs ASUS
    if _MSI_RE.search(vendor + " " + product + " " + board) and expected_manufacturer and _ASUS_RE.search(
        expected_manufacturer
    ):
        reasons.append("msi_cannot_bind_asus_profile")
    ok = not reasons
    return {
        "ok": ok,
        "reasons": reasons,
        "session_vendor": vendor,
        "session_product": product,
        "session_board": board,
        "action": "import" if ok else "excluded_from_result",
    }


def select_compatible_session(
    sessions_root: Path,
    *,
    boot_id: str,
    expected_manufacturer: str | None = None,
    expected_board: str | None = None,
    expected_product: str | None = None,
) -> dict[str, Any]:
    """Select session only when boot_id matches AND machine identity is compatible."""
    if not sessions_root.is_dir():
        return {"ok": False, "code": "sessions_root_missing", "session_dir": None, "conflicts": []}
    conflicts: list[dict[str, Any]] = []
    candidates = sorted(
        [p for p in sessions_root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for session in candidates:
        if not session_matches_boot_id(session, boot_id):
            # Never fall back to newest foreign session.
            continue
        machine = session_machine_blob(session) or {}
        check = session_compatible_with_expected(
            machine,
            expected_manufacturer=expected_manufacturer,
            expected_board=expected_board,
            expected_product=expected_product,
        )
        if check["ok"]:
            return {
                "ok": True,
                "session_dir": session,
                "session_id": session.name,
                "machine": machine,
                "conflicts": conflicts,
            }
        conflicts.append(
            {
                "session_id": session.name,
                "boot_id_matched": True,
                "reason": "machine_identity_mismatch",
                "details": check,
                "action": "excluded_from_gabriel_result",
            }
        )
    # Record newest mismatched sessions for diagnostics (still no import).
    for session in candidates[:3]:
        if session_matches_boot_id(session, boot_id):
            continue
        machine = session_machine_blob(session) or {}
        conflicts.append(
            {
                "session_id": session.name,
                "boot_id_matched": False,
                "reason": "boot_id_mismatch",
                "manufacturer": machine.get("vendor"),
                "product_name": machine.get("product_name"),
                "board_name": machine.get("board_name"),
                "action": "excluded_from_result",
            }
        )
    return {
        "ok": False,
        "code": "no_compatible_session_for_boot",
        "session_dir": None,
        "conflicts": conflicts,
    }


def is_g513qm_gabriel_candidate(dmi_or_machine: Mapping[str, Any]) -> bool:
    blob = " ".join(str(dmi_or_machine.get(k) or "") for k in (
        "sys_vendor", "vendor", "manufacturer", "product_name", "board_name", "product_family"
    ))
    return bool(_ASUS_RE.search(blob) and _G513QM_RE.search(blob))
