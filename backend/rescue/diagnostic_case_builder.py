"""
Diagnostic case builder for ASUS high-information rescue boots.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 Phase 11.

Produces the campaign diagnostics response shape and a strict telemetry
ACK view (HTTP 200 alone is never sufficient — ``accepted`` must be true-ish).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from rescue.diagnostics_forwarding_contract import DIAGNOSTIC_AREAS, build_diagnostics_result

_INSTALL_READINESS = frozenset({"ready", "review_required", "blocked", "unknown"})


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _normalize_confidence(raw: Any) -> float:
    try:
        conf = float(raw)
    except (TypeError, ValueError):
        conf = 0.0
    if conf < 0:
        return 0.0
    if conf > 1:
        return 1.0
    return conf


def _derive_primary_failure_area(
    findings: Sequence[Any],
    driver_gaps: Sequence[Any],
    firmware_gaps: Sequence[Any],
    hardware_state: Mapping[str, Any],
) -> str | None:
    for item in findings:
        if isinstance(item, Mapping):
            area = item.get("area") or item.get("primary_failure_area")
            if area:
                return str(area)
    if driver_gaps:
        return "driver"
    if firmware_gaps:
        return "firmware"
    for key, area in (
        ("gpu", "gpu"),
        ("amd_gpu", "gpu"),
        ("nvidia_gpu", "gpu"),
        ("network", "network"),
        ("nvme", "nvme"),
        ("storage", "nvme"),
        ("boot", "boot_stage"),
    ):
        status = str(hardware_state.get(key) or "").lower()
        if status in {"failed", "driver_missing", "firmware_missing", "degraded", "timeout"}:
            return area
    return None


def _derive_install_readiness(
    hardware_state: Mapping[str, Any],
    findings: Sequence[Any],
    hardware_risks: Sequence[Any],
) -> str:
    explicit = hardware_state.get("install_readiness") or hardware_state.get("linux_install_readiness")
    if explicit in _INSTALL_READINESS:
        return str(explicit)
    if hardware_risks:
        return "blocked"
    for item in findings:
        if isinstance(item, Mapping) and item.get("blocks_install"):
            return "blocked"
    critical = hardware_state.get("critical_hardware_block")
    if critical is True:
        return "blocked"
    if hardware_state.get("linux_target_identified") and hardware_state.get("windows_target_identified"):
        if hardware_state.get("nvme_critical_warning"):
            return "blocked"
        return "review_required"
    return "unknown"


def _derive_safe_remediations(
    findings: Sequence[Any],
    hardware_state: Mapping[str, Any],
) -> list[str]:
    out: list[str] = []
    for item in findings:
        if isinstance(item, Mapping):
            rem = item.get("safe_remediation") or item.get("safe_remediations")
            if isinstance(rem, str) and rem:
                out.append(rem)
            elif isinstance(rem, (list, tuple)):
                out.extend(str(x) for x in rem if x)
    suggested = hardware_state.get("safe_remediations")
    if isinstance(suggested, (list, tuple)):
        out.extend(str(x) for x in suggested if x)
    # Stable unique order
    seen: set[str] = set()
    unique: list[str] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _derive_next_tests(
    boot_profile: str,
    findings: Sequence[Any],
    install_readiness: str,
) -> list[str]:
    tests: list[str] = []
    for item in findings:
        if isinstance(item, Mapping) and item.get("next_test"):
            tests.append(str(item["next_test"]))
    if not tests:
        tests.append("repeat_high_information_boot")
        if boot_profile and "XORG" not in boot_profile.upper() and "GUI" not in boot_profile.upper():
            tests.append("controlled_drm_xorg_probe")
        if install_readiness == "review_required":
            tests.append("verify_linux_nvme_identity")
        elif install_readiness == "ready":
            tests.append("operator_confirm_linux_install_plan")
    seen: set[str] = set()
    unique: list[str] = []
    for t in tests:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def build_diagnostic_case(
    *,
    run_id: str,
    boot_id: str,
    payload_version: str,
    kernel: str,
    boot_profile: str,
    findings: Sequence[Any] | None,
    hypotheses: Sequence[Any] | None,
    driver_gaps: Sequence[Any] | None,
    firmware_gaps: Sequence[Any] | None,
    hardware_state: Mapping[str, Any] | None,
    previous_boot_comparison: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a diagnostic case matching the campaign response shape.

    Also embeds identity fields (run/boot/payload/kernel/profile) and the
    optional previous-boot comparison for local/server correlation.
    """
    findings_list = _as_list(findings)
    hypotheses_list = _as_list(hypotheses)
    driver_list = _as_list(driver_gaps)
    firmware_list = _as_list(firmware_gaps)
    hw = dict(hardware_state or {})
    comparison = dict(previous_boot_comparison or {})

    confirmed = []
    for item in findings_list:
        if isinstance(item, Mapping):
            status = str(item.get("status") or item.get("confirmation") or "").lower()
            if status in {"confirmed", "true", "yes"} or item.get("confirmed") is True:
                confirmed.append(dict(item))
        elif item:
            confirmed.append({"finding": str(item), "status": "confirmed"})

    missing_drivers: list[Any] = []
    for gap in driver_list:
        if isinstance(gap, Mapping):
            missing_drivers.append(dict(gap))
        elif gap:
            missing_drivers.append({"required_driver": str(gap)})

    missing_firmware: list[str] = []
    for gap in firmware_list:
        if isinstance(gap, Mapping):
            name = gap.get("firmware") or gap.get("name") or gap.get("file")
            if name:
                missing_firmware.append(str(name))
        elif gap:
            missing_firmware.append(str(gap))

    hardware_risks: list[Any] = list(_as_list(hw.get("hardware_risks")))
    for key in ("critical_warnings", "risks", "blocked_devices"):
        for item in _as_list(hw.get(key)):
            if item not in hardware_risks:
                hardware_risks.append(item)

    primary = _derive_primary_failure_area(findings_list, driver_list, firmware_list, hw)
    if primary and primary not in DIAGNOSTIC_AREAS:
        # Keep free-form areas from findings, but normalize unknown via contract helper path.
        pass

    conf_raw = hw.get("confidence")
    if conf_raw is None and confirmed:
        conf_raw = 0.7
    elif conf_raw is None and (hypotheses_list or driver_list or firmware_list):
        conf_raw = 0.45
    else:
        conf_raw = conf_raw if conf_raw is not None else 0.2
    confidence = _normalize_confidence(conf_raw)

    install_readiness = _derive_install_readiness(hw, findings_list, hardware_risks)
    safe_remediations = _derive_safe_remediations(findings_list, hw)
    next_tests = _derive_next_tests(str(boot_profile or ""), findings_list, install_readiness)

    # Align confidence/area with existing diagnostics forwarding contract where helpful.
    contract = build_diagnostics_result(
        correlation_id=str(hw.get("correlation_id") or boot_id or run_id or ""),
        run_id=str(run_id or ""),
        diagnostic_status="confirmed" if confirmed else ("partial" if findings_list else "insufficient_evidence"),
        primary_failure_area=primary if primary in DIAGNOSTIC_AREAS else (primary or None),
        primary_issue_code=(
            str(confirmed[0].get("issue_code"))
            if confirmed and isinstance(confirmed[0], Mapping) and confirmed[0].get("issue_code")
            else None
        ),
        root_cause_confidence=confidence,
        missing_drivers=missing_drivers,
        missing_firmware=missing_firmware,
        recommended_actions=safe_remediations,
    )

    area = contract["primary_failure_area"] or primary
    confidence = float(contract["root_cause_confidence"])

    return {
        "run_id": run_id,
        "boot_id": boot_id,
        "payload_version": payload_version,
        "kernel": kernel,
        "boot_profile": boot_profile,
        "device_binding": hw.get("device_binding") or hw.get("asus_device_binding"),
        "findings": findings_list,
        "driver_gaps": driver_list,
        "firmware_gaps": firmware_list,
        "hardware_state": hw,
        "previous_boot_comparison": comparison,
        "primary_failure_area": area,
        "confirmed_findings": confirmed,
        "hypotheses": hypotheses_list,
        "missing_drivers": contract["missing_drivers"],
        "missing_firmware": contract["missing_firmware"],
        "hardware_risks": hardware_risks,
        "safe_remediations": safe_remediations,
        "install_readiness": install_readiness,
        "next_tests": next_tests,
        "confidence": confidence,
        "diagnostic_status": contract["diagnostic_status"],
        "correlation_id": contract["correlation_id"],
    }


def build_telemetry_ack_view(response: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    Strict ACK view for telemetry/diagnostics ingest.

    HTTP 200 alone is insufficient. Requires true-ish ``accepted`` plus
    ``correlation_id``, ``case_id``, and ``diagnostics_forwarding_status``.
    """
    resp = dict(response or {})
    errors: list[str] = []

    accepted_raw = resp.get("accepted")
    if accepted_raw is None and resp.get("ingest_status") == "accepted":
        accepted_raw = True
    accepted = accepted_raw in (True, 1, "1", "true", "True", "yes", "YES")

    correlation_id = resp.get("correlation_id")
    case_id = resp.get("case_id")
    forwarding = resp.get("diagnostics_forwarding_status")
    http_status = resp.get("http_status")

    if not accepted:
        errors.append("accepted_not_true")
    if not correlation_id:
        errors.append("missing_correlation_id")
    if not case_id:
        errors.append("missing_case_id")
    if forwarding is None or forwarding == "":
        errors.append("missing_diagnostics_forwarding_status")
    if http_status == 200 and not accepted:
        errors.append("http_200_without_accepted")

    ok = not errors
    return {
        "ok": ok,
        "accepted": accepted,
        "correlation_id": correlation_id,
        "case_id": case_id,
        "diagnostics_forwarding_status": forwarding,
        "http_status": http_status,
        "errors": errors,
        # Explicit campaign rule surface
        "http_200_alone_insufficient": True,
    }
