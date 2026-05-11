from __future__ import annotations

from typing import Any

_COMPONENT_IDS = [
    "RUNNER_COMPONENT_REAL_WRITE_GUARD",
    "RUNNER_COMPONENT_HARDWARE_GATE",
    "RUNNER_COMPONENT_REAL_WRITE_PROTOTYPE",
    "RUNNER_COMPONENT_FAILURE_INJECTION",
    "RUNNER_COMPONENT_RUNNER_CONTRACT",
    "RUNNER_COMPONENT_RUNNER_RUNTIME_VALIDATION",
    "RUNNER_COMPONENT_RUNNER_LIFECYCLE",
    "RUNNER_COMPONENT_RUNNER_HANDOFF",
    "RUNNER_COMPONENT_PERMISSION_BOUNDARY",
    "RUNNER_COMPONENT_SANDBOX",
    "RUNNER_COMPONENT_ROOTLESS_E2E",
    "RUNNER_COMPONENT_INSTALL_PLAN",
    "RUNNER_COMPONENT_INSTALL_VALIDATOR",
    "RUNNER_COMPONENT_PACKAGE_BLUEPRINT",
    "RUNNER_COMPONENT_INSTALL_CONSISTENCY",
]

_DEFAULT_BLOCKING_GAPS = [
    "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
    "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
    "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
    "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
    "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
    "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
    "RUNNER_GAP_HOTPLUG_RACE_OPEN",
]

_DEFAULT_NON_BLOCKING_GAPS = [
    "RUNNER_GAP_UI_POLISHING_OPEN",
    "RUNNER_GAP_DISTRO_MATRIX_OPEN",
    "RUNNER_GAP_LARGE_IMAGE_PERFORMANCE_OPEN",
    "RUNNER_GAP_MULTI_DEVICE_SCENARIO_OPEN",
]


def _component_defaults(component_id: str) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "status": "partial",
        "risk_level": "medium",
        "evidence_files": [],
        "test_suites": [],
        "release_gate": "review",
        "notes": [],
    }


def _merge_components(components: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    src = list(components or [])
    by_id = {
        str((x or {}).get("component_id") or ""): dict(x)
        for x in src
        if isinstance(x, dict) and str((x or {}).get("component_id") or "")
    }
    merged: list[dict[str, Any]] = []
    for cid in _COMPONENT_IDS:
        item = _component_defaults(cid)
        if cid in by_id:
            incoming = by_id[cid]
            for key in ["status", "risk_level", "release_gate", "notes", "evidence_files", "test_suites"]:
                if key in incoming:
                    item[key] = incoming[key]
        merged.append(item)
    return merged


def _risk_from_components(components: list[dict[str, Any]], blocking_gaps: list[str]) -> str:
    if blocking_gaps:
        return "critical"
    risks = {str((x or {}).get("risk_level") or "medium") for x in components}
    if "critical" in risks:
        return "critical"
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    return "low"


def build_runner_release_readiness_matrix(
    *,
    components: list[dict[str, Any]] | None = None,
    blocking_gaps: list[str] | None = None,
    non_blocking_gaps: list[str] | None = None,
    required_evidence: list[str] | None = None,
    required_next_validations: list[str] | None = None,
) -> dict[str, Any]:
    merged_components = _merge_components(components)
    component_ids = {str((x or {}).get("component_id") or "") for x in merged_components}

    warnings: list[str] = []
    errors: list[str] = []

    missing_components = [cid for cid in _COMPONENT_IDS if cid not in component_ids]
    if missing_components:
        errors.append("missing_required_components")

    blk = list(blocking_gaps) if blocking_gaps is not None else list(_DEFAULT_BLOCKING_GAPS)
    non_blk = list(non_blocking_gaps) if non_blocking_gaps is not None else list(_DEFAULT_NON_BLOCKING_GAPS)

    for c in merged_components:
        gate = str(c.get("release_gate") or "")
        if gate not in {"pass", "review", "required", "fail"}:
            warnings.append(f"component_release_gate_unknown:{c.get('component_id')}")
        st = str(c.get("status") or "")
        if st not in {"implemented", "tested", "runtime_validated", "partial", "missing"}:
            warnings.append(f"component_status_unknown:{c.get('component_id')}")

    evidence = list(required_evidence or [])
    next_validations = list(
        required_next_validations
        or [
            "validate_runner_installation_dryrun",
            "runner_rootless_e2e_repeat",
            "runner_dryrun_under_policy",
            "runtime_proof_before_real_write",
        ]
    )

    # Nie production-ready in dieser Phase.
    readiness_status = "ready_for_lab"
    if blk:
        readiness_status = "blocked"
    elif non_blk:
        readiness_status = "review_required"

    risk = _risk_from_components(merged_components, blk)

    return {
        "readiness_status": readiness_status,
        "overall_risk_level": risk,
        "components": merged_components,
        "blocking_gaps": blk,
        "non_blocking_gaps": non_blk,
        "required_evidence": evidence,
        "required_next_validations": next_validations,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
