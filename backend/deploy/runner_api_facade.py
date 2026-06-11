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

FACADE_VERSION = 1

_DEPLOY_ROOT = Path(__file__).resolve().parent
_UNSAFE_ROUTE_FRAGMENTS = frozenset(
    {"execute", "apply", "install", "write", "delete", "real-write", "prototype"}
)
_READ_ONLY_ROUTE_NAMES = frozenset(
    {
        "/runners/catalog",
        "/runners/summary",
        "/runners/policy-warnings",
        "/runners/{runner_id}",
        "/runners/{runner_id}/empty-result",
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


def clear_registry_cache() -> None:
    """Test helper: invalidate cached registry."""
    _load_registry_entries.cache_clear()
