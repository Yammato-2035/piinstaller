"""
Target-platform vs. OS-catalog compatibility checks — read-only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 13 (compatibility half).
"""

from __future__ import annotations

from typing import Any

OS_COMPATIBILITY_VERSION = 1


def check_architecture_match(catalog_entry: dict[str, Any], target_architecture: str) -> bool:
    return catalog_entry.get("architecture") == target_architecture


def check_platform_supported(catalog_entry: dict[str, Any], target_platform_id: str | None) -> bool:
    supported = catalog_entry.get("supported_platforms") or []
    if not supported:
        # Empty list means "not yet scoped" (see future entries) — never assume yes.
        return False
    if target_platform_id is None:
        return False
    return target_platform_id in supported


def check_target_size_sufficient(catalog_entry: dict[str, Any], target_bytes: int | None) -> bool | None:
    minimum = catalog_entry.get("minimum_target_bytes") or 0
    if target_bytes is None:
        return None
    if minimum <= 0:
        return None  # not yet scoped
    return target_bytes >= minimum


def evaluate_compatibility(
    *,
    catalog_entry: dict[str, Any],
    target_architecture: str,
    target_platform_id: str | None = None,
    target_bytes: int | None = None,
) -> dict[str, Any]:
    arch_ok = check_architecture_match(catalog_entry, target_architecture)
    platform_ok = check_platform_supported(catalog_entry, target_platform_id) if target_platform_id else None
    size_ok = check_target_size_sufficient(catalog_entry, target_bytes)

    blockers: list[str] = []
    if not arch_ok:
        blockers.append("architecture_mismatch")
    if platform_ok is False:
        blockers.append("platform_not_in_supported_platforms")
    if size_ok is False:
        blockers.append("target_below_minimum_bytes")
    if catalog_entry.get("support_status") in ("future", "blocked"):
        blockers.append(f"catalog_support_status_{catalog_entry.get('support_status')}")

    compatibility_status = "compatible" if not blockers else "incompatible"

    return {
        "image_id": catalog_entry.get("image_id"),
        "architecture_match": arch_ok,
        "platform_supported": platform_ok,
        "target_size_sufficient": size_ok,
        "compatibility_status": compatibility_status,
        "blockers": blockers,
    }


def build_os_compatibility_diagnostics() -> dict[str, Any]:
    return {
        "compatibility_version": OS_COMPATIBILITY_VERSION,
        "module": "provisioning.os_compatibility",
        "read_only": True,
        "writes_allowed": False,
    }


__all__ = [
    "OS_COMPATIBILITY_VERSION",
    "check_architecture_match",
    "check_platform_supported",
    "check_target_size_sufficient",
    "evaluate_compatibility",
    "build_os_compatibility_diagnostics",
]
