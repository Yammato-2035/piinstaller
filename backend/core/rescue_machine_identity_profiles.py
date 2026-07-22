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
PROFILE_ASUS_ROG_GABRIEL = "asus_rog_gabriel"
PROFILE_UNKNOWN = "unknown"

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
    """Return (expected_profile, confidence)."""
    blob = " ".join(str(v or "") for v in dmi.values())
    vendor = f"{dmi.get('sys_vendor', '')} {dmi.get('board_vendor', '')}"
    product = f"{dmi.get('product_name', '')} {dmi.get('board_name', '')} {dmi.get('product_family', '')}"

    if _MSI_VENDOR_RE.search(vendor) and _GE63_RE.search(product + " " + blob):
        return PROFILE_MSI_GE63, "high"
    if _MSI_VENDOR_RE.search(vendor) and ("GE63" in product.upper() or "16P5" in blob.upper()):
        return PROFILE_MSI_GE63, "medium"
    if _ASUS_VENDOR_RE.search(vendor) and _ROG_RE.search(blob):
        # Exact SKU for Gabriel's machine is completed after physical diagnosis.
        return PROFILE_ASUS_ROG_GABRIEL, "medium"
    if _ASUS_VENDOR_RE.search(vendor):
        return PROFILE_ASUS_ROG_GABRIEL, "low"
    if _MSI_VENDOR_RE.search(vendor):
        return PROFILE_UNKNOWN, "low"
    return PROFILE_UNKNOWN, "low"


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

    if confidence == "low" or profile == PROFILE_UNKNOWN:
        write_blocked = True
    else:
        write_blocked = confidence != "high" and profile == PROFILE_ASUS_ROG_GABRIEL

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
        "unknown_machine_blocks_install": profile == PROFILE_UNKNOWN or confidence == "low",
        "write_blocked_reason": (
            "unknown_or_low_confidence_machine"
            if write_blocked or profile == PROFILE_UNKNOWN or confidence == "low"
            else None
        ),
    }


def profiles_conflict(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    pa = str(a.get("expected_profile") or "")
    pb = str(b.get("expected_profile") or "")
    if pa == PROFILE_UNKNOWN or pb == PROFILE_UNKNOWN:
        return False
    return pa != pb and {pa, pb} == {PROFILE_MSI_GE63, PROFILE_ASUS_ROG_GABRIEL}


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
