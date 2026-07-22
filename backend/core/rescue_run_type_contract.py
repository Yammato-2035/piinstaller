"""Rescue run-type contracts — discovery must not require full BVR run-control."""

from __future__ import annotations

from typing import Any, Mapping

CONTRACT_VERSION = 1

RUN_TYPES = (
    "hardware_discovery",
    "firmware_audit",
    "windows_diagnostics",
    "full_e2e",
    "bvr",
    "gui_diag",
    "installation_preflight",
)

# Fields required per declared run type (minimal).
REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "hardware_discovery": frozenset({"boot_id", "machine_fingerprint_hash", "payload_version"}),
    "firmware_audit": frozenset({"boot_id", "machine_fingerprint_hash", "bios_version"}),
    "windows_diagnostics": frozenset({"boot_id", "machine_fingerprint_hash"}),
    "full_e2e": frozenset({"boot_id", "run_id", "payload_version", "run_control"}),
    "bvr": frozenset({"boot_id", "run_id", "run_control", "bvr_progress"}),
    "gui_diag": frozenset({"boot_id", "gui_status"}),
    "installation_preflight": frozenset({"boot_id", "machine_fingerprint_hash", "preflight_id"}),
}


def normalize_run_type(value: str | None) -> str | None:
    v = (value or "").strip().lower()
    return v if v in RUN_TYPES else None


def evaluate_run_control(
    *,
    declared_run_type: str,
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate whether run_control_invalid is appropriate for the declared type."""
    rtype = normalize_run_type(declared_run_type)
    if not rtype:
        return {
            "status": "invalid_for_declared_run_type",
            "declared_run_type": declared_run_type,
            "error": "unknown_run_type",
            "run_control_invalid_correct": False,
        }
    required = REQUIRED_FIELDS[rtype]
    missing = [f for f in sorted(required) if not artifact.get(f)]
    # Discovery / firmware / windows_diag must NOT fail solely for missing BVR run_control.
    if rtype in {"hardware_discovery", "firmware_audit", "windows_diagnostics", "gui_diag"}:
        if missing:
            return {
                "status": "discovery_partial" if rtype != "gui_diag" else "discovery_partial",
                "declared_run_type": rtype,
                "missing_fields": missing,
                "run_control_invalid_correct": False,
                "note": "BVR run_control not required for this run type",
            }
        return {
            "status": "discovery_complete",
            "declared_run_type": rtype,
            "missing_fields": [],
            "run_control_invalid_correct": False,
        }
    # full_e2e / bvr / installation_preflight
    if missing:
        return {
            "status": "invalid_for_declared_run_type",
            "declared_run_type": rtype,
            "missing_fields": missing,
            "run_control_invalid_correct": True,
        }
    ctrl = artifact.get("run_control")
    if isinstance(ctrl, dict) and ctrl.get("enabled") is False and ctrl.get("consumed") is True:
        return {
            "status": "invalid_for_declared_run_type",
            "declared_run_type": rtype,
            "missing_fields": [],
            "run_control_invalid_correct": True,
            "code": "run_control_invalid",
            "errors": ["disabled", "already_consumed"],
        }
    return {
        "status": "discovery_complete" if rtype != "full_e2e" else "ok",
        "declared_run_type": rtype,
        "missing_fields": [],
        "run_control_invalid_correct": False,
    }


def classify_gabriel_stick_boot(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """The 2026-07-22 Gabriel stick boot was MSI-lab cmdline with discovery off — treat as hardware_discovery."""
    cmdline = str(artifact.get("cmdline") or artifact.get("cmdline_redacted") or "")
    declared = "hardware_discovery"
    if "setuphelfer_msi_e2e_auto=1" in cmdline and "setuphelfer_auto_discovery=0" in cmdline:
        note = "MSI auto-e2e flags on ASUS hardware_discovery boot; e2e blocked is expected"
    else:
        note = None
    evaled = evaluate_run_control(declared_run_type=declared, artifact=artifact)
    evaled["note"] = note
    evaled["recommended_run_type"] = declared
    return evaled
