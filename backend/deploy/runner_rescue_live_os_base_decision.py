from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import REPO_ROOT, guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json"
_CFG_PATH = REPO_ROOT / "config" / "version.json"
_MAX_BYTES = 512 * 1024


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    out_rel: str,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_live_os_base_decision_status": status,
        "rescue_live_os_base_decision_file_path": out_rel,
        "rescue_live_os_base_decision": body,
        "rescue_live_os_base_decision_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_live_os_base_decision(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    """Evaluates Live-OS bases for the Setuphelfer rescue stick; writes handoff JSON."""
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_LIVE_OS")
    if oerr or out_path is None:
        return _emit("blocked", {}, out_rel=_OUT_REL, wrote=False, warnings=[], errors=[oerr or "RESCUE_LIVE_OS_OUTPUT_INVALID"])

    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_LIVE_OS")
    if gerr:
        return _emit("blocked", {}, out_rel=_OUT_REL, wrote=False, warnings=[], errors=[gerr])

    warnings: list[str] = []
    cfg: dict[str, Any] | None = None
    try:
        if _CFG_PATH.is_file():
            cfg = json.loads(_CFG_PATH.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                cfg = None
                warnings.append("RESCUE_CFG_VERSION_JSON_UNEXPECTED")
    except OSError:
        warnings.append("RESCUE_CFG_VERSION_READ_FAILED")
    if cfg is None:
        warnings.append("RESCUE_CFG_VERSION_MISSING")

    bases = {
        "debian_live": {
            "hardware_compatibility": "high",
            "uefi_support": "high",
            "package_availability": "high",
            "maintainability": "high",
            "beginner_friendliness": "high",
            "image_size": "medium",
            "secure_boot_perspective": "review_required",
            "setuphelfer_stack_fit": "high",
            "summary": "Debian stable + live-build; best match for Python backend, apt, and long-term security support.",
        },
        "ubuntu_live": {
            "hardware_compatibility": "high",
            "uefi_support": "high",
            "package_availability": "high",
            "maintainability": "high",
            "beginner_friendliness": "high",
            "image_size": "medium_large",
            "secure_boot_perspective": "review_required",
            "setuphelfer_stack_fit": "high",
            "summary": "Ubuntu live is viable but adds churn vs Debian; prefer Debian for controlled rescue baseline.",
        },
        "alpine": {
            "hardware_compatibility": "medium",
            "uefi_support": "medium",
            "package_availability": "medium",
            "maintainability": "medium",
            "beginner_friendliness": "low",
            "image_size": "small",
            "secure_boot_perspective": "review_required",
            "setuphelfer_stack_fit": "medium",
            "summary": "Small footprint but musl/busybox friction for the current Setuphelfer Python/apt workflow.",
        },
        "archiso": {
            "hardware_compatibility": "high",
            "uefi_support": "high",
            "package_availability": "high",
            "maintainability": "medium",
            "beginner_friendliness": "low",
            "image_size": "medium",
            "secure_boot_perspective": "review_required",
            "setuphelfer_stack_fit": "medium",
            "summary": "Rolling model and ISO pipeline differ from Debian live-build; higher operational variance.",
        },
        "raspberry_pi_os_image": {
            "hardware_compatibility": "arm_specific",
            "uefi_support": "low_arm_firmware",
            "package_availability": "high_debian_derived",
            "maintainability": "medium",
            "beginner_friendliness": "medium",
            "image_size": "medium",
            "secure_boot_perspective": "review_required",
            "setuphelfer_stack_fit": "medium",
            "summary": "Separate arm64/RPi track; not the primary amd64 rescue stick baseline.",
        },
    }

    secure_boot = "review_required"
    recommended = "debian_live"
    status = "ok"
    if bases[recommended].get("secure_boot_perspective") == "review_required":
        warnings.append("RESCUE_SECUREBOOT_REVIEW_REQUIRED")

    body: dict[str, Any] = {
        "rescue_live_os_base_decision_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "recommended_live_os_base": recommended,
        "secure_boot_status": secure_boot,
        "criteria_axes": [
            "hardware_compatibility",
            "uefi_support",
            "package_availability",
            "maintainability",
            "beginner_friendliness",
            "image_size",
            "secure_boot_perspective",
            "setuphelfer_stack_fit",
        ],
        "evaluation": bases,
        "mvp_recommendation": {
            "primary": "debian_live_amd64",
            "secondary_tracks": ["ubuntu_live_optional", "arm64_raspberry_pi_os_later"],
        },
        "inputs": {"config_version_path": "config/version.json"},
        "project_version": str(cfg.get("project_version") or "") if isinstance(cfg, dict) else "",
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, out_rel=_OUT_REL, wrote=False, warnings=warnings, errors=[werr])
    return _emit(status, body, out_rel=_OUT_REL, wrote=True, warnings=warnings, errors=[])
