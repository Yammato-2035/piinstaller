"""
Diagnostics forwarding contract after accepted telemetry ingest.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 11.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

DIAGNOSTIC_AREAS = (
    "boot_stage",
    "cpu",
    "memory",
    "gpu",
    "firmware",
    "driver",
    "pci_pcie",
    "nvme",
    "usb",
    "network",
    "input",
    "audio",
    "camera",
    "thermal",
    "power",
    "rescue_runtime",
)


def build_diagnostics_result(
    *,
    correlation_id: str,
    run_id: str,
    diagnostic_status: str,
    primary_failure_area: str | None = None,
    primary_issue_code: str | None = None,
    root_cause_confidence: float = 0.0,
    missing_drivers: Sequence[Mapping[str, Any]] | None = None,
    missing_firmware: Sequence[str] | None = None,
    degraded_devices: Sequence[str] | None = None,
    blocked_devices: Sequence[str] | None = None,
    recommended_next_boot_profile: str | None = None,
    recommended_actions: Sequence[str] | None = None,
    evidence_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status = diagnostic_status
    if status not in {"confirmed", "partial", "insufficient_evidence", "failed"}:
        status = "insufficient_evidence"

    drivers = []
    for item in missing_drivers or []:
        if isinstance(item, Mapping):
            # Require concrete module/package candidates when claiming a missing driver.
            if not item.get("required_driver") and not item.get("package_candidates"):
                status = "insufficient_evidence"
            drivers.append(dict(item))
        else:
            status = "insufficient_evidence"

    firmware = [str(x) for x in (missing_firmware or [])]

    conf = float(root_cause_confidence)
    if conf < 0:
        conf = 0.0
    if conf > 1:
        conf = 1.0
    if status == "insufficient_evidence":
        conf = min(conf, 0.49)

    area = primary_failure_area
    if area and area not in DIAGNOSTIC_AREAS:
        area = "rescue_runtime"

    return {
        "diagnostic_status": status,
        "correlation_id": correlation_id,
        "run_id": run_id,
        "primary_failure_area": area,
        "primary_issue_code": primary_issue_code,
        "root_cause_confidence": conf,
        "missing_drivers": drivers,
        "missing_firmware": firmware,
        "degraded_devices": list(degraded_devices or []),
        "blocked_devices": list(blocked_devices or []),
        "recommended_next_boot_profile": recommended_next_boot_profile,
        "recommended_actions": list(recommended_actions or []),
        "evidence_refs": list(evidence_refs or []),
    }


def validate_ingest_response(response: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    status = response.get("ingest_status")
    if status not in {"accepted", "rejected", "duplicate", "review_required"}:
        errors.append("invalid_ingest_status")
    if not response.get("correlation_id"):
        errors.append("missing_correlation_id")
    if "received_events" not in response:
        errors.append("missing_received_events")
    if "diagnostics_forwarding_status" not in response:
        errors.append("missing_diagnostics_forwarding_status")
    # Explicit rule: HTTP 200 alone never proves success.
    if response.get("http_status") == 200 and status not in {"accepted", "duplicate"}:
        errors.append("http_200_without_accepted_ingest_status")
    return errors
