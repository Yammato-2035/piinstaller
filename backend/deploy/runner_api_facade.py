"""
Deploy runner API facade — read-only registry and result contract access.

Phase C.3: No runner_*.py imports, no execution, no runtime writes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from deploy.runner_registry import (
    REGISTRY_VERSION,
    RunnerRegistryEntry,
    build_runner_registry_from_files,
    build_runner_registry_summary,
    entry_to_dict,
    find_runner_by_id,
    registry_policy_warnings,
)
from deploy.runner_result_contract import (
    CONTRACT_VERSION,
    build_empty_result_for_registry_entry,
    validate_registry_result_contract,
)
from deploy.runner_risk_gate import (
    RISK_GATE_VERSION,
    RunnerRiskDecision,
    build_risk_gate_summary,
    evaluate_runner_risk_gate,
    list_operator_required_runners,
)

FACADE_VERSION = 4

DECOUPLED_ROUTE_RUNNER_IDS_C5 = frozenset(
    {
        "runner_next_phase_gate",
        "runner_version_governance",
        "runner_version_source_of_truth_check",
        "runner_legacy_identifier_inventory",
    }
)

DECOUPLED_ROUTE_RUNNER_IDS_C6 = frozenset(
    {
        "runner_legacy_identifier_hotspot_analysis",
        "runner_setuphelfer_identifier_consistency_check",
        "runner_manual_runtime_evidence_timeline",
        "runner_manual_runtime_evidence_final_snapshot",
        "runner_manual_runtime_validator_seal_index",
    }
)

DECOUPLED_ROUTE_RUNNER_IDS_D7 = frozenset(
    {
        "runner_legacy_identifier_cleanup_classifier",
        "runner_legacy_runtime_compatibility_validation",
        "runner_manual_runtime_failure_test_result_capture",
        "runner_manual_runtime_failure_result_evaluation",
        "runner_manual_runtime_validator_seal_consistency_audit",
    }
)

DECOUPLED_ROUTE_RUNNER_IDS = (
    DECOUPLED_ROUTE_RUNNER_IDS_C5 | DECOUPLED_ROUTE_RUNNER_IDS_C6 | DECOUPLED_ROUTE_RUNNER_IDS_D7
)

_DEPLOY_ROOT = Path(__file__).resolve().parent
_UNSAFE_ROUTE_FRAGMENTS = frozenset(
    {"execute", "apply", "install", "write", "delete", "real-write", "prototype"}
)
_READ_ONLY_ROUTE_NAMES = frozenset(
    {
        "/runners/catalog",
        "/runners/summary",
        "/runners/policy-warnings",
        "/runners/risk-gate/summary",
        "/runners/risk-gate/operator-required",
        "/runners/risk-gate/never-auto",
        "/runners/risk-gate/plan-allowed",
        "/runners/{runner_id}",
        "/runners/{runner_id}/empty-result",
        "/runners/{runner_id}/risk-gate",
    }
)


def facade_response(
    *,
    status: str,
    code: str,
    data: dict[str, Any] | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
) -> dict[str, Any]:
    """Stable facade envelope for API and tests."""
    return {
        "status": status,
        "code": code,
        "data": data or {},
        "warnings": list(warnings or []),
        "errors": list(errors or []),
    }


@lru_cache(maxsize=1)
def _load_registry_entries() -> tuple[RunnerRegistryEntry, ...]:
    return tuple(build_runner_registry_from_files(root=_DEPLOY_ROOT))


def _entries_list() -> list[RunnerRegistryEntry]:
    return list(_load_registry_entries())


def list_runner_registry_entries() -> dict[str, Any]:
    """Return all registry entries as dicts."""
    entries = _entries_list()
    return facade_response(
        status="ok",
        code="RUNNER_REGISTRY_LIST",
        data={
            "facade_version": FACADE_VERSION,
            "registry_version": REGISTRY_VERSION,
            "contract_version": CONTRACT_VERSION,
            "total": len(entries),
            "entries": [entry_to_dict(e) for e in entries],
        },
    )


def get_runner_registry_entry(runner_id: str) -> dict[str, Any]:
    """Return a single registry entry or structured not-found."""
    entries = _entries_list()
    entry = find_runner_by_id(runner_id, entries)
    if entry is None:
        return facade_response(
            status="blocked",
            code="RUNNER_NOT_FOUND",
            errors=[{"code": "RUNNER_NOT_FOUND", "message": f"Unknown runner_id: {runner_id}"}],
        )
    return facade_response(
        status="ok",
        code="RUNNER_REGISTRY_ENTRY",
        data={"entry": entry_to_dict(entry)},
    )


def get_runner_empty_result(runner_id: str) -> dict[str, Any]:
    """Plan-only empty result for a registry entry."""
    entries = _entries_list()
    entry = find_runner_by_id(runner_id, entries)
    if entry is None:
        return facade_response(
            status="blocked",
            code="RUNNER_NOT_FOUND",
            errors=[{"code": "RUNNER_NOT_FOUND", "message": f"Unknown runner_id: {runner_id}"}],
        )
    empty = build_empty_result_for_registry_entry(entry)
    return facade_response(
        status="ok",
        code="RUNNER_EMPTY_RESULT",
        data={
            "runner_id": runner_id,
            "result": empty.to_dict(),
            "no_execution_performed": True,
        },
    )


def validate_runner_empty_result(runner_id: str) -> dict[str, Any]:
    """Validate empty result against registry + result contract."""
    entries = _entries_list()
    entry = find_runner_by_id(runner_id, entries)
    if entry is None:
        return facade_response(
            status="blocked",
            code="RUNNER_NOT_FOUND",
            errors=[{"code": "RUNNER_NOT_FOUND", "message": f"Unknown runner_id: {runner_id}"}],
        )
    empty = build_empty_result_for_registry_entry(entry)
    validation = validate_registry_result_contract(entry, empty)
    status = "ok" if validation.valid else "review_required"
    return facade_response(
        status=status,
        code="RUNNER_EMPTY_RESULT_VALIDATION",
        data={
            "runner_id": runner_id,
            "valid": validation.valid,
            "contract_version": CONTRACT_VERSION,
            "result": empty.to_dict(),
        },
        warnings=list(validation.warnings),
        errors=list(validation.errors),
    )


def build_runner_catalog() -> dict[str, Any]:
    """Compact catalog for list UIs (id, category, risk, policy)."""
    entries = _entries_list()
    catalog = [
        {
            "runner_id": e.runner_id,
            "path": e.path,
            "category": e.category.value,
            "risk_level": e.risk_level.value,
            "execution_policy": e.execution_policy.value,
            "requires_operator": e.requires_operator,
            "has_tests": e.has_tests,
            "lines": e.lines,
        }
        for e in entries
    ]
    return facade_response(
        status="ok",
        code="RUNNER_CATALOG",
        data={
            "facade_version": FACADE_VERSION,
            "total": len(catalog),
            "catalog": catalog,
        },
    )


def build_runner_catalog_summary() -> dict[str, Any]:
    """Aggregate summary aligned with registry summary."""
    entries = _entries_list()
    summary = build_runner_registry_summary(entries)
    return facade_response(
        status="ok",
        code="RUNNER_CATALOG_SUMMARY",
        data={
            "facade_version": FACADE_VERSION,
            "registry_version": summary.facade_version,
            "total": summary.total,
            "by_category": summary.by_category,
            "by_risk": summary.by_risk,
            "by_policy": summary.by_policy,
            "device_write_count": summary.device_write_count,
            "destructive_count": summary.destructive_count,
            "sudo_count": summary.sudo_count,
            "unknown_count": summary.unknown_count,
            "largest": summary.largest[:10],
        },
    )


def build_runner_policy_warnings() -> dict[str, Any]:
    """Registry policy warnings (warn-only, no execution)."""
    entries = _entries_list()
    warnings = registry_policy_warnings(entries)
    status = "review_required" if warnings else "ok"
    return facade_response(
        status=status,
        code="RUNNER_POLICY_WARNINGS",
        data={"total": len(warnings), "warnings": warnings},
        warnings=warnings,
    )


def read_only_runner_route_paths() -> frozenset[str]:
    """Documented read-only runner API paths (for boundary checks)."""
    return _READ_ONLY_ROUTE_NAMES


def is_unsafe_runner_route_path(path: str) -> bool:
    """True if path fragment suggests execute/apply/write/install/delete."""
    lower = path.lower()
    return any(fragment in lower for fragment in _UNSAFE_ROUTE_FRAGMENTS)


def get_runner_risk_gate_decision(runner_id: str) -> dict[str, Any]:
    """Read-only risk gate decision for a runner (no execution)."""
    entries = _entries_list()
    decision = evaluate_runner_risk_gate(runner_id, entries=entries)
    status = "ok" if decision.decision == RunnerRiskDecision.ALLOWED_PLAN_ONLY else "review_required"
    if decision.decision.value.startswith("blocked"):
        status = "blocked"
    return facade_response(
        status=status,
        code="RUNNER_RISK_GATE_DECISION",
        data={
            "facade_version": FACADE_VERSION,
            "risk_gate_version": RISK_GATE_VERSION,
            "decision": decision.to_dict(),
            "allowed_to_execute": decision.allowed_to_execute,
        },
        warnings=decision.warnings,
        errors=decision.errors,
    )


def build_runner_risk_gate_summary() -> dict[str, Any]:
    """Aggregate risk gate summary for all runners."""
    entries = _entries_list()
    summary = build_risk_gate_summary(entries)
    status = "review_required" if summary.get("never_auto_count", 0) > 0 else "ok"
    return facade_response(
        status=status,
        code="RUNNER_RISK_GATE_SUMMARY",
        data={"facade_version": FACADE_VERSION, **summary},
    )


def list_runner_operator_required() -> dict[str, Any]:
    entries = _entries_list()
    ids = list_operator_required_runners(entries)
    return facade_response(
        status="review_required" if ids else "ok",
        code="RUNNER_OPERATOR_REQUIRED_LIST",
        data={"total": len(ids), "runner_ids": ids},
    )


def list_runner_never_auto() -> dict[str, Any]:
    entries = _entries_list()
    ids = sorted(
        e.runner_id
        for e in entries
        if evaluate_runner_risk_gate(e.runner_id, entries=entries).decision
        == RunnerRiskDecision.BLOCKED_NEVER_AUTO
    )
    return facade_response(
        status="review_required" if ids else "ok",
        code="RUNNER_NEVER_AUTO_LIST",
        data={"total": len(ids), "runner_ids": ids},
    )


def list_runner_plan_allowed() -> dict[str, Any]:
    entries = _entries_list()
    ids = sorted(
        e.runner_id
        for e in entries
        if evaluate_runner_risk_gate(e.runner_id, entries=entries).allowed_to_plan
    )
    return facade_response(
        status="ok",
        code="RUNNER_PLAN_ALLOWED_LIST",
        data={"total": len(ids), "runner_ids": ids},
    )


def assert_runner_plan_allowed(runner_id: str) -> Any:
    """Raise ValueError if risk gate disallows plan-only access (no runner execution)."""
    entries = _entries_list()
    decision = evaluate_runner_risk_gate(runner_id, entries=entries)
    if not decision.allowed_to_plan:
        raise ValueError(
            f"runner_plan_not_allowed:{runner_id}:{decision.decision.value}"
        )
    return decision


def build_plan_only_response(
    runner_id: str,
    *,
    response_code: str = "RUNNER_PLAN_ONLY",
    decoupling_phase: str = "c5",
) -> dict[str, Any]:
    """Plan-only facade response: risk gate + contract empty result, no runner import."""
    phase_tag = f"facade_decoupling_{decoupling_phase}"
    entries = _entries_list()
    gate_decision = evaluate_runner_risk_gate(runner_id, entries=entries)
    gate_dict = gate_decision.to_dict()

    def _base(**extra: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "allowed_to_execute": False,
            phase_tag: True,
        }
        payload.update(extra)
        return payload

    if gate_decision.decision == RunnerRiskDecision.BLOCKED_UNKNOWN_RUNNER:
        return _base(
            status="blocked",
            code=f"{response_code}_BLOCKED",
            runner_id=runner_id,
            risk_gate=gate_dict,
            result={},
            warnings=list(gate_decision.warnings),
            errors=list(gate_decision.errors),
        )

    if not gate_decision.allowed_to_plan:
        status = "blocked" if gate_decision.decision.value.startswith("blocked") else "review_required"
        suffix = "BLOCKED" if status == "blocked" else "REVIEW_REQUIRED"
        return _base(
            status=status,
            code=f"{response_code}_{suffix}",
            runner_id=runner_id,
            risk_gate=gate_dict,
            result={},
            warnings=list(gate_decision.warnings),
            errors=list(gate_decision.errors),
        )

    entry = find_runner_by_id(runner_id, entries)
    assert entry is not None
    empty = build_empty_result_for_registry_entry(entry)
    status = "ok" if gate_decision.decision == RunnerRiskDecision.ALLOWED_PLAN_ONLY else "review_required"
    suffix = "OK" if status == "ok" else "REVIEW_REQUIRED"
    return _base(
        status=status,
        code=f"{response_code}_{suffix}",
        runner_id=runner_id,
        risk_gate=gate_dict,
        result=empty.to_dict(),
        warnings=list(gate_decision.warnings),
        errors=[],
    )


def build_readonly_runner_response(
    runner_id: str,
    *,
    response_code: str = "RUNNER_READONLY",
) -> dict[str, Any]:
    """Plan-only response for read-only / evidence runners (delegates to plan-only gate)."""
    entries = _entries_list()
    entry = find_runner_by_id(runner_id, entries)
    if entry is None:
        return build_plan_only_response(runner_id, response_code=response_code)
    if entry.risk_level.value not in {"read_only", "evidence_write"}:
        return build_plan_only_response(runner_id, response_code=response_code)
    return build_plan_only_response(runner_id, response_code=response_code)


def clear_registry_cache() -> None:
    """Test helper: invalidate cached registry."""
    _load_registry_entries.cache_clear()
