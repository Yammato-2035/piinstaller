"""Machine identity profiles for MSI GE63 and ASUS ROG (PI-RS-ASUS-WIN11-LINUX-001).

Read-only DMI-based classification. No BIOS flash. No raw serials in public status.
"""

from __future__ import annotations

import hashlib
import platform
import re
from pathlib import Path
from typing import Any, Mapping

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

PROFILE_MSI_GE63 = "msi_ge63"
PROFILE_ASUS_ROG = "asus_rog"
PROFILE_ASUS_ROG_GABRIEL = "asus_rog_gabriel"
PROFILE_UNKNOWN = "unknown"

# Development workstation (Volker) — must never be auto-bound as Gabriel's install target.
KNOWN_DEVELOPER_ASUS_BOARD_NAMES = frozenset({"G713PI"})

_MSI_VENDOR_RE = re.compile(r"micro.?star|msi", re.I)
_GE63_RE = re.compile(r"GE63|MS-16P5|16P5", re.I)
_ASUS_VENDOR_RE = re.compile(r"asus", re.I)
_ROG_RE = re.compile(r"rog|strix|zephyrus|tuf.?gaming", re.I)


def _read_text(path: Path, limit: int = 512) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit].strip()
    except OSError:
        return ""


def read_dmi_fields(*, sys_class_dmi: Path | None = None) -> dict[str, str]:
    root = sys_class_dmi or Path("/sys/class/dmi/id")
    keys = (
        "sys_vendor",
        "product_name",
        "product_version",
        "product_family",
        "product_serial",
        "product_uuid",
        "board_vendor",
        "board_name",
        "board_version",
        "board_serial",
        "bios_vendor",
        "bios_version",
        "bios_date",
        "chassis_type",
    )
    return {k: _read_text(root / k) for k in keys}


def mask_serial(serial: str) -> str:
    s = (serial or "").strip()
    if not s or s.lower() in {"none", "to be filled by o.e.m.", "default string"}:
        return ""
    if len(s) <= 4:
        return "****"
    return f"…{s[-4:]}"


def hash_serial(serial: str) -> str:
    s = (serial or "").strip()
    if not s:
        return ""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hash_system_uuid(uuid_raw: str) -> str:
    u = (uuid_raw or "").strip()
    if not u:
        return ""
    return hashlib.sha256(u.encode("utf-8")).hexdigest()[:32]


def classify_expected_profile(dmi: Mapping[str, str]) -> tuple[str, str]:
    """Return (expected_profile, confidence).

    `asus_rog_gabriel` is NEVER assigned from DMI alone. Gabriel's laptop must be
    bound explicitly after physical confirmation. Generic ASUS ROG → `asus_rog`.
    """
    blob = " ".join(str(v or "") for v in dmi.values())
    vendor = f"{dmi.get('sys_vendor', '')} {dmi.get('board_vendor', '')}"
    product = f"{dmi.get('product_name', '')} {dmi.get('board_name', '')} {dmi.get('product_family', '')}"
    board = (dmi.get("board_name") or "").strip().upper()

    if _MSI_VENDOR_RE.search(vendor) and _GE63_RE.search(product + " " + blob):
        return PROFILE_MSI_GE63, "high"
    if _MSI_VENDOR_RE.search(vendor) and ("GE63" in product.upper() or "16P5" in blob.upper()):
        return PROFILE_MSI_GE63, "medium"
    if _ASUS_VENDOR_RE.search(vendor) and _ROG_RE.search(blob):
        # Developer ROG (e.g. G713PI) and any other ROG stay generic until Gabriel bind.
        return PROFILE_ASUS_ROG, "medium"
    if _ASUS_VENDOR_RE.search(vendor):
        return PROFILE_ASUS_ROG, "low"
    if _MSI_VENDOR_RE.search(vendor):
        return PROFILE_UNKNOWN, "low"
    return PROFILE_UNKNOWN, "low"


def is_known_developer_asus(dmi: Mapping[str, str]) -> bool:
    board = (dmi.get("board_name") or "").strip().upper()
    product = (dmi.get("product_name") or "").strip().upper()
    if board in KNOWN_DEVELOPER_ASUS_BOARD_NAMES:
        return True
    return any(b in product for b in KNOWN_DEVELOPER_ASUS_BOARD_NAMES)


def bind_gabriel_operator_profile(
    identity: Mapping[str, Any],
    *,
    operator_confirmed: bool,
    exact_model_confirmed: str,
    not_developer_host_ack: bool,
) -> dict[str, Any]:
    """Promote a generic asus_rog identity to asus_rog_gabriel only with operator proof."""
    base = dict(identity)
    if is_known_developer_asus(
        {
            "board_name": str(base.get("board_name") or ""),
            "product_name": str(base.get("product_name") or ""),
        }
    ):
        return {
            "ok": False,
            "identity": base,
            "error": "developer_asus_cannot_bind_as_gabriel",
        }
    if not operator_confirmed or not not_developer_host_ack or not exact_model_confirmed.strip():
        return {
            "ok": False,
            "identity": base,
            "error": "gabriel_bind_requirements_missing",
        }
    if str(base.get("expected_profile") or "") not in {PROFILE_ASUS_ROG, PROFILE_ASUS_ROG_GABRIEL}:
        return {"ok": False, "identity": base, "error": "not_asus_rog_family"}
    base["expected_profile"] = PROFILE_ASUS_ROG_GABRIEL
    base["confidence"] = "high"
    base["gabriel_bound"] = True
    base["exact_model_confirmed"] = exact_model_confirmed.strip()
    base["operator_confirmation_required"] = False
    base["unknown_machine_blocks_install"] = False
    base["write_blocked_reason"] = None
    return {"ok": True, "identity": base, "error": None}


def build_machine_identity(
    *,
    dmi: Mapping[str, str] | None = None,
    cpu_model: str | None = None,
    gpu_devices: list[str] | None = None,
    ram_bytes: int | None = None,
    sys_class_dmi: Path | None = None,
) -> dict[str, Any]:
    fields = dict(dmi or read_dmi_fields(sys_class_dmi=sys_class_dmi))
    profile, confidence = classify_expected_profile(fields)
    serial = fields.get("product_serial") or fields.get("board_serial") or ""
    machine_id_parts = [
        fields.get("sys_vendor", ""),
        fields.get("product_name", ""),
        fields.get("board_name", ""),
        hash_serial(serial)[:16],
    ]
    machine_id = hashlib.sha256("|".join(machine_id_parts).encode()).hexdigest()
    developer_host = is_known_developer_asus(fields)

    # Install writes never auto-allowed; Gabriel not auto-selected.
    write_blocked = True
    blocked_reason = "writes_require_explicit_gates"
    if developer_host:
        blocked_reason = "developer_workstation_not_gabriel_target"
    elif profile == PROFILE_UNKNOWN or confidence == "low":
        blocked_reason = "unknown_or_low_confidence_machine"
    elif profile == PROFILE_ASUS_ROG:
        blocked_reason = "asus_rog_not_bound_as_gabriel"

    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "machine_id": machine_id,
        "expected_profile": profile,
        "manufacturer": fields.get("sys_vendor") or fields.get("board_vendor") or "",
        "product_name": fields.get("product_name") or "",
        "product_family": fields.get("product_family") or "",
        "board_name": fields.get("board_name") or "",
        "board_vendor": fields.get("board_vendor") or "",
        "bios_vendor": fields.get("bios_vendor") or "",
        "bios_version": fields.get("bios_version") or "",
        "bios_date": fields.get("bios_date") or "",
        "system_uuid_hash": hash_system_uuid(fields.get("product_uuid") or ""),
        "chassis_type": fields.get("chassis_type") or "",
        "cpu_model": cpu_model or platform.processor() or "",
        "gpu_devices": list(gpu_devices or []),
        "ram_bytes": int(ram_bytes or 0),
        "serial_masked": mask_serial(serial),
        "serial_hash": hash_serial(serial),
        "confidence": confidence,
        "operator_confirmation_required": True,
        "installation_writes_allowed": False,
        "is_developer_workstation": developer_host,
        "is_gabriel_target": False,
        "gabriel_bound": False,
        "unknown_machine_blocks_install": profile == PROFILE_UNKNOWN or confidence == "low",
        "write_blocked_reason": blocked_reason if write_blocked else None,
    }


def profiles_conflict(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    pa = str(a.get("expected_profile") or "")
    pb = str(b.get("expected_profile") or "")
    if pa == PROFILE_UNKNOWN or pb == PROFILE_UNKNOWN:
        return False
    asus_family = {PROFILE_ASUS_ROG, PROFILE_ASUS_ROG_GABRIEL}
    if pa in asus_family and pb in asus_family:
        return False
    return pa != pb and (
        {pa, pb} == {PROFILE_MSI_GE63, PROFILE_ASUS_ROG_GABRIEL}
        or {pa, pb} == {PROFILE_MSI_GE63, PROFILE_ASUS_ROG}
    )


def assert_profile_for_writes(identity: Mapping[str, Any], allowed: set[str]) -> dict[str, Any]:
    profile = str(identity.get("expected_profile") or PROFILE_UNKNOWN)
    confidence = str(identity.get("confidence") or "low")
    ok = profile in allowed and confidence in {"high", "medium"} and profile != PROFILE_UNKNOWN
    return {
        "ok": ok,
        "profile": profile,
        "confidence": confidence,
        "blocked_reason": None if ok else "machine_identity_gate_failed",
    }
