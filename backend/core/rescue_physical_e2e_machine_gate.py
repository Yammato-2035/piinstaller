"""MSI machine identity and boot-parameter gates for physical E2E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version
from core.rescue_system_identity import detect_booted_machine_identity


def read_kernel_cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def verify_boot_parameters(*, cmdline: str | None = None) -> dict[str, Any]:
    line = cmdline if cmdline is not None else read_kernel_cmdline()
    required = (
        "setuphelfer_msi_lab_auto=1",
        "setuphelfer_msi_e2e_auto=1",
    )
    missing = [flag for flag in required if flag not in line]
    return {"ok": not missing, "missing": missing, "cmdline_present": bool(line)}


def verify_machine_identity(expected: dict[str, Any] | None) -> dict[str, Any]:
    identity = detect_booted_machine_identity()
    errors: list[str] = []
    if not expected:
        return {"ok": False, "code": "blocked_machine_identity_mismatch", "errors": ["no_expected_machine"]}

    vendor = str(expected.get("vendor") or "")
    model_contains = str(expected.get("model_contains") or "")
    actual_vendor = str(identity.get("vendor") or "")
    actual_model = str(identity.get("model") or "")

    if vendor and vendor.lower() not in actual_vendor.lower():
        errors.append("vendor_mismatch")
    if model_contains and model_contains.lower() not in actual_model.lower():
        errors.append("model_mismatch")

    return {
        "ok": not errors,
        "code": "ok" if not errors else "blocked_machine_identity_mismatch",
        "errors": errors,
        "identity": identity,
    }


def verify_payload_version_gate(expected_version: str | None) -> dict[str, Any]:
    actual = rescue_payload_version()
    if not expected_version:
        return {"ok": True, "actual": actual}
    ok = actual == expected_version
    return {
        "ok": ok,
        "code": "ok" if ok else "payload_version_mismatch",
        "expected": expected_version,
        "actual": actual,
    }
